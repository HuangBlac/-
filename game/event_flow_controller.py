"""Event-flow orchestration extracted from GameEngine."""


class EventFlowController:
    """Bridge event payloads into state-machine choices and effect resolution."""

    def __init__(self, engine):
        self.engine = engine

    def trigger_event(self, event: dict, label: str, next_stage: str = "after_action", post_apply=None) -> str:
        """Trigger an event and either queue player choice or resolve immediately."""
        if self.engine.event_system.has_choices(event):
            return self.queue_event_choice(event, label, next_stage, post_apply)
        return self.apply_event_result(event, label, post_apply=post_apply)

    def queue_event_choice(self, event: dict, label: str, next_stage: str, post_apply=None) -> str:
        """Push the event-choice input state and return its prompt text."""
        self.engine.event_choice_state.configure(event, label, next_stage, post_apply)
        return self.engine.state_machine.push("input.event_choice")

    def apply_event_result(
        self,
        event: dict,
        label: str,
        choice_id: str = None,
        post_apply=None,
    ) -> str:
        """Apply event effects and return the composed player-facing text."""
        lines = [f"【{label}】{event['title']}", event["description"]]

        if choice_id:
            choice = self.engine.event_system.get_choice(event, choice_id)
            if choice:
                lines.append(f"你选择了：{choice['text']}")

        effect_desc = self.engine.event_system.apply_event_effect(self.engine.player, event, choice_id)
        if effect_desc and effect_desc != "无":
            lines.append(f"效果：{effect_desc}")

        followup = self.engine.event_system.get_followup_event(event, self.engine.player)
        if followup:
            lines.append(followup["description"])
            followup_effect = self.engine.event_system.apply_event_effect(self.engine.player, followup)
            if followup_effect and followup_effect != "无":
                lines.append(f"效果：{followup_effect}")

        if post_apply:
            extra = post_apply(event, choice_id)
            if extra:
                lines.append(extra)

        return "\n".join(lines)
