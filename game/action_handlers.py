"""Action handler implementations."""

import json
import os
import random
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .game_engine import GameEngine


class ActionHandler(ABC):
    """Base class for action handlers."""

    def __init__(self, game: "GameEngine"):
        self.game = game

    @abstractmethod
    def handle(self, action: str) -> str:
        """Handle a player action."""
        pass

    @abstractmethod
    def get_available_actions(self) -> list:
        """Return available actions as (id, name, description)."""
        pass

    @property
    def player(self):
        return self.game.player

    @property
    def log(self):
        return self.game.log


class CourseActionHandler(ActionHandler):
    """Course-stage action handler."""

    def handle(self, action: str) -> str:
        if self._is_final_week():
            return self._do_final_exam()

        if self.player.week_in_semester == 1 and not self.player.courses_selected:
            return self._do_select_courses()

        return self._do_class()

    def get_available_actions(self) -> list:
        if self._is_final_week():
            return [("1", "期末考试", "参加期末考试")]

        if self.player.week_in_semester == 1 and not self.player.courses_selected:
            return [("1", "选课", "选择本学期课程")]

        return [("1", "上课", "参加课程学习")]

    def handle_course_selection(self, selection: str, log_func) -> str:
        """Handle follow-up input after the course menu is shown."""
        self.game.action_system.awaiting_course_selection = False

        try:
            selections = [int(x.strip()) for x in selection.split() if x.strip().isdigit()]
            if len(selections) != 3:
                log_func("请选择3门选修课！")
                self.game.action_system.awaiting_course_selection = True
                return "请输入3个编号（例如：1 2 3）"

            success = self.game.course_system.select_electives(selections)
            if success:
                self.player.courses_selected = True
                log_func("选课完成！你选择了：")
                for course in self.game.course_system.selected_electives:
                    log_func(f"  - {course.name}")
                return "选课完成！"

            log_func("选课失败，请重试！")
            self.game.action_system.awaiting_course_selection = True
            return self.game.course_system.get_course_selection_menu()

        except (ValueError, IndexError):
            log_func("输入格式错误！")
            self.game.action_system.awaiting_course_selection = True
            return "请输入3个编号（例如：1 2 3）"

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
        self.game.action_system.awaiting_course_selection = True
        return (
            "选课系统：\n"
            "必修课已自动选择：\n"
            "- 拉莱耶语初步\n"
            "- 神话文本阅读\n"
            "- 形式科学导论\n\n"
            "请选择3门选修课（输入编号，例如：1 2 3）："
        )

    def _do_class(self) -> str:
        active_courses = self.game.course_system.get_active_courses()
        if not active_courses:
            return "你已完成所有课程，可以开始科研了！"

        course = random.choice(active_courses)
        course.study_count += 1

        difficulty = self.player.EDU + course.study_count * 10
        roll = random.randint(1, 100)
        modified_attrs = []

        if roll == 1:
            bonus = random.randint(2, 4)
            for attr in ["INT", "SEN", "EDU", "STR"]:
                if attr in course.attributes:
                    setattr(self.player, attr, getattr(self.player, attr) + bonus)
                    modified_attrs.append(f"{attr}+{bonus}")
            result = f"【大成功】你对《{course.name}》有了突飞猛进的理解！"
        elif roll < difficulty:
            bonus = random.randint(1, 2)
            for attr in ["INT", "SEN", "EDU", "STR"]:
                if attr in course.attributes:
                    setattr(self.player, attr, getattr(self.player, attr) + bonus)
                    modified_attrs.append(f"{attr}+{bonus}")
            result = f"你认真学习了{course.name}课程。"
        else:
            result = f"你上了{course.name}课，但感觉收获不大。"

        if modified_attrs:
            result += "\n" + "\n".join(modified_attrs)

        san_loss = random.randint(1, 3)
        self.player.change_sanity(-san_loss)
        return result + f"\n理智-{san_loss}"

    def _do_final_exam(self) -> str:
        if not self.game.action_system.exam_done:
            result = self.game.exam_system.hold_final_exams(self.player)
            self.game.action_system.exam_done = True
            self.player.research_direction = self.game.exam_system.get_research_direction_from_courses()
            self.player.courses_selected = True
            return (
                f"【期末考试成绩】\n{result}\n\n"
                f"根据你的选课，你的研究方向是：{self.player.research_direction.value}"
            )

        return "你已经完成期末考试！"


class ResearchActionHandler(ActionHandler):
    """Research-stage action handler."""

    def handle(self, action: str) -> str:
        action = action.lower()

        if action == "2":
            if not self.player.research_direction:
                return self.game.research_system.assign_research_direction()
            return self.game.research_system.read_literature()
        if action == "3":
            return self._do_experiment()
        if action == "4":
            return self.game.research_system.write_draft()
        if action == "5":
            return self.game.research_system.submit_paper()
        if action == "e":
            return "__EVALUATE_IDEA__"

        return "无效行动"

    def get_available_actions(self) -> list:
        if not self.player.research_direction:
            return []

        actions = [("2", "阅读文献", "获取创新idea")]

        from .research import IdeaStatus

        raw_ideas = [idea for idea in self.game.research_system.ideas if idea.status == IdeaStatus.RAW]
        if raw_ideas:
            actions.append(("E", "评估Idea", f"评估{len(raw_ideas)}个新idea"))

        actions.extend([
            ("3", "实验验证", "进行实验获得结果"),
            ("4", "撰写论文", "改写论文初稿"),
            ("5", "投稿", "提交论文发表"),
        ])
        return actions

    def _do_experiment(self) -> str:
        from .research import IdeaStatus

        ideas = [idea for idea in self.game.research_system.ideas if idea.status == IdeaStatus.PRELIMINARY]
        if not ideas:
            return "没有初步想法可以实验。\n请先通过阅读文献获得idea，然后评估为初步想法。"

        idea = ideas[0]
        idea_index = self.game.research_system.ideas.index(idea)
        return self.game.research_system.conduct_experiment(idea_index)


