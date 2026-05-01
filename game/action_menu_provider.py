"""Action menu aggregation extracted from GameEngine."""


class ActionMenuProvider:
    """Build the currently visible action list for console and GUI surfaces."""

    def __init__(self, engine):
        self.engine = engine

    def get_actions(self) -> list:
        """Return the merged action menu for the current game situation."""
        actions = self._current_phase_actions()
        if not self.engine.state_actions.is_temporary_input_state():
            self._append_unique(actions, self._graduation_actions())
            self._append_unique(actions, self._side_actions())
        self._append_system_actions(actions)
        return actions

    def _current_phase_actions(self) -> list:
        if self.engine.state_actions.is_temporary_input_state():
            return self._state_machine_actions()

        if self.engine.state_actions.uses_course_state_machine() or self.engine.state_actions.is_course_selection_input_state():
            self.engine.state_actions.sync_course_state()
            actions = self._state_machine_actions()
            actions.append(("0", "状态", "查看当前状态"))
            return actions

        if self.engine.state_actions.uses_research_state_machine():
            current_id = self.engine.state_machine.current.state_id
            if not current_id.startswith("research."):
                self.engine.state_actions.sync_state("research.phase")
            return self._state_machine_actions()

        if self.engine.state_actions.uses_holiday_state_machine():
            self.engine.state_actions.sync_state("holiday.phase")
            return self._state_machine_actions()

        return []

    def _state_machine_actions(self) -> list:
        return [action_def.as_tuple() for action_def in self.engine.state_machine.get_available_actions()]

    def _graduation_actions(self) -> list:
        if not self.engine.state_actions.graduation_action_available():
            return []
        return [
            action_def.as_tuple()
            for action_def in self.engine.graduation_state.get_available_actions(self.engine.game_context)
        ]

    def _side_actions(self) -> list:
        actions = []
        for state_id in ["side.investigation", "side.social"]:
            state = self.engine.state_machine._states[state_id]
            actions.extend(action_def.as_tuple() for action_def in state.get_available_actions(self.engine.game_context))
        return actions

    def _append_unique(self, actions: list, additions: list) -> None:
        existing_ids = {action_id for action_id, _, _ in actions}
        for action in additions:
            if action[0] not in existing_ids:
                actions.append(action)
                existing_ids.add(action[0])

    def _append_system_actions(self, actions: list) -> None:
        existing_ids = {action_id for action_id, _, _ in actions}
        if "0" not in existing_ids:
            actions.append(("0", "状态", "查看当前状态"))
        actions.append(("q", "退出", "结束游戏"))
