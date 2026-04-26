"""Turn-flow orchestration extracted from GameEngine."""

import random

from .character import SemesterType
from .ui_messages import ui_text


class TurnFlowController:
    """Own action-point consumption and turn-end progression."""

    def __init__(self, engine):
        self.engine = engine

    def consume_action_for_state_action(self) -> bool:
        """Consume action points using the original STR continue-work fallback."""
        if self.engine.player.consume_action_point(self.engine.player.advisor):
            self.engine.turn_count += 1
            return True

        if self.engine._check_continue_work():
            self.engine.player.action_points += 1
            self.engine.player.consume_action_point(self.engine.player.advisor)
            self.engine.turn_count += 1
            return True

        self.engine.log(ui_text("action_points_depleted"))
        self.engine._advance_week()
        return False

    def check_continue_work(self) -> bool:
        """Apply the original STR extra-work roll when action points are exhausted."""
        player = self.engine.player
        if player.STR > 70 and player.continue_action_count < player.max_continue_actions:
            trigger_chance = (player.STR - 70) / 2
            if random.random() * 100 < trigger_chance:
                player.continue_action_count += 1
                self.engine.log(ui_text("str_continue_work"))
                return True
        return False

    def advance_week(self, skip_pressure: bool = False) -> bool:
        """Advance the calendar by one week, including advisor pressure interruptions."""
        advisor = self.engine.player.advisor
        if not skip_pressure and advisor and advisor.personality_value >= 61:
            pressure_event = self.engine.advisor_system.trigger_pressure_event(
                self.engine.player,
                self.engine.event_system,
            )
            if pressure_event:
                result = self.engine.trigger_event(
                    pressure_event,
                    "导师事件",
                    next_stage="advance_week",
                )
                if result:
                    self.engine.log(result)
                if self.engine.state_actions.is_event_choice_state():
                    return False

        self.engine.player.advance_week()
        self.engine.player.reset_action_points()
        self.engine.log(
            f"--- 第{self.engine.player.year}学年 "
            f"{self.engine.player.semester_name} "
            f"第{self.engine.player.week_in_semester}周 ---"
        )
        return True

    def trigger_random_event(self) -> None:
        """Run the per-turn random event roll."""
        is_holiday = self.engine.player.semester in (SemesterType.SUMMER, SemesterType.WINTER)

        if is_holiday:
            event_type = "holiday" if random.random() < 0.7 else "random"
        else:
            roll = random.random()
            if roll < 0.2 and self.engine.player.advisor:
                event_type = "advisor"
            elif roll < 0.3:
                event_type = random.choice(["academic", "mythos", "social", "investigation"])
            else:
                event_type = "random"

        if random.random() < 0.3:
            if event_type == "advisor":
                event = self.engine.advisor_system.get_random_advisor_event(
                    self.engine.player,
                    self.engine.event_system,
                )
            else:
                event = self.engine.event_system.get_random_event(event_type, self.engine.player)
            if event:
                type_label = {
                    "advisor": "导师事件",
                    "holiday": "假期事件",
                    "academic": "学术事件",
                    "mythos": "神话事件",
                    "social": "社交事件",
                    "investigation": "调查事件",
                }.get(event_type, "随机事件")
                self.engine.log(self.engine.trigger_event(event, type_label, next_stage="after_random_event"))

    def trigger_inspiration_burst(self) -> None:
        """Resolve end-of-turn inspiration burst logic."""
        player = self.engine.player
        if player.research_progress < 100 or not player.research_direction:
            return

        idea_result, triggered = self.engine.research_system.generate_inspiration_idea()
        if not triggered:
            self.engine.log(idea_result)
            return

        progress_loss = random.randint(1, 100)
        sanity_mod = player.advisor.sanity_consumption_modifier if player.advisor else 1.0
        sanity_loss = int(random.randint(3, 8) * sanity_mod)
        player.research_progress = max(0, player.research_progress - progress_loss)
        player.change_sanity(-sanity_loss)

        self.engine.log("【灵感爆发】你仿佛从那梦境的都市取得了最璀璨的宝石，但是你是从何而来的，你陷入了困惑……")
        self.engine.log(f"理智-{sanity_loss}")
        self.engine.log(idea_result)

    def continue_turn(self, stage: str) -> bool:
        """Resume interrupted turn resolution from the requested stage."""
        if stage == "after_action":
            self.engine._trigger_random_event()
            if self.engine.state_actions.is_event_choice_state():
                return True
            stage = "after_random_event"

        if stage == "after_random_event":
            self.engine._trigger_inspiration_burst()
            self.engine.mutation_system.apply_mutation_effect(self.engine.player, self.engine.log)

            if self.engine.player.action_points <= 0:
                if not self.engine._advance_week():
                    return True

            self.engine.game_state.check_game_over(
                self.engine.player,
                self.engine.graduation_thesis,
                self.engine.log,
            )
            return not self.engine.game_state.is_ended()

        if stage == "advance_week":
            if not self.engine._advance_week(skip_pressure=True):
                return True
            self.engine.game_state.check_game_over(
                self.engine.player,
                self.engine.graduation_thesis,
                self.engine.log,
            )
            return not self.engine.game_state.is_ended()

        return not self.engine.game_state.is_ended()
