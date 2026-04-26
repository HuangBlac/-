"""Holiday phase state."""

import random

from game.action_def import ActionDef
from game.state_machine import GameState, StateResult
from game.ui_messages import ui_text


class HolidayPhaseState(GameState):
    """State for summer and winter holiday actions."""

    @property
    def state_id(self) -> str:
        return "holiday.phase"

    def get_available_actions(self, ctx) -> list:
        return [
            ActionDef("1", "旅游", "去外地旅游"),
            ActionDef("2", "回家", "回老家探亲"),
            ActionDef("3", "娱乐", "在宿舍娱乐"),
            ActionDef("4", "学习", "继续学习"),
            ActionDef("9", "休息", "好好休息"),
        ]

    def handle_action(self, ctx, action: str) -> StateResult:
        if ctx.player.advisor:
            holiday_event = ctx.advisor_system.trigger_holiday_event(ctx.player, ctx.event_system)
            if holiday_event:
                return StateResult(self._trigger_holiday_event(ctx, holiday_event))

        holiday_options = {
            "1": ("旅游", 20, 0, 0),
            "2": ("回家", 25, 0, 0),
            "3": ("娱乐", 15, 0, 0),
            "4": ("学习", 5, 10, 0),
            "9": ("休息", 18, 0, 0),
        }
        if action not in holiday_options:
            return StateResult("无效选择，请重试")

        name, sanity, progress, str_bonus = holiday_options[action]
        sanity_modified = int(sanity / self._get_advisor_sanity_modifier(ctx))
        ctx.player.change_sanity(sanity_modified)
        ctx.player.research_progress = min(255, max(0, ctx.player.research_progress + progress))
        if str_bonus:
            ctx.player.STR += str_bonus

        result = f"你{name}了几天\n理智+{sanity_modified}"
        if progress:
            result += f"，灵感+{progress}"
        if str_bonus:
            result += f"，STR+{str_bonus}"

        if action == "3" and random.random() < 0.4:
            extra = self._trigger_entertainment_event(ctx)
            if extra:
                result += extra

        return StateResult(result)

    def on_enter(self, ctx, from_state=None) -> str:
        if from_state and from_state.startswith("research."):
            return (
                f"{ui_text('phase_holiday')}\n"
                f"{ui_text('holiday_action_hint')}"
            )
        return ""

    def _get_advisor_sanity_modifier(self, ctx) -> float:
        if ctx.player.advisor:
            return ctx.player.advisor.sanity_consumption_modifier
        return 1.0

    def _trigger_entertainment_event(self, ctx) -> str:
        event = ctx.event_system.get_random_event("entertainment", ctx.player)
        if not event:
            return ""
        return "\n" + ctx.trigger_event(event, "随机事件", next_stage="after_action")

    def _trigger_holiday_event(self, ctx, event: dict = None) -> str:
        """Trigger a holiday event or fallback advisor task."""
        if not ctx.event_system:
            return self._trigger_holiday_task_fallback(ctx)

        if event is None:
            event = ctx.event_system.get_random_event("holiday", ctx.player)
        if not event:
            return self._trigger_holiday_task_fallback(ctx)

        return ctx.trigger_event(event, "假期事件", next_stage="after_action")

    def _trigger_holiday_task_fallback(self, ctx) -> str:
        tasks = [
            "导师在假期给你安排了任务",
            "导师要求你参加线上组会",
            "导师说有急事需要处理",
        ]
        task = random.choice(tasks)
        san_loss = int(random.randint(10, 15) * self._get_advisor_sanity_modifier(ctx))
        progress = random.randint(5, 15)

        ctx.player.change_sanity(-san_loss)
        ctx.player.research_progress = min(255, max(0, ctx.player.research_progress + progress))

        return f"【{task}】\n理智-{san_loss}，灵感+{progress}\n这个假期没法好好休息了..."
