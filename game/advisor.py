"""导师系统"""
import random
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional


ADVISOR_TRIGGER_CONDITIONS = {
    "high_pressure",
    "extreme",
    "nyarlathotep",
    "has_assistant",
    "low_ability",
    "high_ability",
}


class AdvisorPersonality(Enum):
    """导师性格类型（压力等级）"""
    LAZY = "佛系羊导"          # 1-30
    NORMAL = "中庸导师"        # 31-60
    PUSH = "高压导师"          # 61-90
    EXTREME = "无假期导师"     # 91-100


class AdvisorRace(Enum):
    """导师种族"""
    HUMAN = "人类"
    DEEP_ONE = "深潜者"
    MIGO = "米-戈"
    ELDER_THING = "古老者"
    FLATULENT = "伊斯之伟大种族"
    NYARLATHOTEP = "奈亚提亚普"


# 导师名字库
ADVISOR_NAMES = {
    AdvisorRace.HUMAN: ["黄教授", "张教授", "李教授", "王教授", "刘教授", "陈教授", "赵教授", "孙教授"],
    AdvisorRace.DEEP_ONE: ["深潜教授", "海洋学者", "深渊导师", "深海研究员"],
    AdvisorRace.MIGO: ["米-戈教授", "星之学者", "维度导师", "米格教授"],
    AdvisorRace.ELDER_THING: ["上古导师", "远古教授", "古老学者", "远古研究员"],
    AdvisorRace.FLATULENT: ["伊斯教授", "伟大导师", "全知学者", "永恒研究员"],
    AdvisorRace.NYARLATHOTEP: ["导师"],
}


@dataclass
class Advisor:
    """导师"""
    name: str
    personality_value: int  # 1-100 压力值
    ability_value: int      # 0-99 能力值
    race: AdvisorRace       # 种族

    @property
    def personality(self) -> AdvisorPersonality:
        """获取性格类型"""
        if self.personality_value <= 30:
            return AdvisorPersonality.LAZY
        elif self.personality_value <= 60:
            return AdvisorPersonality.NORMAL
        elif self.personality_value <= 90:
            return AdvisorPersonality.PUSH
        else:
            return AdvisorPersonality.EXTREME

    @property
    def display_ability(self) -> str:
        """显示能力值（80-95时显示-20的小括号）"""
        if 80 <= self.ability_value <= 95:
            actual = self.ability_value - 20
            return f"{self.ability_value}({actual})"
        return str(self.ability_value)

    @property
    def has_assistant(self) -> bool:
        """是否有小导（能力值>80）"""
        return self.ability_value > 80

    @property
    def assistant_ability(self) -> Optional[int]:
        """小导能力值（如果存在）"""
        if self.has_assistant:
            return max(0, self.ability_value - 20)
        return None

    @property
    def is_eldritch(self) -> bool:
        """是否是非人类超凡生物（能力值>=95）"""
        return self.ability_value >= 95

    @property
    def is_nyarrothotep(self) -> bool:
        """是否是奈亚提亚普（能力值=99）"""
        return self.ability_value == 99

    @property
    def graduation_requirement(self) -> int:
        """计算毕业所需论文数"""
        # 基础要求1篇
        required = 1
        # 高能力导师要求更高
        if self.ability_value > 60:
            required += 1
        if self.ability_value > 80:
            required += 1
        if self.personality_value >= 90:
            required += 1
        # 奈亚提亚普特殊要求
        if self.is_nyarrothotep:
            required = 5  # 需要5篇顶刊
        return required

    @property
    def efficiency_modifier(self) -> float:
        """科研效率修正"""
        eff = 1.0
        if self.personality_value <= 30:
            eff *= 0.8
        elif self.personality_value >= 61:
            eff *= 1.2
        if self.personality_value >= 90:
            eff *= 1.5
        return eff

    @property
    def sanity_consumption_modifier(self) -> float:
        """理智消耗修正"""
        san = 1.0
        if self.personality_value <= 30:
            san *= 0.7
        elif self.personality_value >= 61:
            san *= 1.3
        if self.personality_value >= 90:
            san *= 1.5
        return san

    @property
    def action_consumption_modifier(self) -> float:
        """行动力消耗修正（>=90时）"""
        if self.personality_value >= 90:
            return 1.3
        return 1.0

    @property
    def has_title(self) -> bool:
        """是否有title（能力值>60）"""
        return self.ability_value > 60

    @property
    def requires_lateral_work(self) -> bool:
        """是否需要做横向（能力值<40）"""
        return self.ability_value < 40

    @property
    def can_get_funding(self) -> bool:
        """是否可以申请学生基金（有小导时）"""
        return self.has_assistant

    def get_description(self) -> str:
        """获取导师描述"""
        desc = f"{self.name}（{self.race.value}）\n"
        desc += f"性格：{self.personality.value}（压力值：{self.personality_value}）\n"
        desc += f"能力：{self.display_ability}"

        if self.has_assistant:
            desc += f"\n配有助理导师（能力值：{self.assistant_ability}）"
        if self.is_eldritch:
            desc += "\n注：此导师为非人类超凡生物"
        if self.is_nyarrothotep:
            desc += "\n注：此导师为奈亚提亚普的化身"

        return desc

    def get_pressure_event_chance(self) -> float:
        """获取爆压事件触发概率"""
        base = 0.05  # 基础5%
        if self.personality_value >= 90:
            base += 0.15
        elif self.personality_value >= 61:
            base += 0.05
        return base


