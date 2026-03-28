"""行动处理器基类和工厂"""
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .game_engine import GameEngine


class ActionHandler(ABC):
    """行动处理器基类"""

    def __init__(self, game: 'GameEngine'):
        self.game = game

    @abstractmethod
    def handle(self, action: str) -> str:
        """处理行动

        Args:
            action: 行动代码

        Returns:
            行动结果描述
        """
        pass

    @abstractmethod
    def get_available_actions(self) -> list:
        """获取当前可用的行动列表

        Returns:
            [(action_id, action_name, description), ...]
        """
        pass

    @property
    def player(self):
        return self.game.player

    @property
    def log(self):
        return self.game.log


class CourseActionHandler(ActionHandler):
    """课程行动处理器"""

    def handle(self, action: str) -> str:
        """处理课程相关行动"""
        from .character import SemesterType

        is_holiday = self.player.semester in (SemesterType.SUMMER, SemesterType.WINTER)

        # 期末周：强制期末考试
        if self._is_final_week():
            return self._do_final_exam()

        if is_holiday:
            return self._do_holiday_rest()

        if self.player.week_in_semester == 1 and not self.player.courses_selected:
            return self._do_select_courses()
        else:
            return self._do_class()

    def get_available_actions(self) -> list:
        from .character import SemesterType
        from .course import CourseSystem

        actions = []
        is_holiday = self.player.semester in (SemesterType.SUMMER, SemesterType.WINTER)
        course_system: CourseSystem = self.game.course_system

        # 期末周：只有期末考试
        if self._is_final_week():
            return [("1", "期末考试", "参加期末考试")]

        if not is_holiday:
            if self.player.week_in_semester == 1 and not self.player.courses_selected:
                actions.append(("1", "选课", "选择本学期课程"))
            else:
                actions.append(("1", "上课", "参加课程学习"))
        else:
            actions.append(("1", "假期休息", "享受假期时光"))

        return actions

    def _is_final_week(self) -> bool:
        from .character import SEMESTER_WEEKS
        total_weeks = SEMESTER_WEEKS.get(self.player.semester, 8)
        exam_week = max(1, total_weeks - 1)
        return self.player.week_in_semester >= exam_week

    def _do_select_courses(self) -> str:
        if self.player.courses_selected:
            return "你已经选过课了！"

        menu = self.game.course_system.get_course_selection_menu()
        self.log(menu)
        return "选课系统：\n必修课已自动选择：\n- 拉莱亚语言初步\n- 神话文本阅读\n- 形式科学导论\n\n请选择3门选修课（输入编号如：1 2 3）"

    def _do_class(self) -> str:
        """上课"""
        import random

        active_courses = self.game.course_system.get_active_courses()

        if not active_courses:
            return "你已完成所有课程，可以开始科研了！"

        course = random.choice(active_courses)
        course.study_count += 1

        difficulty = self.player.EDU + course.study_count * 10
        roll = random.randint(1, 100)

        if roll == 1:
            bonus = random.randint(2, 4)
            for attr in ["INT", "SEN", "EDU", "STR"]:
                if attr in course.attributes:
                    current = getattr(self.player, attr)
                    setattr(self.player, attr, current + bonus)
            result = f"【大成功】你对{course.name}有了突飞猛进的理解！\n{attr}+{bonus}"
        elif roll < difficulty:
            bonus = random.randint(1, 2)
            for attr in ["INT", "SEN", "EDU", "STR"]:
                if attr in course.attributes:
                    current = getattr(self.player, attr)
                    setattr(self.player, attr, current + bonus)
            result = f"你认真学习了{course.name}课。\n{attr}+{bonus}"
        else:
            result = f"你上了{course.name}课，但感觉收获不大。"

        san_loss = random.randint(1, 3)
        self.player.change_sanity(-san_loss)
        result += f"\n理智-{san_loss}"

        return result

    def _do_final_exam(self) -> str:
        """期末考试"""
        if not hasattr(self.game.action_system, '_exam_done'):
            self.game.action_system._exam_done = False

        if not self.game.action_system._exam_done:
            result = self.game.exam_system.hold_final_exams(self.player)
            self.game.action_system._exam_done = True
            self.player.research_direction = self.game.exam_system.get_research_direction_from_courses()
            self.player.courses_selected = True
            return f"【期末考试成绩】\n{result}\n\n根据你的选课，你的研究方向是：{self.player.research_direction.value}"
        return "你已完成期末考试！"

    def _do_holiday_rest(self) -> str:
        """假期休息"""
        from .character import SemesterType
        is_summer = self.player.semester == SemesterType.SUMMER

        actions = []

        # 假期行动
        actions.append(("1", "旅游", "去外地旅游放松"))
        actions.append(("2", "回家", "回老家探亲"))
        actions.append(("3", "娱乐", "在宿舍娱乐"))
        actions.append(("4", "学习", "继续学习"))

        # 高压导师可能触发任务
        if self.player.advisor and self.player.advisor.personality_value >= 61:
            if random.random() < 0.3:
                self.log("【警告】假期期间，导师给你安排了任务！")
                return self._trigger_advisor_holiday_task()

        # 显示菜单让玩家选择
        menu = "\n【假期活动】\n"
        for a in actions:
            menu += f"{a[0]}. {a[1]}\n"
        menu += "\n请选择: "

        # 这里暂时返回菜单，实际选择需要在前端处理
        return menu + "\n(当前系统需要输入数字选择)"

    def _trigger_advisor_holiday_task(self) -> str:
        """触发导师假期任务"""
        import random

        holiday_tasks = [
            ("导师让你假期来取快递", -3, 5),
            ("导师要求你假期远程协助实验", -8, 10),
            ("导师安排你假期写报告", -10, 15),
        ]

        task, san_loss, progress = random.choice(holiday_tasks)
        self.player.change_sanity(san_loss)
        self.player.research_progress += progress

        return f"{task}\n理智{san_loss:+d}，研究进度+{progress}"


