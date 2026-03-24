"""角色系统"""


class Player:
    """玩家角色"""

    def __init__(self, name: str):
        self.name = name
        self.year = 1  # 研几
        self.week = 1  # 第几周
        self.age = 22  # 年龄

        # 核心数值
        self.sanity = 100  # 理智 (SAN)
        self.knowledge = 10  # 知识值
        self.inspiration = 10  # 灵感
        self.reputation = 0  # 学术声望

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

    def change_sanity(self, amount: int):
        """改变理智值"""
        self.sanity = max(0, min(100, self.sanity + amount))

    def add_skill(self, skill_name: str, amount: int = 1):
        """增加技能经验"""
        if skill_name in self.skills:
            self.skills[skill_name] += amount

    def advance_week(self):
        """推进一周"""
        self.week += 1
        if self.week > 16:  # 每学年16周
            self.week = 1
            self.year += 1
            self.age += 1

    def get_status(self) -> dict:
        """获取当前状态"""
        return {
            "姓名": self.name,
            "年级": self.year_name,
            "周数": f"第{self.week}周",
            "年龄": f"{self.age}岁",
            "理智": f"{self.sanity}/100 ({self.sanity_level})",
            "知识": self.knowledge,
            "灵感": self.inspiration,
            "声望": self.reputation,
            "研究进度": f"{self.research_progress}%",
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
