"""Temporary input states for multi-step player decisions."""

from game.action_def import ActionDef
from game.state_machine import GameState, StateResult
from game.ui_messages import ui_text


class EventChoiceState(GameState):
    """Temporary state for resolving JSON event choices."""

    def __init__(self):
        self.event = None
        self.label = ""
        self.next_stage = "after_action"
        self.post_apply = None

    @property
    def state_id(self) -> str:
        return "input.event_choice"

    def configure(self, event: dict, label: str, next_stage: str, post_apply=None) -> None:
        """Set the event payload before pushing this state."""
        self.event = event
        self.label = label
        self.next_stage = next_stage
        self.post_apply = post_apply

    def get_available_actions(self, ctx) -> list:
        return [
            ActionDef(
                "input",
                ui_text("event_choice_input_label"),
                ui_text("event_choice_input_description"),
                costs_action_point=False,
            )
        ]

    def on_enter(self, ctx, from_state=None) -> str:
        if not self.event:
            return ui_text("event_choice_missing")

        lines = [
            f"【{self.label}】{self.event['title']}",
            self.event["description"],
            ui_text("event_choice_select_label"),
        ]
        for idx, choice in enumerate(self.event.get("choices", []), 1):
            lines.append(f"{idx}. {choice['text']} ({choice['id']})")
        lines.append(ui_text("prompt_event_choice"))
        return "\n".join(lines)

    def handle_action(self, ctx, action: str) -> StateResult:
        if not self.event:
            return StateResult(ui_text("event_choice_missing"), pop_state=True, resume_stage="after_action")

        choice_id = self._resolve_choice_id(action)
        if choice_id is None:
            return StateResult(ui_text("event_choice_error"), prompt=self.on_enter(ctx))

        result = self._apply_event_result(ctx, choice_id)
        resume_stage = self.next_stage
        self._clear()
        return StateResult(result, pop_state=True, resume_stage=resume_stage)

    def _resolve_choice_id(self, action: str):
        choices = self.event.get("choices", [])
        decision = action.strip().lower()
        if decision.isdigit():
            index = int(decision) - 1
            if 0 <= index < len(choices):
                return choices[index]["id"]
            return None

        for choice in choices:
            if choice["id"].lower() == decision:
                return choice["id"]
        return None

    def _apply_event_result(self, ctx, choice_id: str) -> str:
        return ctx.apply_event_result(
            self.event,
            self.label,
            choice_id=choice_id,
            post_apply=self.post_apply,
        )

    def _clear(self) -> None:
        self.event = None
        self.label = ""
        self.next_stage = "after_action"
        self.post_apply = None