class ResearchActionHandler(ActionHandler):
    """科研行动处理器"""

    def handle(self, action: str) -> str:
        """处理科研相关行动"""
        action = action.lower()

        if action == "2":
            if not self.player.research_direction:
                return self.game.research_system.assign_research_direction()
            return self.game.research_system.read_literature()
        elif action == "3":
            return self._do_experiment()
        elif action == "4":
            return self.game.research_system.write_draft()
        elif action == "5":
            return self.game.research_system.submit_paper()
        elif action.lower() == "e":
            return "__EVALUATE_IDEA__"

        return "无效行动"

    def get_available_actions(self) -> list:
        actions = []

        # 需要有研究方向才能科研
        if not self.player.research_direction:
            return []

        actions.append(("2", "阅读文献", "获取创新idea"))

        from .research import IdeaStatus
        raw_ideas = [i for i in self.game.research_system.ideas if i.status == IdeaStatus.RAW]
        if raw_ideas:
            actions.append(("E", "评估Idea", f"评估{len(raw_ideas)}个新idea"))

        actions.append(("3", "实验验证", "进行实验获得结果"))
        actions.append(("4", "撰写论文", "攥写论文初稿"))
        actions.append(("5", "投稿", "提交论文发表"))

        return actions

    def _do_experiment(self) -> str:
        ideas = [i for i in self.game.research_system.ideas if i.status.value == "初步想法"]
        if not ideas:
            return "没有初步想法可以实验！\n请先通过阅读文献获取idea，然后评估为初步想法。"

        idea = ideas[0]
        idea_index = self.game.research_system.ideas.index(idea)
        return self.game.research_system.conduct_experiment(idea_index)