class EntertainmentActionHandler(ActionHandler):
    """Holiday and rest action handler."""

    def handle(self, action: str) -> str:
        return self._do_holiday_activity(action)

    def get_available_actions(self) -> list:
        return [
            ("1", "旅游", "去外地旅游"),
            ("2", "回家", "回老家探亲"),
            ("3", "娱乐", "在宿舍娱乐"),
            ("4", "学习", "继续学习"),
            ("9", "休息", "好好休息"),
        ]

    def _do_holiday_activity(self, action: str) -> str:
        if self.player.advisor and self.player.advisor.personality_value >= 61:
            if random.random() < 0.3:
                return self._trigger_holiday_task()

        holiday_options = {
            "1": ("旅游", 20, 0, 0),
            "2": ("回家", 25, 0, 0),
            "3": ("娱乐", 15, 0, 0),
            "4": ("学习", 5, 10, 0),
            "9": ("休息", 18, 0, 0),
        }
        if action not in holiday_options:
            return "无效选择，请重试"

        name, sanity, progress, str_bonus = holiday_options[action]
        self.player.change_sanity(sanity)
        self.player.research_progress += progress
        if str_bonus:
            self.player.STR += str_bonus

        result = f"你{name}了几天\n理智+{sanity}"
        if progress:
            result += f"，研究进度+{progress}"
        if str_bonus:
            result += f"，STR+{str_bonus}"

        if action == "3" and random.random() < 0.4:
            extra = self._trigger_entertainment_event()
            if extra:
                result += extra

        return result

    def _trigger_entertainment_event(self) -> str:
        event_system = self.game.event_system
        if not event_system:
            return ""

        event = event_system.get_random_event("entertainment", self.player)
        if not event:
            return ""

        lines = [f"\n【随机事件】{event['title']}", event["description"]]
        event_system.apply_event_effect(self.player, event)
        followup = event_system.get_followup_event(event, self.player)
        if followup:
            lines.append(followup["description"])
            event_system.apply_event_effect(self.player, followup)
        return "\n".join(lines)

    def _trigger_holiday_task(self) -> str:
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


class InvestigationActionHandler(ActionHandler):
    """Investigation action handler."""

    def handle(self, action: str) -> str:
        return self._do_investigation()

    def get_available_actions(self) -> list:
        return [("6", "调查", "参与神秘调查")]

    def _do_investigation(self) -> str:
        # TODO: Replace temporary logic with events_investigation.json.
        san_loss = random.randint(3, 8)
        int_gain = random.randint(3, 8)
        reputation_gain = random.randint(1, 5)

        self.player.change_sanity(-san_loss)
        self.player.INT += int_gain
        self.player.reputation += reputation_gain

        events = [
            "你在图书馆发现了一本禁书",
            "你参加了校外的神秘聚会",
            "你跟踪了一个可疑的邪教成员",
            "你在实验室发现了奇怪的实验结果",
        ]
        return f"{random.choice(events)}\nINT+{int_gain}，声望+{reputation_gain}，理智-{san_loss}"


class SocialActionHandler(ActionHandler):
    """Social action handler."""

    def handle(self, action: str) -> str:
        return self._do_social()

    def get_available_actions(self) -> list:
        return [("7", "社交", "与NPC交流")]

    def _do_social(self) -> str:
        # TODO: Replace temporary logic with events_social.json.
        targets = ["导师", "同门", "同门1", "同门2"]
        target = random.choice(targets)

        favor_change = random.randint(-5, 10)
        if target in self.player.relationships:
            self.player.relationships[target] = max(0, min(100, self.player.relationships[target] + favor_change))

        san_change = random.randint(-2, 3)
        self.player.change_sanity(san_change)

        return f"你与{target}交流了一会\n好感度变化 {favor_change:+d}，理智{san_change:+d}"


class GraduationActionHandler(ActionHandler):
    """Graduation thesis action handler."""

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
            title = self._generate_thesis_title()
            return self.game.graduation_thesis.start_thesis(title)
        return self.game.graduation_thesis.work_on_thesis()

    def _generate_thesis_title(self) -> str:
        from .character import ResearchDirection

        data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "thesis_titles.json")
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
        key = direction_map.get(self.player.research_direction, "default")
        titles = data["titles"].get(key, data["titles"]["default"])
        return random.choice(titles)


class ActionHandlerFactory:
    """Factory for action handlers."""

    _handlers = {
        "course": CourseActionHandler,
        "research": ResearchActionHandler,
        "entertainment": EntertainmentActionHandler,
        "investigation": InvestigationActionHandler,
        "social": SocialActionHandler,
        "graduation": GraduationActionHandler,
    }

    @classmethod
    def create(cls, handler_type: str, game: "GameEngine") -> ActionHandler:
        handler_class = cls._handlers.get(handler_type)
        if handler_class:
            return handler_class(game)
        return None

    @classmethod
    def get_all_handlers(cls, game: "GameEngine") -> dict:
        return {key: handler(game) for key, handler in cls._handlers.items()}
