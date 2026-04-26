"""Graduation thesis phase state."""

import json
import os
import random

from game.action_def import ActionDef
from game.character import ResearchDirection
from game.state_machine import GameState, StateResult
from game.ui_messages import ui_text


class GraduationPhaseState(GameState):
    """State for graduation thesis actions."""

    @property
    def state_id(self) -> str:
        return "graduation.phase"

    def get_available_actions(self, ctx) -> list:
        thesis = ctx.graduation_thesis
        if ctx.player.year >= 3 and thesis.can_start():
            if thesis.stage.value == "未开始":
                description = f"开始毕业论文（需{thesis.required_papers}篇，当前{ctx.player.papers_published}篇）"
                return [ActionDef("8", "开题", description)]
            return [ActionDef("8", "毕业论文", "继续毕业论文")]
        return []

    def handle_action(self, ctx, action: str) -> StateResult:
        if action != "8":
            return StateResult(ui_text("invalid_action"))

        if ctx.graduation_thesis.stage.value == "未开始":
            title = self._generate_thesis_title(ctx)
            return StateResult(ctx.graduation_thesis.start_thesis(title))
        return StateResult(ctx.graduation_thesis.work_on_thesis())

    def on_enter(self, ctx, from_state=None) -> str:
        if from_state and from_state != self.state_id:
            return f"{ui_text('phase_graduation')}\n{ui_text('graduation_action_hint')}"
        return ""

    def _generate_thesis_title(self, ctx) -> str:
        data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "thesis_titles.json")
        try:
            with open(data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return "克苏鲁神话相关研究"

        direction_map = {
            ResearchDirection.ARCANE_ANALYSIS: "arcane_analysis",
            ResearchDirection.MYTHOS_RITUAL: "mythos_ritual",
            ResearchDirection.DEITY_RACE: "deity_race",
            ResearchDirection.OUTER_GOD: "outer_god",
        }
        key = direction_map.get(ctx.player.research_direction, "default")
        titles = data["titles"].get(key, data["titles"]["default"])
        return random.choice(titles)
