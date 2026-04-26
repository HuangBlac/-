"""Course phase states."""

from game.action_def import ActionDef
from game.character import SEMESTER_WEEKS
from game.state_machine import GameState, StateResult
from game.ui_messages import ui_text


class AttendingClassesState(GameState):
    """Course phase state for selecting courses and attending classes."""

    @property
    def state_id(self) -> str:
        return "course.attending_classes"

    def get_available_actions(self, ctx) -> list:
        if self._needs_course_selection(ctx):
            return [ActionDef("1", "选课", "选择本学期课程")]
        return [ActionDef("1", "上课", "参加课程学习")]

    def handle_action(self, ctx, action: str) -> StateResult:
        if action != "1":
            return StateResult(ui_text("invalid_action"))

        if self._needs_course_selection(ctx):
            return StateResult(
                text=self._selection_prompt(ctx),
                next_state="course.selecting_courses",
                transition_notice=ui_text("course_selection_started"),
                prompt=ui_text("prompt_course_selection"),
            )

        return StateResult(ctx.course_system.attend_class(ctx.player, ctx.player.advisor))

    def on_enter(self, ctx, from_state=None) -> str:
        if from_state == "course.selecting_courses":
            return (
                f"{ui_text('course_selection_completed')}\n"
                f"{ui_text('course_after_selection_hint')}"
            )
        return ""

    def _needs_course_selection(self, ctx) -> bool:
        return ctx.player.week_in_semester == 1 and not ctx.player.courses_selected

    def _selection_prompt(self, ctx) -> str:
        ctx.log_func(ctx.course_system.get_course_selection_menu())
        return (
            "选课系统：\n"
            "必修课已自动选择：\n"
            "- 拉莱耶语初步\n"
            "- 神话文本阅读\n"
            "- 形式科学导论\n\n"
            f"{ui_text('prompt_course_selection_menu')}"
        )


class SelectingCoursesState(GameState):
    """Input state for elective course selection."""

    @property
    def state_id(self) -> str:
        return "course.selecting_courses"

    def get_available_actions(self, ctx) -> list:
        return [ActionDef("input", "输入选课编号", "输入3个编号，例如：1 2 3", costs_action_point=False)]

    def handle_action(self, ctx, action: str) -> StateResult:
        try:
            selections = [int(x.strip()) for x in action.split() if x.strip().isdigit()]
        except ValueError:
            selections = []

        if len(selections) != 3:
            return StateResult(
                ui_text("course_selection_count_error"),
                prompt=ui_text("course_selection_format_hint"),
            )

        if not ctx.course_system.select_electives(selections):
            return StateResult(
                "选课失败，请重试！\n" + ctx.course_system.get_course_selection_menu()
            )

        ctx.player.courses_selected = True
        lines = ["选课完成！你选择了："]
        for course in ctx.course_system.selected_electives:
            lines.append(f"  - {course.name}")
        return StateResult("\n".join(lines), next_state="course.attending_classes")


class FinalExamsState(GameState):
    """Course phase state for final exams."""

    @property
    def state_id(self) -> str:
        return "course.final_exams"

    def get_available_actions(self, ctx) -> list:
        return [ActionDef("1", "期末考试", "参加期末考试")]

    def handle_action(self, ctx, action: str) -> StateResult:
        if action != "1":
            return StateResult(ui_text("invalid_action"))

        if ctx.exam_system.exams_completed:
            return StateResult("你已经完成期末考试！")

        result = ctx.exam_system.hold_final_exams(ctx.player)
        ctx.player.courses_selected = True

        if ctx.player.research_unlocked:
            ctx.player.research_direction = ctx.exam_system.get_research_direction_from_courses()
            return StateResult(
                text=(
                    f"【期末考试成绩】\n{result}\n\n"
                    f"根据你的选课，你的研究方向是：{ctx.player.research_direction.value}"
                ),
                transition_notice=(
                    f"{ui_text('course_to_research')}\n"
                    f"{ui_text('course_after_exam_hint')}"
                ),
            )

        return StateResult(
            text=(
                f"【期末考试成绩】\n{result}\n\n"
                "课程尚未全部通过，暂未解锁科研方向。"
            )
        )


def is_final_exam_week(player) -> bool:
    """Return whether the player is in the course exam week."""
    total_weeks = SEMESTER_WEEKS.get(player.semester, 8)
    exam_week = max(1, total_weeks - 1)
    return player.week_in_semester >= exam_week
