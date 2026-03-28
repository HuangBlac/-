"""角色系统"""
import random
from enum import Enum
from typing import Optional
from dataclasses import dataclass


# ========== 判定结果 ==========
class CheckResult:
    """判定结果类型"""
    CRITICAL_SUCCESS = "大成功"   # 骰点=1
    EXTREME_SUCCESS = "极难成功"  # <能力值/5
    HARD_SUCCESS = "困难成功"    # <能力值/2
    SUCCESS = "一般成功"          # <能力值
    FAILURE = "失败"             # >能力值 且 <=95
    CRITICAL_FAILURE = "大失败"  # 96-100


def ability_check(player, ability: str, difficulty: int = None) -> tuple:
    """能力检定

    判定机制（1d100）:
    - 骰点=1: 大成功
    - 骰点 < 能力值/5: 极难成功
    - 骰点 < 能力值/2: 困难成功
    - 骰点 < 能力值: 一般成功
    - 骰点 > 能力值 且 <=95: 失败
    - 骰点 96-100: 大失败

    Args:
        player: 玩家对象
        ability: 属性名 ("INT", "SEN", "EDU", "STR", "SOC")
        difficulty: 自定义难度（可选，如果不传则使用属性值）

    Returns:
        (result: str, roll: int)
        result: CheckResult中的判定结果
        roll: 骰点值(1-100)
    """
    # 获取属性值
    ability_value = getattr(player, ability, 50)
    if ability_value is None:
        ability_value = 50

    # 计算难度阈值
    if difficulty is None:
        difficulty = ability_value

    # 投掷骰子
    roll = random.randint(1, 100)

    # 理智修正（理智越低，判定越难）
    sanity_modifier = 1.0
    if player.sanity < 30:
        sanity_modifier = 0.6
    elif player.sanity < 50:
        sanity_modifier = 0.8

    # 计算修正后的阈值
    extreme_threshold = max(1, int(difficulty // 5 * sanity_modifier))
    hard_threshold = max(1, int(difficulty // 2 * sanity_modifier))

    # 判定
    if roll == 1:
        result = CheckResult.CRITICAL_SUCCESS
    elif roll <= extreme_threshold:
        result = CheckResult.EXTREME_SUCCESS
    elif roll <= hard_threshold:
        result = CheckResult.HARD_SUCCESS
    elif roll < difficulty:
        result = CheckResult.SUCCESS
    elif roll <= 95:
        result = CheckResult.FAILURE
    else:
        result = CheckResult.CRITICAL_FAILURE

    return result, roll


def generate_attributes() -> dict:
    """生成玩家属性

    每个属性1d100随机生成，单项≥10，总和≥300
    """
    while True:
        attributes = {
            "INT": random.randint(1, 100),  # 直觉
            "SEN": random.randint(1, 100),  # 感知
            "EDU": random.randint(1, 100),  # 知识
            "STR": random.randint(1, 100),  # 耐力
            "SOC": random.randint(1, 100),  # 社交
        }

        # 检查是否符合要求
        if all(v >= 10 for v in attributes.values()) and sum(attributes.values()) >= 300:
            return attributes


class SemesterType(Enum):
    """学期类型"""
    SPRING = "上学期"      # 8周
    SUMMER = "暑假"        # 4周
    AUTUMN = "下学期"      # 9周
    WINTER = "寒假"        # 2周


class ResearchDirection(Enum):
    """研究方向"""
    ARCANE_ANALYSIS = "法术与超自然科技分析"      # 形式科学建模分析
    MYTHOS_RITUAL = "神话文本与仪式构造"          # 钻研典籍
    DEITY_RACE = "神明附属种族与独立种族"          # 田野调查
    OUTER_GOD = "旧日支配者与外神"                 # 理论研究


# 每年各学期的周数
SEMESTER_WEEKS = {
    SemesterType.SPRING: 8,
    SemesterType.SUMMER: 4,
    SemesterType.AUTUMN: 9,
    SemesterType.WINTER: 2,
}


class Player:
    """玩家角色"""

    def __init__(self, name: str):
        self.name = name
        self.year = 1  # 研几
        self.semester = SemesterType.SPRING  # 当前学期
        self.week_in_semester = 1  # 学期内第几周
        self.age = 22  # 年龄
        self.action_points = 3  # 当前行动点
        self.max_action_points = 3  # 每周最大行动点

        # ========== 新属性系统 (2026-03-27) ==========
        # 新五维属性
        attrs = generate_attributes()
        self.INT = attrs["INT"]  # 直觉: 创新、应对挑战
        self.SEN = attrs["SEN"]  # 感知: 操作精度、发现细节
        self.EDU = attrs["EDU"]  # 知识: 研究效率、理解深度
        self.STR = attrs["STR"]  # 耐力: 长时间活动、不消耗行动点
        self.SOC = attrs["SOC"]  # 社交: 交流、获取资源

        # 核心数值
        self.sanity = 100  # 理智 (SAN)
        self.reputation = 0  # 学术声望

        # 异变值（新增）
        self.mutation = 0  # 异变程度，影响UI

        # 继续工作触发次数限制
        self.continue_action_count = 0  # STR>70时触发"继续工作"的次数
        self.max_continue_actions = 10  # 每局最多触发次数

        # 旧属性（兼容保留）
        self.knowledge = 10  # 知识（用于部分事件判定）
        self.inspiration = 10  # 灵感（用于部分事件判定）

        # 导师相关（研一自动分配）
        self.advisor = None  # 导师对象
        self.advisor_assigned = False  # 是否已分配导师
        self.graduation_required_papers = 1  # 毕业所需论文数
        # 选课相关
        self.courses_selected = False  # 是否已选课
        self.required_courses = []  # 必修课
        self.elective_courses = []  # 选修课
        self.research_direction: Optional[ResearchDirection] = None  # 研究方向

        # 研究相关
        self.research_progress = 0  # 研究进度 0-100
        self.current_paper = None  # 当前论文
        self.papers_published = 0  # 已发表论文数

        # 人际关系
        self.relationships = {
            "导师": 50,
            "同门": 50,
            "评审": 50,
        }

        # 状态
        self.status = []  # 当前状态（如：疯狂、神志清醒）

    def get_attributes(self) -> dict:
        """获取新五维属性"""
        return {
            "INT直觉": self.INT,
            "SEN感知": self.SEN,
            "EDU知识": self.EDU,
            "STR耐力": self.STR,
            "SOC社交": self.SOC,
        }

    @property
    def mutation_level(self) -> str:
        """异变等级描述"""
        if self.mutation <= 0:
            return "无异变"
        elif self.mutation < 0.5:
            return "轻微异变"
        elif self.mutation < 1:
            return "中度异变"
        elif self.mutation < 2:
            return "严重异变"
        else:
            return "极度危险"

    @property
    def is_mutated(self) -> bool:
        """是否有异变"""
        return self.mutation > 0

    @property
    def sanity_level(self) -> str:
        """理智等级描述"""
        if self.sanity >= 80:
            return "神志清醒"
        elif self.sanity >= 60:
            return "有些不安"
        elif self.sanity >= 40:
            return "精神恍惚"
        elif self.sanity >= 20:
            return "濒临崩溃"
        else:
            return "彻底疯狂"

    @property
    def year_name(self) -> str:
        """学年名称"""
        year_names = {1: "研一", 2: "研二", 3: "研三"}
        return year_names.get(self.year, "已毕业")

    @property
    def semester_name(self) -> str:
        """学期名称"""
        return self.semester.value

    def get_max_action_points(self) -> int:
        """根据年级获取每周最大行动点"""
        action_map = {1: 2, 2: 3, 3: 4}
        return action_map.get(self.year, 3)

    def consume_action_point(self) -> bool:
        """消耗一次行动点，返回是否成功（行动点不足返回False）"""
        if self.action_points > 0:
            self.action_points -= 1
            return True
        return False

    def change_sanity(self, amount: int, force_mutation: bool = False) -> bool:
        """改变理智值

        Args:
            amount: 理智变化量（负数减少，正数恢复）
            force_mutation: 是否强制触发异变（用于理智归零时）

        Returns:
            是否触发了异变（理智归零时返回True）
        """
        old_sanity = self.sanity
        self.sanity = max(0, min(100, self.sanity + amount))

        # 理智从正数变为0：触发异变
        if old_sanity > 0 and self.sanity == 0:
            self.mutation += 1
            self.sanity = 50  # 恢复一半理智
            return True

        return False

    def add_skill(self, skill_name: str, amount: int = 1):
        """增加技能经验"""
        if skill_name in self.skills:
            self.skills[skill_name] += amount

    def advance_week(self):
        """推进一周（每学期内推进）"""
        self.week_in_semester += 1
        semester_weeks = SEMESTER_WEEKS[self.semester]

        if self.week_in_semester > semester_weeks:
            # 切换到下个学期
            self.week_in_semester = 1
            self._next_semester()

    def _next_semester(self):
        """切换到下个学期"""
        if self.semester == SemesterType.SPRING:
            self.semester = SemesterType.SUMMER
        elif self.semester == SemesterType.SUMMER:
            self.semester = SemesterType.AUTUMN
        elif self.semester == SemesterType.AUTUMN:
            self.semester = SemesterType.WINTER
        elif self.semester == SemesterType.WINTER:
            # 寒假结束，学年+1
            self.semester = SemesterType.SPRING
            self.year += 1
            self.age += 1

    def reset_action_points(self):
        """重置行动点（每周开始时调用）"""
        self.action_points = self.get_max_action_points()

    def get_status(self) -> dict:
        """获取当前状态"""
        status = {
            "姓名": self.name,
            "年级": self.year_name,
            "学期": self.semester_name,
            "周数": f"第{self.week_in_semester}周",
            "行动点": f"{self.action_points}/{self.max_action_points}",
            "年龄": f"{self.age}岁",
            "理智": f"{self.sanity}/100 ({self.sanity_level})",
            "异变": f"{self.mutation:.2f} ({self.mutation_level})",
            "INT直觉": self.INT,
            "SEN感知": self.SEN,
            "EDU知识": self.EDU,
            "STR耐力": self.STR,
            "SOC社交": self.SOC,
            "声望": self.reputation,
            "研究方向": self.research_direction.value if self.research_direction else "未选择",
            "已发表论文": self.papers_published,
            "毕业要求": f"{self.graduation_required_papers}篇",
        }

        # 添加导师信息
        if self.advisor:
            status["导师"] = f"{self.advisor.name}（{self.advisor.race.value}）"
            status["导师能力"] = self.advisor.display_ability
            status["导师性格"] = self.advisor.personality.value

        return status

    def is_alive(self) -> bool:
        """是否还活着"""
        return self.sanity > 0 and "死亡" not in self.status


class NPC:
    """NPC角色"""

    def __init__(self, name: str, role: str, description: str = ""):
        self.name = name
        self.role = role  # 导师、评审、同门
        self.description = description
        self.favorability = 50  # 好感度
        self.is_deity = False  # 是否是外神/旧日支配者
        self.is_eldritch = False  # 是否是深潜者等

    def __repr__(self):
        return f"<NPC: {self.name} ({self.role})>"
