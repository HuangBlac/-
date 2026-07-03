"""Local Ollama-backed content generation for courses and events."""

from __future__ import annotations

import argparse
import json
import os
import re
import socket
import urllib.error
import urllib.request
from typing import Any, Dict, Iterable, List


DEFAULT_MODEL = os.environ.get("CTHULHU_OLLAMA_MODEL", "qwen3.5")
DEFAULT_URL = os.environ.get("CTHULHU_OLLAMA_URL", "http://127.0.0.1:11434/api/generate")
DEFAULT_TIMEOUT = float(os.environ.get("CTHULHU_OLLAMA_TIMEOUT", "120"))
DEFAULT_DEEPSEEK_MODEL = os.environ.get("CTHULHU_DEEPSEEK_MODEL", "deepseek-v4-flash")
DEFAULT_DEEPSEEK_URL = os.environ.get(
    "CTHULHU_DEEPSEEK_URL",
    "https://api.deepseek.com/chat/completions",
)
DEFAULT_DEEPSEEK_API_KEY_ENV = os.environ.get("CTHULHU_DEEPSEEK_API_KEY_ENV", "DEEPSEEK_API_KEY")

ALLOWED_ATTRIBUTES = {"INT", "SEN", "EDU", "STR", "SOC"}
ALLOWED_EVENT_TYPES = {
    "random",
    "advisor",
    "advisor_pressure",
    "advisor_task",
    "academic",
    "mythos",
    "social",
    "investigation",
    "holiday",
    "entertainment",
}
ALLOWED_TRIGGERS = {
    "always",
    "normal",
    "random",
    "rare",
    "periodic",
    "weekly",
    "low_progress",
    "high_progress",
    "high_reputation",
    "low_reputation",
    "low_sanity",
    "mutation",
    "research",
    "read",
    "submit",
    "investigation",
    "family_pressure",
}
ALLOWED_EFFECTS = {
    "sanity",
    "INT",
    "SEN",
    "EDU",
    "STR",
    "SOC",
    "reputation",
    "progress",
    "papers_published",
    "mutation",
}

EVENT_TYPE_BY_FILE = {
    "advisor_pressure_event.json": "advisor_pressure",
    "events_academic.json": "academic",
    "events_advisor.json": "advisor",
    "events_advisor_task.json": "advisor_task",
    "events_entertainment.json": "entertainment",
    "events_holiday.json": "holiday",
    "events_investigation.json": "investigation",
    "events_mythos.json": "mythos",
    "events_random.json": "random",
    "events_social.json": "social",
}


class ContentGenerationError(RuntimeError):
    """Raised when Ollama content generation or validation fails."""


def generated_data_dir() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "generated")


def generated_courses_path() -> str:
    return os.path.join(generated_data_dir(), "courses.json")


def generated_events_path() -> str:
    return os.path.join(generated_data_dir(), "events.json")


def event_drafts_dir() -> str:
    return os.path.join(generated_data_dir(), "event_drafts")