class EntertainmentActionHandler(ActionHandler):
    """娱乐行动处理器"""

    def handle(self, action: str) -> str:
        """处理娱乐/休息行动"""
        return self._do_entertainment(action)

    def get_available_actions(self) -> list:
        return [
            ("1", "听歌", "听音乐放松"),
            ("2", "游戏", "打游戏消遣"),
            ("3", "运动", "打篮球/跑步"),
            ("4", "电影", "看电影"),
            ("5", "社交", "和朋友聊天"),
            ("9", "休息", "好好休息"),
        ]

    def _do_entertainment(self, action: str) -> str:
        """执行娱乐活动"""
        import random
        from .character import SemesterType

        is_holiday = self.player.semester in (SemesterType.SUMMER, SemesterType.WINTER)

        # 检查高压导师假期任务
        if is_holiday and self.player.advisor and self.player.advisor.personality_value >= 61:
            if random.random() < 0.3:
                return self._trigger_holiday_task()

        # 娱乐活动
        entertainment_options = {
            "1": ("听音乐", 8, 0, 0),
            "2": ("玩游戏", 10, -5, 0),
            "3": ("打篮球", 12, 0, 1),
            "4": ("看电影", 10, 0, 0),
            "5": ("社交", 6, 0, 0),
            "9": ("睡觉", 15, 0, 0),
        }

        if action not in entertainment_options:
            return "无效选择"

        name, san, progress, str_bonus = entertainment_options[action]

        self.player.change_sanity(san)
        self.player.research_progress += progress
        if str_bonus:
            self.player.STR += str_bonus

        return f"你{name}了{random.choice(['一会儿', '一下午', '一晚上'])}\n理智+{san}" + \
               (f"，STR+{str_bonus}" if str_bonus else "") + \
               (f"，研究进度{progress:+d}" if progress else "")

    def _trigger_holiday_task(self) -> str:
        """触发假期导师任务"""
        import random

        tasks = [
            "导师在假期给你安排了任务",
            "导师要求你参加线上组会",
            "导师说有急事需要处理",
        ]

        task = random.choice(tasks)
        san_loss = random.randint(10, 15)
        progress = random.randint(5, 15)

        self.player.change_sanity(-san_loss)
        self.player.research_progress += progress

        return f"【{task}】\n理智-{san_loss}，研究进度+{progress}\n这个假期没法好好休息了..."


class SocialActionHandler(ActionHandler):
    """社交行动处理器"""

    def handle(self, action: str) -> str:
        return self._do_social()

    def get_available_actions(self) -> list:
        return [
            ("6", "调查", "参与神秘调查"),
            ("7", "社交", "与NPC交流"),
        ]

    def _do_social(self) -> str:
        """社交"""
        import random

        targets = ["导师", "同门", "同门1", "同门2"]
        target = random.choice(targets)

        favor_change = random.randint(-5, 10)
        if target in self.player.relationships:
            self.player.relationships[target] = max(0, min(100,
                self.player.relationships[target] + favor_change))

        san_change = random.randint(-2, 3)
        self.player.change_sanity(san_change)

        return f"你与{target}交流了一下\n好感度变化: {favor_change:+d}，理智{san_change:+d}"

    def _do_investigation(self) -> str:
        """调查"""
        import random

        san_loss = random.randint(3, 8)
        inspiration_gain = random.randint(3, 8)
        reputation_gain = random.randint(1, 5)

        self.player.change_sanity(-san_loss)
        self.player.inspiration += inspiration_gain
        self.player.reputation += reputation_gain

        events = [
            "你在图书馆发现了一本禁书",
            "你参加了校外的神秘聚会",
            "你跟踪了一个可疑的邪教成员",
            "你在实验室发现了奇怪的实验结果",
        ]
        event_desc = random.choice(events)

        return f"{event_desc}\n灵感+{inspiration_gain}，声望+{reputation_gain}，理智-{san_loss}"


class GraduationActionHandler(ActionHandler):
    """毕业行动处理器"""

    def handle(self, action: str) -> str:
        return self._do_graduation()

    def get_available_actions(self) -> list:
        if self.player.year >= 3 and self.player.papers_published >= 1:
            if self.game.graduation_thesis.stage.value == "未开始":
                return [("8", "开题", "开始毕业论文")]
            return [("8", "毕业论文", "继续毕业论文")]
        return []

    def _do_graduation(self) -> str:
        if self.game.graduation_thesis.stage.value == "未开始":
            return "请先输入毕业论文题目。\n（当前系统需要手动输入题目）"
        return self.game.graduation_thesis.work_on_thesis()


# 行动处理器工厂
class ActionHandlerFactory:
    """行动处理器工厂"""

    _handlers = {
        "course": CourseActionHandler,
        "research": ResearchActionHandler,
        "entertainment": EntertainmentActionHandler,
        "social": SocialActionHandler,
        "graduation": GraduationActionHandler,
    }

    @classmethod
    def create(cls, handler_type: str, game: 'GameEngine') -> ActionHandler:
        """创建行动处理器"""
        handler_class = cls._handlers.get(handler_type)
        if handler_class:
            return handler_class(game)
        return None

    @classmethod
    def get_all_handlers(cls, game: 'GameEngine') -> dict:
        """获取所有行动处理器"""
        return {k: v(game) for k, v in cls._handlers.items()}
