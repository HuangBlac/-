"""Data-driven UI message catalog."""

import json
import os


_MESSAGES = None


def _load_messages() -> dict:
    global _MESSAGES
    if _MESSAGES is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "ui_messages.json")
        with open(path, "r", encoding="utf-8") as handle:
            _MESSAGES = json.load(handle)
    return _MESSAGES


def ui_text(key: str, **kwargs) -> str:
    """Return a formatted UI message from the message catalog."""
    template = _load_messages()[key]
    return template.format(**kwargs)
