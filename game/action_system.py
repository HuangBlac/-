"""Action dispatch layer."""

from .character import SemesterType
from .action_handlers import ActionHandlerFactory


class ActionSystem:
    """Routes player actions to the appropriate action handler.

    This class owns action dispatch state, but concrete gameplay effects live in
    handlers or lower-level systems.
    """

    def __init__(self, game_engine, player, course_system, research_system, graduation_thesis, npcs):
        self.game = game_engine
        self.player = player
        self.course_system = course_system
        self.research_system = research_system
        self.graduation_thesis = graduation_thesis
        self.npcs = npcs

        self.handlers = ActionHandlerFactory.get_all_handlers(game_engine)

        self.exam_done = False
        self.awaiting_course_selection = False

    def is_valid_action(self, action: str) -> bool:
        """Return whether the input matches a currently available action id."""
        normalized = action.strip().lower()
        if not normalized:
            return False

        valid_ids = {str(action_id).strip().lower() for action_id, _, _ in self.get_actions()}
        return normalized in valid_ids

    def do_action(self, action: str, log_func) -> tuple:
        """Dispatch an action and return (message, should_continue)."""
        if self.awaiting_course_selection:
            result = self.handlers["course"].handle_course_selection(action, log_func)
            return (result, True)

        if action == "0":
            return ("__SHOW_STATUS__", True)

        if action == "6":
            return (self.handlers["investigation"].handle(action), True)

        if action == "7":
            return (self.handlers["social"].handle(action), True)

        if action == "8":
            return (self.handlers["graduation"].handle(action), True)

        in_research = self.research_system.can_start_research()
        is_holiday = self.player.semester in (SemesterType.SUMMER, SemesterType.WINTER)

        if not in_research and not is_holiday:
            return (self.handlers["course"].handle(action), True)

        if is_holiday:
            return (self.handlers["entertainment"].handle(action), True)

        if action.lower() == "e":
            return ("__EVALUATE_IDEA__", True)

        if action == "1":
            return (self.handlers["entertainment"].handle(action), True)

        return (self.handlers["research"].handle(action), True)

    def get_actions(self) -> list:
        """Return currently available actions."""
        actions = []

        in_research = self.research_system.can_start_research()
        is_holiday = self.player.semester in (SemesterType.SUMMER, SemesterType.WINTER)

        if not in_research and not is_holiday:
            actions.extend(self.handlers["course"].get_available_actions())
        elif is_holiday:
            actions.extend(self.handlers["entertainment"].get_available_actions())
        else:
            actions.extend(self.handlers["research"].get_available_actions())
            actions.extend(self.handlers["entertainment"].get_available_actions())

        if self.player.year >= 3 and self.player.papers_published >= 1:
            actions.extend(self.handlers["graduation"].get_available_actions())

        actions.extend(self.handlers["investigation"].get_available_actions())
        actions.extend(self.handlers["social"].get_available_actions())
        actions.append(("0", "状态", "查看当前状态"))

        return actions
