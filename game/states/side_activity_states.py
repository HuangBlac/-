"""Temporary side activity states for investigation and social actions."""

import random

from game.action_def import ActionDef
from game.state_machine import GameState, StateResult
from game.ui_messages import ui_text


class InvestigationState(GameState):
    """Temporary investigation state until the investigation event system is redesigned."""

    @property
    def state_id(self) -> str:
        return "side.investigation"

    def get_available_actions(self, ctx) -> list:
        return [ActionDef("6", "调查", "参与神秘调查")]

    def handle_action(self, ctx, action: str) -> StateResult:
        if action != "6":
            return StateResult(ui_text("invalid_action"))
        return StateResult(self._do_investigation(ctx))

    def _do_investigation(self, ctx) -> str:
        # TODO: Replace this temporary logic with the redesigned investigation event system.
        san_loss = int(random.randint(3, 8) * self._get_advisor_sanity_modifier(ctx))
        int_gain = random.randint(3, 8)
        reputation_gain = random.randint(1, 5)

        ctx.player.change_sanity(-san_loss)
        ctx.player.INT += int_gain
        ctx.player.reputation += reputation_gain

        events = [
            "你在图书馆发现了一本禁书",
            "你参加了校外的神秘聚会",
            "你跟踪了一个可疑的邪教成员",
            "你在实验室发现了奇怪的实验结果",
        ]
        return f"{random.choice(events)}\nINT+{int_gain}，声望+{reputation_gain}，理智-{san_loss}"

    def _get_advisor_sanity_modifier(self, ctx) -> float:
        if ctx.player.advisor:
            return ctx.player.advisor.sanity_consumption_modifier
        return 1.0


class SocialState(GameState):
    """Temporary social state until NPC interaction design is expanded."""

    @property
    def state_id(self) -> str:
        return "side.social"

    def get_available_actions(self, ctx) -> list:
        return [ActionDef("7", "社交", "与NPC交流")]

    def handle_action(self, ctx, action: str) -> StateResult:
        if action != "7":
            return StateResult(ui_text("invalid_action"))
        return StateResult(self._do_social(ctx))

    def _do_social(self, ctx) -> str:
        # TODO: Replace this temporary logic with the redesigned social/NPC event system.
        targets = ["导师", "同门", "同门1", "同门2"]
        target = random.choice(targets)

        favor_change = random.randint(-5, 10)
        if target in ctx.player.relationships:
            ctx.player.relationships[target] = max(
                0,
                min(100, ctx.player.relationships[target] + favor_change),
            )

        san_change = random.randint(-2, 3)
        if san_change < 0:
            san_change = int(san_change * self._get_advisor_sanity_modifier(ctx))
        ctx.player.change_sanity(san_change)

        return f"你与{target}交流了一会\n好感度变化 {favor_change:+d}，理智{san_change:+d}"

    def _get_advisor_sanity_modifier(self, ctx) -> float:
        if ctx.player.advisor:
            return ctx.player.advisor.sanity_consumption_modifier
        return 1.0
