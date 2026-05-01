"""State-machine execution helpers extracted from GameEngine."""

from .character import SemesterType
from .states.course_phase import is_final_exam_week
from .ui_messages import ui_text


class StateActionExecutor:
    """Own the state-machine orchestration that should not live in GameEngine."""

    def __init__(self, engine):
        self.engine = engine

    def uses_course_state_machine(self) -> bool:
        """Return whether current input should be handled by course states."""
        is_holiday = self.engine.player.semester in (SemesterType.SUMMER, SemesterType.WINTER)
        return not self.engine.research_system.can_start_research() and not is_holiday

    def uses_research_state_machine(self) -> bool:
        """Return whether current input should be handled by the research state."""
        is_holiday = self.engine.player.semester in (SemesterType.SUMMER, SemesterType.WINTER)
        return self.engine.research_system.can_start_research() and not is_holiday

    def uses_holiday_state_machine(self) -> bool:
        """Return whether current input should be handled by the holiday state."""
        return self.engine.player.semester in (SemesterType.SUMMER, SemesterType.WINTER)

    def graduation_action_available(self) -> bool:
        """Return whether graduation thesis actions should be exposed."""
        return self.engine.player.year >= 3 and self.engine.graduation_thesis.can_start()

    def normalize_action(self, action: str) -> str:
        """Normalize player input for state-action matching."""
        return action.strip().lower()

    def current_state_action_ids(self) -> set[str]:
        """Return normalized action ids exposed by the current state."""
        return {
            action_def.key.strip().lower()
            for action_def in self.engine.state_machine.get_available_actions()
        }

    def log_state_result(self, result) -> None:
        """Write player-facing state output to the message log."""
        if result.text:
            self.engine.log(result.text)
        if result.transition_notice:
            self.engine.log(result.transition_notice)
        if result.prompt:
            self.engine.log(result.prompt)

    def sync_state(self, target_state: str, *, allow_temporary: bool = False) -> None:
        """Keep the active state aligned with the requested phase state."""
        if not allow_temporary and self.is_temporary_input_state():
            return

        if self.engine.state_machine.current.state_id == target_state:
            return

        notice = self.engine.state_machine.transition_to(target_state)
        if notice:
            self.engine.log(notice)

    def current_course_state_id(self) -> str:
        """Return the calendar-driven course state id."""
        if is_final_exam_week(self.engine.player):
            return "course.final_exams"
        return "course.attending_classes"

    def run_state_action(
        self,
        action: str,
        *,
        target_state: str = "",
        consume_action_point: bool,
        validate_action: bool = False,
        continue_stage: str = "",
        stop_on_temporary: bool = False,
        check_blocking: bool = False,
    ) -> bool:
        """Run a state-machine action with shared sync, validation, logging, and turn flow."""
        if target_state:
            self.sync_state(target_state)

        if validate_action and self.normalize_action(action) not in self.current_state_action_ids():
            self.engine.log(ui_text("invalid_action"))
            return True

        if check_blocking:
            blocking_message = self.engine.state_machine.current.get_blocking_message(
                self.engine.game_context,
                action,
            )
            if blocking_message:
                self.engine.log(blocking_message)
                return True

        if consume_action_point and not self.engine.turn_flow.consume_action_for_state_action():
            return not self.engine.game_state.is_ended()

        result = self.engine.state_machine.handle_action(action)
        self.log_state_result(result)

        if result.resume_stage:
            return self.engine.turn_flow.continue_turn(result.resume_stage)
        if stop_on_temporary and self.is_temporary_input_state():
            return True
        if continue_stage:
            return self.engine.turn_flow.continue_turn(continue_stage)
        return not self.engine.game_state.is_ended()

    def is_research_state_action(self, action: str) -> bool:
        """Return whether the action belongs to the research phase state."""
        if not self.uses_research_state_machine():
            return False
        current_id = self.engine.state_machine.current.state_id
        # 如果已经在 research 子状态（如 submission_target），不要强制切回 phase
        if not current_id.startswith("research."):
            self.sync_state("research.phase")
        return self.normalize_action(action) in self.current_state_action_ids()

    def is_holiday_state_action(self, action: str) -> bool:
        """Return whether the action belongs to the holiday phase state."""
        if not self.uses_holiday_state_machine():
            return False
        self.sync_state("holiday.phase")
        return self.normalize_action(action) in self.current_state_action_ids()

    def is_graduation_state_action(self, action: str) -> bool:
        """Return whether the action belongs to the graduation phase state."""
        if action.strip() != "8":
            return False
        if not self.graduation_action_available():
            return False
        valid_ids = {
            action_def.key.strip().lower()
            for action_def in self.engine.graduation_state.get_available_actions(self.engine.game_context)
        }
        return self.normalize_action(action) in valid_ids

    def is_side_activity_action(self, action: str) -> bool:
        """Return whether the action belongs to side activity states."""
        return action.strip() in {"6", "7"}

    def is_course_selection_input_state(self) -> bool:
        """Return whether the course state is waiting for free-form selection input."""
        return self.engine.state_machine.current.state_id == "course.selecting_courses"

    def is_event_choice_state(self) -> bool:
        """Return whether the state machine is waiting for event-choice input."""
        return self.engine.state_machine.current.state_id == "input.event_choice"

    def is_temporary_input_state(self) -> bool:
        """Return whether the current state is a no-cost temporary input state."""
        current_id = self.engine.state_machine.current.state_id
        return current_id.startswith("input.") or current_id in (
            "research.idea_decision",
            "research.submission_target",
        )

    def do_temporary_input_action(self, action: str) -> bool:
        """Handle no-cost temporary input states and resume any deferred flow."""
        return self.run_state_action(action, consume_action_point=False)

    def sync_course_state(self) -> None:
        """Keep the course state aligned with calendar-driven exam timing."""
        if self.is_course_selection_input_state():
            return
        self.sync_state(self.current_course_state_id())

    def do_course_state_action(self, action: str, costs_action_point: bool) -> bool:
        """Handle course-stage input through the state machine."""
        return self.run_state_action(
            action,
            target_state=self.current_course_state_id() if costs_action_point else "",
            consume_action_point=costs_action_point,
            validate_action=costs_action_point,
            continue_stage="after_action" if costs_action_point else "",
        )

    def do_research_state_action(self, action: str) -> bool:
        """Handle research-stage input through the state machine."""
        current_id = self.engine.state_machine.current.state_id
        # 如果已经在 research 子状态（如 submission_target），不要强制切回 phase
        target = "research.phase" if not current_id.startswith("research.") else ""
        return self.run_state_action(
            action,
            target_state=target,
            consume_action_point=True,
            continue_stage="after_action",
            stop_on_temporary=True,
            check_blocking=True,
        )

    def do_graduation_state_action(self, action: str) -> bool:
        """Handle graduation thesis input through the state machine."""
        return self.run_state_action(
            action,
            target_state="graduation.phase",
            consume_action_point=True,
            continue_stage="after_action",
        )

    def do_side_activity_action(self, action: str) -> bool:
        """Handle investigation and social temporary states through the state machine."""
        target_state = "side.investigation" if action == "6" else "side.social"
        return self.run_state_action(
            action,
            target_state=target_state,
            consume_action_point=True,
            continue_stage="after_action",
        )

    def do_holiday_state_action(self, action: str) -> bool:
        """Handle holiday-stage input through the state machine."""
        return self.run_state_action(
            action,
            target_state="holiday.phase",
            consume_action_point=True,
            validate_action=True,
            continue_stage="after_action",
            stop_on_temporary=True,
        )
