"""Side activity states for investigation and social actions (JSON-driven)."""

import random

from game.action_def import ActionDef
from game.state_machine import GameState, StateResult
from game.ui_messages import ui_text


class InvestigationState(GameState):
    """Investigation state — loads events from JSON."""

    @property
    def state_id(self) -> str:
        return "side.investigation"

    def get_available_actions(self, ctx) -> list:
        remaining = ctx.player.investigation_max_per_week - ctx.player.investigation_this_week
        if remaining <= 0:
            return []
        return [ActionDef("6", "调查", f"进行神秘调查（本周剩余{remaining}次）")]

    def handle_action(self, ctx, action: str) -> StateResult:
        if action != "6":
            return StateResult(ui_text("invalid_action"))

        ctx.player.investigation_this_week += 1
        ctx.player.investigation_count += 1

        events = ctx.event_system.get_investigation_events(ctx.player)
        if not events:
            return StateResult("你四处查看，但没有发现什么异常。")

        event = random.choice(events)
        description = ctx.event_system.get_event_description(event, ctx.player)

        output = f"【{event['title']}】\n\n{description}"

        if ctx.event_system.has_choices(event):
            return StateResult(
                output,
                push_state="input.event_choice",
                state_data={"event": event},
            )

        effect_msg = ctx.event_system.apply_event_effect(ctx.player, event)
        if effect_msg:
            output += f"\n\n{effect_msg}"

        # 硕士阶段：调查有30%概率获得科研灵感
        if random.random() < 0.3:
            ctx.player.research_progress += 5
            output += "\n[你在调查中获得了一丝科研灵感]"

        return StateResult(output)


class SocialState(GameState):
    """Social state — loads events from JSON with revelation-level support."""

    @property
    def state_id(self) -> str:
        return "side.social"

    def get_available_actions(self, ctx) -> list:
        return [ActionDef("7", "社交", "与NPC交流")]

    def handle_action(self, ctx, action: str) -> StateResult:
        if action != "7":
            return StateResult(ui_text("invalid_action"))

        ctx.player.social_count += 1

        events = ctx.event_system.get_social_events(ctx.player)
        if not events:
            return StateResult("你环顾四周，没什么特别的社交机会。")

        event = random.choice(events)
        ctx.player.social_events_seen.add(event.get("id"))

        description = ctx.event_system.get_event_description(event, ctx.player)

        output = f"【{event['title']}】\n\n{description}"

        if ctx.event_system.has_choices(event):
            return StateResult(
                output,
                push_state="input.event_choice",
                state_data={"event": event},
            )

        effect_msg = ctx.event_system.apply_event_effect(ctx.player, event)
        if effect_msg:
            output += f"\n\n{effect_msg}"

        return StateResult(output)