def call_ollama(prompt: str, model: str = DEFAULT_MODEL, url: str = DEFAULT_URL,
                timeout: float = DEFAULT_TIMEOUT) -> Dict[str, Any]:
    """Call Ollama's local generate endpoint and return a JSON object."""
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "think": False,
        "options": {
            "temperature": 0.8,
            "top_p": 0.9,
        },
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except (TimeoutError, socket.timeout) as exc:
        raise ContentGenerationError(
            f"Ollama did not finish within {timeout} seconds. Try fewer items or a longer --timeout."
        ) from exc
    except urllib.error.URLError as exc:
        raise ContentGenerationError(
            f"Could not reach Ollama at {url}. Is `ollama serve` running?"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ContentGenerationError("Ollama returned a non-JSON response.") from exc

    text = response_payload.get("response")
    if not isinstance(text, str):
        raise ContentGenerationError("Ollama response did not contain a text payload.")
    return extract_json_object(text)


def call_deepseek(prompt: str, model: str = DEFAULT_DEEPSEEK_MODEL,
                  url: str = DEFAULT_DEEPSEEK_URL, timeout: float = DEFAULT_TIMEOUT,
                  api_key: str | None = None,
                  api_key_env: str = DEFAULT_DEEPSEEK_API_KEY_ENV) -> Dict[str, Any]:
    """Call DeepSeek's OpenAI-compatible chat completions endpoint."""
    selected_api_key = api_key if api_key is not None else os.environ.get(api_key_env, "")
    if not selected_api_key:
        raise ContentGenerationError(f"Missing DeepSeek API key. Set environment variable {api_key_env}.")

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "你是游戏内容生成器。必须只输出一个合法 JSON 对象，不要解释。",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.8,
        "stream": False,
        "response_format": {"type": "json_object"},
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {selected_api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except (TimeoutError, socket.timeout) as exc:
        raise ContentGenerationError(
            f"DeepSeek did not finish within {timeout} seconds. Try fewer items or a longer --timeout."
        ) from exc
    except urllib.error.HTTPError as exc:
        error_text = exc.read().decode("utf-8", errors="replace")
        raise ContentGenerationError(f"DeepSeek HTTP error {exc.code}: {error_text}") from exc
    except urllib.error.URLError as exc:
        raise ContentGenerationError(f"Could not reach DeepSeek at {url}.") from exc
    except json.JSONDecodeError as exc:
        raise ContentGenerationError("DeepSeek returned a non-JSON response.") from exc

    try:
        text = response_payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ContentGenerationError("DeepSeek response did not contain chat completion text.") from exc
    if not isinstance(text, str):
        raise ContentGenerationError("DeepSeek response text was not a string.")
    return extract_json_object(text)


def extract_json_object(text: str) -> Dict[str, Any]:
    """Extract the first JSON object from model text."""
    stripped = text.strip()
    if stripped.startswith("{"):
        return _loads_json_object(stripped)

    match = re.search(r"\{.*\}", stripped, flags=re.DOTALL)
    if not match:
        raise ContentGenerationError("Model output did not contain a JSON object.")
    return _loads_json_object(match.group(0))


def _loads_json_object(text: str) -> Dict[str, Any]:
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ContentGenerationError(f"Model output was not valid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ContentGenerationError("Model output must be a JSON object.")
    return value


def build_content_prompt(course_count: int, event_count: int) -> str:
    return f"""
你是《克研模拟器》的内容设计助手。请生成适合研究生科研生活 + 克苏鲁神话题材的游戏内容。

只输出一个 JSON 对象，不要 Markdown，不要解释。

JSON schema:
{{
  "required_courses": [
    {{
      "name": "课程名",
      "type": "必修",
      "description": "一句课程描述",
      "attributes": {{"EDU": 2, "SEN": 1}},
      "credits": 3
    }}
  ],
  "elective_courses": [
    {{
      "name": "课程名",
      "type": "选修",
      "description": "一句课程描述",
      "attributes": {{"INT": 2, "SOC": 1}},
      "credits": 2
    }}
  ],
  "hidden_courses": [
    {{
      "name": "隐藏课程名",
      "type": "隐藏",
      "description": "一句课程描述",
      "attributes": {{"SEN": 3}},
      "credits": 5,
      "hidden": true
    }}
  ],
  "events": [
    {{
      "id": 9001,
      "title": "事件标题",
      "description": "事件描述",
      "type": "random",
      "trigger_condition": "normal",
      "effect": {{"sanity": -2, "progress": 3}}
    }}
  ]
}}

要求:
- 生成 {course_count} 门课程，放在 required_courses/elective_courses/hidden_courses 中，选修课为主。
- 生成 {event_count} 个日常事件，type 分散在 random、academic、social、holiday、entertainment、investigation、mythos。
- 所有 name/title/description 使用简体中文。
- 课程属性只能使用 INT、SEN、EDU、STR、SOC，单项加成在 -3 到 5 之间。
- 事件 effect 只能使用 sanity、INT、SEN、EDU、STR、SOC、reputation、progress、papers_published、mutation。
- 事件 id 使用 9001 开始的整数，不要和示例重复以外的低编号混用。
- 事件应当偏日常、科研、导师、校园生活，只允许少量超自然暗示。
""".strip()


def build_event_expansion_prompt(source_file: str, event_type: str, existing_events: List[Dict[str, Any]],
                                 event_count: int, context_events: int = 12) -> str:
    sampled_events = existing_events[:context_events]
    context_json = json.dumps({"events": sampled_events}, ensure_ascii=False, indent=2)
    return f"""
你是《克研模拟器》的事件设计助手。请根据下面这个源事件文件的既有内容，生成同类型的扩展事件草稿。

源文件: {source_file}
事件类型: {event_type}

现有事件上下文:
{context_json}

只输出一个 JSON 对象，不要 Markdown，不要解释。

JSON schema:
{{
  "events": [
    {{
      "id": 9001,
      "title": "事件标题",
      "description": "事件描述",
      "type": "{event_type}",
      "trigger_condition": "normal",
      "effect": {{"sanity": -2, "progress": 3}}
    }}
  ]
}}

要求:
- 生成 {event_count} 个新事件，必须贴合源文件的叙事风格和玩法用途。
- type 必须是 "{event_type}"。
- title 和 description 使用简体中文。
- 不要照抄现有事件，要延展相同主题。
- 事件应当可直接进入 JSON 事件库，字段保持简洁。
- trigger_condition 只能使用 normal、research、read、submit、investigation、low_sanity、mutation、family_pressure、weekly、rare。
- effect 只能使用 sanity、INT、SEN、EDU、STR、SOC、reputation、progress、papers_published、mutation。
- 如果事件需要玩家选择，可以使用 choices；每个 choice 需要 id、text、effect。
""".strip()


def validate_courses_payload(payload: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    return {
        "required_courses": _normalize_courses(payload.get("required_courses", []), "必修"),
        "elective_courses": _normalize_courses(payload.get("elective_courses", []), "选修"),
        "hidden_courses": _normalize_courses(payload.get("hidden_courses", []), "隐藏", hidden=True),
    }


def validate_events_payload(payload: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    events = payload.get("events", [])
    if not isinstance(events, list):
        raise ContentGenerationError("`events` must be a list.")
    normalized = []
    used_ids = set()
    next_id = 9001
    for raw in events:
        if not isinstance(raw, dict):
            continue
        event = _normalize_event(raw)
        if event["id"] in used_ids:
            while next_id in used_ids:
                next_id += 1
            event["id"] = next_id
        used_ids.add(event["id"])
        normalized.append(event)
    return {"events": normalized}


def validate_event_draft_payload(payload: Dict[str, Any], event_type: str) -> Dict[str, List[Dict[str, Any]]]:
    events = validate_events_payload(payload)["events"]
    for event in events:
        event["type"] = event_type
    return {"events": events}


def validate_content_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    courses = validate_courses_payload(payload)
    events = validate_events_payload(payload)
    return {**courses, **events}


def write_generated_content(payload: Dict[str, Any], courses_path: str | None = None,
                            events_path: str | None = None) -> None:
    courses_path = courses_path or generated_courses_path()
    events_path = events_path or generated_events_path()
    os.makedirs(os.path.dirname(courses_path), exist_ok=True)
    os.makedirs(os.path.dirname(events_path), exist_ok=True)

    courses = validate_courses_payload(payload)
    events = validate_events_payload(payload)

    _write_json(courses_path, courses)
    _write_json(events_path, events)


def generate_and_write(course_count: int, event_count: int, model: str = DEFAULT_MODEL,
                       url: str = DEFAULT_URL, timeout: float = DEFAULT_TIMEOUT,
                       provider: str = "ollama", api_key: str | None = None,
                       api_key_env: str = DEFAULT_DEEPSEEK_API_KEY_ENV) -> Dict[str, Any]:
    prompt = build_content_prompt(course_count, event_count)
    if provider == "deepseek":
        payload = call_deepseek(
            prompt,
            model=model,
            url=url,
            timeout=timeout,
            api_key=api_key,
            api_key_env=api_key_env,
        )
    elif provider == "ollama":
        payload = call_ollama(prompt, model=model, url=url, timeout=timeout)
    else:
        raise ContentGenerationError(f"Unsupported provider `{provider}`.")
    normalized = validate_content_payload(payload)
    write_generated_content(normalized)
    return normalized


def generate_event_file_drafts(event_count: int, model: str = DEFAULT_MODEL,
                              url: str = DEFAULT_URL, timeout: float = DEFAULT_TIMEOUT,
                              provider: str = "ollama", api_key: str | None = None,
                              api_key_env: str = DEFAULT_DEEPSEEK_API_KEY_ENV,
                              event_files: List[str] | None = None,
                              context_events: int = 12) -> List[str]:
    source_files = _select_event_source_files(event_files)
    output_paths = []
    os.makedirs(event_drafts_dir(), exist_ok=True)

    for source_path in source_files:
        source_name = os.path.basename(source_path)
        event_type = EVENT_TYPE_BY_FILE[source_name]
        existing_events = _read_events_from_file(source_path)
        prompt = build_event_expansion_prompt(
            source_file=source_name,
            event_type=event_type,
            existing_events=existing_events,
            event_count=event_count,
            context_events=context_events,
        )
        payload = _call_provider(
            prompt=prompt,
            provider=provider,
            model=model,
            url=url,
            timeout=timeout,
            api_key=api_key,
            api_key_env=api_key_env,
        )
        draft = validate_event_draft_payload(payload, event_type)
        output_path = os.path.join(event_drafts_dir(), source_name)
        _write_json(output_path, {
            "source_file": os.path.join("game", "data", "events", source_name),
            "event_type": event_type,
            "events": draft["events"],
        })
        output_paths.append(output_path)

    return output_paths


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate CthulhuAcademy content with local Ollama.")
    parser.add_argument("--provider", choices=["ollama", "deepseek"], default="ollama")
    parser.add_argument("--model", default=None, help="model name for the selected provider")
    parser.add_argument("--url", default=None, help="generation endpoint URL for the selected provider")
    parser.add_argument("--api-key", default=None, help="DeepSeek API key; prefer using an environment variable")
    parser.add_argument("--api-key-env", default=DEFAULT_DEEPSEEK_API_KEY_ENV, help="DeepSeek API key env var")
    parser.add_argument("--courses", type=int, default=8, help="number of courses to request")
    parser.add_argument("--events", type=int, default=16, help="number of events to request")
    parser.add_argument("--expand-event-files", action="store_true", help="generate per-source event draft files")
    parser.add_argument("--event-files", nargs="*", default=None, help="specific event JSON filenames to expand")
    parser.add_argument("--context-events", type=int, default=12, help="existing events to include per source file")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="request timeout in seconds")
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.provider == "deepseek":
        model = args.model or DEFAULT_DEEPSEEK_MODEL
        url = args.url or DEFAULT_DEEPSEEK_URL
    else:
        model = args.model or DEFAULT_MODEL
        url = args.url or DEFAULT_URL

    try:
        if args.expand_event_files:
            paths = generate_event_file_drafts(
                event_count=args.events,
                model=model,
                url=url,
                timeout=args.timeout,
                provider=args.provider,
                api_key=args.api_key,
                api_key_env=args.api_key_env,
                event_files=args.event_files,
                context_events=args.context_events,
            )
            print(f"Generated event drafts for {len(paths)} files.")
            for path in paths:
                print(path)
            return 0

        normalized = generate_and_write(
            course_count=args.courses,
            event_count=args.events,
            model=model,
            url=url,
            timeout=args.timeout,
            provider=args.provider,
            api_key=args.api_key,
            api_key_env=args.api_key_env,
        )
    except ContentGenerationError as exc:
        print(f"Content generation failed: {exc}")
        return 1
    print(
        "Generated "
        f"{sum(len(normalized[key]) for key in ('required_courses', 'elective_courses', 'hidden_courses'))} courses "
        f"and {len(normalized['events'])} events."
    )
    print(f"Courses: {generated_courses_path()}")
    print(f"Events: {generated_events_path()}")
    return 0


def _normalize_courses(raw_courses: Any, expected_type: str, hidden: bool = False) -> List[Dict[str, Any]]:
    if raw_courses is None:
        return []
    if not isinstance(raw_courses, list):
        raise ContentGenerationError(f"`{expected_type}` courses must be a list.")

    courses = []
    for raw in raw_courses:
        if not isinstance(raw, dict):
            continue
        name = _require_text(raw, "name")
        description = _require_text(raw, "description")
        attributes = _normalize_number_map(raw.get("attributes", {}), ALLOWED_ATTRIBUTES, -3, 5)
        if not attributes:
            raise ContentGenerationError(f"Course `{name}` must have at least one valid attribute.")
        course = {
            "name": name,
            "type": raw.get("type") or expected_type,
            "description": description,
            "attributes": attributes,
            "credits": _clamp_int(raw.get("credits", 3), 1, 5),
        }
        if hidden:
            course["hidden"] = True
        courses.append(course)
    return courses


def _normalize_event(raw: Dict[str, Any]) -> Dict[str, Any]:
    event_type = raw.get("type", "random")
    if event_type not in ALLOWED_EVENT_TYPES:
        event_type = "random"
    trigger = raw.get("trigger_condition", "normal")
    if trigger not in ALLOWED_TRIGGERS:
        trigger = "normal"

    event = {
        "id": _clamp_int(raw.get("id", 9001), 9001, 999999),
        "title": _require_text(raw, "title"),
        "description": _require_text(raw, "description"),
        "type": event_type,
        "trigger_condition": trigger,
        "effect": _normalize_number_map(raw.get("effect", {}), ALLOWED_EFFECTS, -50, 50),
    }
    choices = raw.get("choices")
    if isinstance(choices, list):
        normalized_choices = []
        for index, choice in enumerate(choices, 1):
            if not isinstance(choice, dict):
                continue
            normalized_choices.append({
                "id": str(choice.get("id") or f"choice_{index}"),
                "text": _require_text(choice, "text"),
                "effect": _normalize_number_map(choice.get("effect", {}), ALLOWED_EFFECTS, -50, 50),
            })
        if normalized_choices:
            event["choices"] = normalized_choices
            event.pop("effect", None)
    return event


def _call_provider(prompt: str, provider: str, model: str, url: str, timeout: float,
                   api_key: str | None = None,
                   api_key_env: str = DEFAULT_DEEPSEEK_API_KEY_ENV) -> Dict[str, Any]:
    if provider == "deepseek":
        return call_deepseek(
            prompt,
            model=model,
            url=url,
            timeout=timeout,
            api_key=api_key,
            api_key_env=api_key_env,
        )
    if provider == "ollama":
        return call_ollama(prompt, model=model, url=url, timeout=timeout)
    raise ContentGenerationError(f"Unsupported provider `{provider}`.")


def _event_source_dir() -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "events")


def _select_event_source_files(event_files: List[str] | None = None) -> List[str]:
    selected_names = event_files or list(EVENT_TYPE_BY_FILE)
    paths = []
    for name in selected_names:
        normalized_name = os.path.basename(name)
        if normalized_name not in EVENT_TYPE_BY_FILE:
            raise ContentGenerationError(f"Unsupported event source file `{name}`.")
        path = os.path.join(_event_source_dir(), normalized_name)
        if not os.path.exists(path):
            raise ContentGenerationError(f"Event source file not found: {path}")
        paths.append(path)
    return paths


def _read_events_from_file(path: str) -> List[Dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise ContentGenerationError(f"Could not read event source file: {path}") from exc
    events = payload.get("events", [])
    if not isinstance(events, list):
        raise ContentGenerationError(f"Event source file has no events list: {path}")
    return [event for event in events if isinstance(event, dict)]


def _require_text(raw: Dict[str, Any], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ContentGenerationError(f"Missing required text field `{key}`.")
    return value.strip()


def _normalize_number_map(raw: Any, allowed_keys: set[str], min_value: float,
                          max_value: float) -> Dict[str, Any]:
    if not isinstance(raw, dict):
        return {}
    normalized: Dict[str, Any] = {}
    for key, value in raw.items():
        if key not in allowed_keys or not isinstance(value, (int, float)):
            continue
        if isinstance(value, float) and key == "mutation":
            normalized[key] = max(-1.0, min(1.0, value))
        else:
            normalized[key] = _clamp_int(value, int(min_value), int(max_value))
    return normalized


def _clamp_int(value: Any, min_value: int, max_value: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = min_value
    return max(min_value, min(max_value, number))


def _write_json(path: str, payload: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


if __name__ == "__main__":
    raise SystemExit(main())