def generate_advisor(race: AdvisorRace = None) -> Advisor:
    """生成随机导师

    Args:
        race: 指定种族（可选，不指定则随机）

    Returns:
        Advisor对象
    """
    # 确定种族
    if race is None:
        # 95%以上是非人类，99是奈亚提亚普
        roll = random.randint(1, 100)
        if roll == 99:
            race = AdvisorRace.NYARLATHOTEP
        elif roll >= 95:
            # 非人类超凡生物
            race = random.choice([
                AdvisorRace.DEEP_ONE,
                AdvisorRace.MIGO,
                AdvisorRace.ELDER_THING,
                AdvisorRace.FLATULENT,
            ])
        else:
            race = AdvisorRace.HUMAN

    # 随机名字
    name = random.choice(ADVISOR_NAMES.get(race, ADVISOR_NAMES[AdvisorRace.HUMAN]))

    # 随机压力值和能力值
    personality_value = random.randint(1, 100)
    ability_value = random.randint(0, 99)

    return Advisor(
        name=name,
        personality_value=personality_value,
        ability_value=ability_value,
        race=race,
    )


class AdvisorSystem:
    """导师系统管理器"""

    def __init__(self):
        self.advisor: Optional[Advisor] = None
        self.pressure_events_triggered = 0  # 爆压事件触发次数

    def assign_advisor(self, race: AdvisorRace = None) -> Advisor:
        """分配导师

        Args:
            race: 指定种族（可选）

        Returns:
            分配的导师
        """
        self.advisor = generate_advisor(race)
        return self.advisor

    def get_graduation_requirement_text(self) -> str:
        """获取毕业要求文本"""
        if not self.advisor:
            return "尚未分配导师"

        req = self.advisor.graduation_requirement
        return f"你需要发表{req}篇论文才能毕业"

    @staticmethod
    def is_advisor_trigger_condition(trigger: Optional[str]) -> bool:
        """Return whether a trigger condition depends on advisor-specific rules."""
        return trigger in ADVISOR_TRIGGER_CONDITIONS

    def _matches_event_requirements(self, event: Dict, player) -> bool:
        """Check event requirements for advisor-managed event selection."""
        req = event.get("requirement")
        if not req:
            return True

        for key, value in req.items():
            player_val = getattr(player, key, 0)

            if isinstance(value, str) and value.startswith((">=", ">", "<=", "<")):
                op = value[:2] if len(value) > 1 and value[1] in "=<>" else value[0]
                threshold = float(value[len(op):])
                if op == ">=" and player_val < threshold:
                    return False
                if op == ">" and player_val <= threshold:
                    return False
                if op == "<=" and player_val > threshold:
                    return False
                if op == "<" and player_val >= threshold:
                    return False
                continue

            if key == "sanity":
                if player.sanity > value:
                    return False
            elif player_val < value:
                return False

        return True

    def _matches_managed_trigger(self, trigger: Optional[str], player) -> bool:
        """Check triggers that advisor-owned event selection is responsible for."""
        if trigger in (None, "always", "normal", "random", "rare", "periodic", "weekly"):
            return True
        if trigger == "high_pressure":
            return bool(player.advisor and player.advisor.personality_value >= 61)
        if trigger == "extreme":
            return bool(player.advisor and player.advisor.personality_value >= 90)
        if trigger == "nyarlathotep":
            return bool(player.advisor and player.advisor.is_nyarrothotep)
        if trigger == "has_assistant":
            return bool(player.advisor and player.advisor.has_assistant)
        if trigger == "low_ability":
            return bool(player.advisor and player.advisor.requires_lateral_work)
        if trigger == "high_ability":
            return bool(player.advisor and player.advisor.ability_value > 60)
        if trigger == "low_progress":
            return player.research_progress < 50
        if trigger == "high_progress":
            return player.research_progress >= 100
        if trigger == "high_reputation":
            return player.reputation >= 10
        return False

    def _get_matching_events(self, player, event_system, event_type: str, advisor_only: bool = False) -> List[Dict]:
        """Load raw events and centralize advisor-related filtering here."""
        if not event_system:
            return []

        matches = []
        for event in event_system.get_events(event_type):
            trigger = event.get("trigger_condition")
            if advisor_only and not self.is_advisor_trigger_condition(trigger):
                continue
            if not self._matches_event_requirements(event, player):
                continue
            if not self._matches_managed_trigger(trigger, player):
                continue
            matches.append(event)
        return matches

    def get_advisor_events(self, player, event_system) -> List[Dict]:
        """Return advisor event candidates with all advisor logic centralized here."""
        return self._get_matching_events(player, event_system, "advisor")

    def get_advisor_pressure_events(self, player, event_system) -> List[Dict]:
        """Return advisor pressure event candidates with centralized filtering."""
        return self._get_matching_events(player, event_system, "advisor_pressure")

    def get_advisor_holiday_events(self, player, event_system) -> List[Dict]:
        """Return holiday events that are specifically driven by advisor rules."""
        return self._get_matching_events(player, event_system, "holiday", advisor_only=True)

    def get_entertainment_events(self, player, event_system) -> List[Dict]:
        """Return entertainment events with advisor triggers resolved here."""
        return self._get_matching_events(player, event_system, "entertainment")

    def get_random_advisor_event(self, player, event_system) -> Optional[dict]:
        """Pick a regular advisor event."""
        events = self.get_advisor_events(player, event_system)
        if not events:
            return None
        return random.choice(events)

    def trigger_pressure_event(self, player, event_system) -> Optional[dict]:
        """尝试触发导师爆压事件。

        Args:
            player: 玩家对象
            event_system: 事件系统实例

        Returns:
            事件字典，如果未触发则返回None
        """
        if not self.advisor or not event_system:
            return None
        if self.advisor.personality_value < 61:
            return None

        if random.random() >= self.advisor.get_pressure_event_chance():
            return None

        pressure_events = self.get_advisor_pressure_events(player, event_system)
        if not pressure_events:
            return None

        self.pressure_events_triggered += 1
        return random.choice(pressure_events)

    def trigger_holiday_event(self, player, event_system) -> Optional[dict]:
        """Try to trigger an advisor-interrupted holiday event."""
        if not self.advisor or not event_system:
            return None

        if random.random() >= self.advisor.get_pressure_event_chance():
            return None

        holiday_events = self.get_advisor_holiday_events(player, event_system)
        if not holiday_events:
            return None

        return random.choice(holiday_events)

    def get_random_entertainment_event(self, player, event_system) -> Optional[dict]:
        """Pick an entertainment event while keeping advisor conditions centralized."""
        entertainment_events = self.get_entertainment_events(player, event_system)
        if not entertainment_events:
            return None
        return random.choice(entertainment_events)

    def apply_entertainment_adjustments(self, player, event: Dict, event_system, choice_id: str = None) -> str:
        """Apply advisor-specific aftermath for semester entertainment events."""
        if not player.advisor:
            return ""

        notes = []
        sanity_delta = self._get_positive_sanity_reduction(player, event, event_system, choice_id)
        if sanity_delta > 0:
            player.change_sanity(-sanity_delta)
            notes.append(f"导师压力让你没能完全放松，理智-{sanity_delta}")

        if player.advisor.personality_value >= 61 and random.random() < 0.15:
            caught_san_loss = int(3 * player.advisor.sanity_consumption_modifier)
            player.change_sanity(-caught_san_loss)
            player.relationships["导师"] = max(0, player.relationships.get("导师", 50) - 2)
            notes.append("【被抓包】导师路过时看到你在摸鱼")
            notes.append(f"理智-{caught_san_loss}，导师好感-2")

        return "\n".join(notes)

    def _get_positive_sanity_reduction(self, player, event: Dict, event_system, choice_id: str = None) -> int:
        """Return how much positive sanity recovery should be reduced by advisor pressure."""
        advisor = player.advisor
        if not advisor:
            return 0

        modifier = advisor.sanity_consumption_modifier
        if modifier == 1.0:
            return 0

        total_reduction = self._get_effect_sanity_reduction(
            self._get_event_effect(event, event_system, choice_id),
            modifier,
        )

        followup = event_system.get_followup_event(event, player) if event_system else None
        if followup:
            total_reduction += self._get_effect_sanity_reduction(followup.get("effect", {}), modifier)

        return total_reduction

    @staticmethod
    def _get_effect_sanity_reduction(effect: Dict, modifier: float) -> int:
        sanity_gain = effect.get("sanity", 0)
        if sanity_gain <= 0:
            return 0
        return sanity_gain - int(sanity_gain / modifier)

    @staticmethod
    def _get_event_effect(event: Dict, event_system, choice_id: str = None) -> Dict:
        if choice_id and event_system:
            choice = event_system.get_choice(event, choice_id)
            if choice:
                return choice.get("effect", {})
            return {}
        return event.get("effect", {})
