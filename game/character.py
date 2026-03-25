"""角色系统"""
from enum import Enum
from typing import Optional


class SemesterType(Enum):
    """学期类型"""
    SPRING = "上学期"      # 18周
    SUMMER = "暑假"        # 7周
    AUTUMN = "下学期"      # 19周
    WINTER = "寒假"        # 5周


class ResearchDirection(Enum):
    """研究方向"""
    ARCANE_ANALYSIS = "法术与超自然科技分析"      # 形式科学建模分析
    MYTHOS_RITUAL = "神话文本与仪式构造"          # 钻研典籍
    DEITY_RACE = "神明附属种族与独立种族"          # 田野调查
    OUTER_GOD = "旧日支配者与外神"                 # 理论研究


# 每年各学期的周数
SEMESTER_WEEKS = {
    SemesterType.SPRING: 18,
    SemesterType.SUMMER: 7,
    SemesterType.AUTUMN: 19,
    SemesterType.WINTER: 5,
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

        # 核心数值
        self.sanity = 100  # 理智 (SAN)
        self.knowledge = 10  # 知识值
        self.inspiration = 10  # 灵感
        self.reputation = 0  # 学术声望

        # 选课相关
        self.courses_selected = False  # 是否已选课
        self.required_courses = []  # 必修课
        self.elective_courses = []  # 选修课
        self.research_direction: Optional[ResearchDirection] = None  # 研究方向

        # 研究相关
        self.research_progress = 0  # 研究进度 0-100
        self.current_paper = None  # 当前论文
        self.papers_published = 0  # 已发表论文数

        # 技能
        self.skills = {
            "神话学": 0,
            "密码学": 0,
            "神秘生物学": 0,
            "量子克苏鲁学": 0,
            "田野调查": 0,
            "说服": 0,
            "拉莱亚语言": 0,  # 研一新增
            "文本解读": 0,     # 研一新增
            "形式科学": 0,     # 研一新增
        }

        # 人际关系
        self.relationships = {
            "导师": 50,
            "同门": 50,
            "评审": 50,
        }

        # 状态
        self.status = []  # 当前状态（如：疯狂、神志清醒）

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
        action_map = {1: 3, 2: 4, 3: 5}
        return action_map.get(self.year, 3)

    def consume_action_point(self) -> bool:
        """消耗一次行动点，返回是否成功（行动点不足返回False）"""
        if self.action_points > 0:
            self.action_points -= 1
            return True
        return False

    def change_sanity(self, amount: int):
        """改变理智值"""
        self.sanity = max(0, min(100, self.sanity + amount))

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
        return {
            "姓名": self.name,
            "年级": self.year_name,
            "学期": self.semester_name,
            "周数": f"第{self.week_in_semester}周",
            "行动点": f"{self.action_points}/{self.max_action_points}",
            "年龄": f"{self.age}岁",
            "理智": f"{self.sanity}/100 ({self.sanity_level})",
            "知识": self.knowledge,
            "灵感": self.inspiration,
            "声望": self.reputation,
            "研究方向": self.research_direction.value if self.research_direction else "未选择",
            "已发表论文": self.papers_published,
        }

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
