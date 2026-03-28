"""导师系统"""
import random
from enum import Enum
from dataclasses import dataclass
from typing import Optional


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

    def trigger_pressure_event(self, player) -> Optional[str]:
        """尝试触发爆压事件

        Args:
            player: 玩家对象

        Returns:
            事件描述，如果未触发则返回None
        """
        if not self.advisor:
            return None

        # 奈亚提亚普有特殊事件
        if self.advisor.is_nyarrothotep:
            # 奈亚提亚普的爆压事件
            events = [
                "奈亚导师与你进行了一次深入的灵魂交流，你感觉世界观被完全颠覆了...",
                "奈亚导师向你展示了宇宙的真相，你的理智获得了洗礼...",
                "奈亚导师对你说：'你的研究很有趣，但还不够疯狂...'",
            ]
            self.pressure_events_triggered += 1
            # 理智回满
            player.sanity = 100
            return f"【爆压事件】{random.choice(events)}\n理智已回满！"

        # 普通导师爆压事件
        chance = self.advisor.get_pressure_event_chance()
        if random.random() < chance:
            self.pressure_events_triggered += 1

            # 性格不同，事件不同
            if self.advisor.personality_value >= 90:
                events = [
                    f"导师{self.advisor.name}打电话给你：'这个周末必须把实验结果发给我！'",
                    f"导师{self.advisor.name}发来消息：'你的进度太慢了，明天来我办公室！'",
                    f"导师{self.advisor.name}取消了你的假期：'这个假期你来做这个项目！'",
                ]
            else:
                events = [
                    f"导师{self.advisor.name}对你说：'你的研究思路有问题，需要大改！'",
                    f"导师{self.advisor.name}在组会上批评了你：'这个月的进展不尽人意！'",
                    f"导师{self.advisor.name}发来一封长邮件，列举了10个需要改进的地方...",
                ]

            # 爆压事件：理智回满，异常值增加
            player.sanity = 100
            # 异常值增加（这里暂时用mutation代表）
            player.mutation += 0.05

            return f"【爆压事件】{random.choice(events)}\n理智已回满！但你感觉有什么东西不一样了..."

        return None
