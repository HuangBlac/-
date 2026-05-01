"""游戏引擎 - 核心游戏控制器"""
import json
import os

import random

from .character import Player, NPC
from .event_system import EventSystem
from .course import CourseSystem, ExamSystem
from .research import ResearchSystem
from .graduation import GraduationThesis
from .advisor import AdvisorSystem
from .mutation_system import MutationSystem
from .game_state import GameStateManager
from .game_context import GameContext
from .event_flow_controller import EventFlowController
from .action_menu_provider import ActionMenuProvider
from .state_machine import StateMachine
from .state_action_executor import StateActionExecutor
from .turn_flow_controller import TurnFlowController
from .ui_messages import ui_text
from .states.course_phase import (
    AttendingClassesState,
    FinalExamsState,
    SelectingCoursesState,
)
from .states.graduation_phase import GraduationPhaseState
from .states.holiday_phase import HolidayPhaseState
from .states.input_states import EventChoiceState
from .states.research_phase import IdeaDecisionState, ResearchPhaseState, SubmissionTargetState
from .states.side_activity_states import InvestigationState, SocialState


class GameEngine:
    """游戏核心引擎"""

    def __init__(self, player_name: str):
        # 加载配置
        self.config = self._load_config()
        self.debug_mode = self.config.get("debug", {}).get("enabled", False)

        # 玩家
        self.player = Player(player_name)

        # 消息日志
        self.message_log = []

        # 事件系统
        self.event_system = EventSystem()

        # 初始化各子系统（异变系统先创建，供科研系统使用）
        self.mutation_system = MutationSystem()
        self.course_system = CourseSystem()
        self.exam_system = ExamSystem(self.course_system)
        self.research_system = ResearchSystem(self.player, self.mutation_system)
        self.graduation_thesis = GraduationThesis(self.player)
        self.advisor_system = AdvisorSystem()
        self.event_flow = EventFlowController(self)

        # NPCs are kept as data for later social-system redesign.
        self.npcs = self._init_npcs()

        # 游戏状态管理
        self.game_state = GameStateManager()

        # 状态机（先迁移课程阶段；科研/假期/事件仍走旧路由）
        self.game_context = GameContext(
            player=self.player,
            course_system=self.course_system,
            exam_system=self.exam_system,
            research_system=self.research_system,
            event_system=self.event_system,
            mutation_system=self.mutation_system,
            graduation_thesis=self.graduation_thesis,
            advisor_system=self.advisor_system,
            game_state=self.game_state,
            log_func=self.log,
            trigger_event=self.trigger_event,
            apply_event_result=self._apply_event_result,
        )
        self.event_choice_state = EventChoiceState()
        self.graduation_state = GraduationPhaseState()
        self.state_machine = StateMachine(
            initial_state=AttendingClassesState(),
            context=self.game_context,
            states={
                "course.selecting_courses": SelectingCoursesState(),
                "course.final_exams": FinalExamsState(),
                "graduation.phase": self.graduation_state,
                "input.event_choice": self.event_choice_state,
                "side.investigation": InvestigationState(),
                "side.social": SocialState(),
                "holiday.phase": HolidayPhaseState(),
                "research.phase": ResearchPhaseState(),
                "research.idea_decision": IdeaDecisionState(),
                "research.submission_target": SubmissionTargetState(),
            },
        )
        self.state_actions = StateActionExecutor(self)
        self.turn_flow = TurnFlowController(self)
        self.action_menu = ActionMenuProvider(self)

        # 游戏状态
        self.turn_count = 0

    def _init_npcs(self) -> dict:
        """初始化NPC"""
        return {
            "导师": NPC("黄教授", "导师", "克苏鲁研究院资深教授，研究方向：量子神话学"),
            "评审1": NPC("深海学者", "评审", "来自深潜者一族的资深评审"),
            "评审2": NPC("外星教授", "评审", "米-格星域来的访问学者"),
            "同门1": NPC("张同学", "同门", "热衷于古代文本研究的同学"),
            "同门2": NPC("李同学", "同门", "相信科学的研究生"),
        }

    def _load_config(self) -> dict:
        """加载游戏配置"""
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'config.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"debug": {"enabled": False}}

    # ========== 日志系统 ==========
    def log(self, message: str):
        """添加消息到日志（可能受异变影响）"""
        if self.player.mutation > 0 and random.random() < self.player.mutation * 0.3:
            message = self.mutation_system.corrupt_text(message, self.player.mutation)
        self.message_log.append(message)

    # ========== 游戏生命周期 ==========
    def start_game(self):
        """开始游戏"""
        self.log("=" * 50)
        self.log("欢迎来到克苏鲁研究院")
        self.log("=" * 50)
        self.log(f"研究生 {self.player.name}，你的学术生涯即将开始...")
        self.log(f"你的目标：在陷入疯狂之前，发表足够多的论文，顺利毕业！")

        # 分配导师
        self._assign_advisor()

    def _assign_advisor(self):
        """分配导师"""
        advisor = self.advisor_system.assign_advisor()
        self.player.advisor = advisor
        self.player.advisor_assigned = True
        self.player.graduation_required_papers = advisor.graduation_requirement

        self.log("")
        self.log("=" * 50)
        self.log("【导师分配】")
        self.log(advisor.get_description())
        self.log("")
        self.log(self.advisor_system.get_graduation_requirement_text())
        self.log("=" * 50)

    # ========== 状态显示 ==========
    def get_status_lines(self) -> list[str]:
        """Return the current status as player-facing text lines."""
        status = self.player.get_status()
        lines = [
            "-" * 30,
            f"【当前状态】{self.player.year_name} {status['学期']} {status['周数']}",
            f"理智: {status['理智']}",
            f"行动点: {status['行动点']}",
            f"INT: {status['INT直觉']} | SEN: {status['SEN感知']} | EDU: {status['EDU知识']}",
            f"STR: {status['STR耐力']} | SOC: {status['SOC社交']}",
            f"声望: {status['声望']} | 研究方向: {status['研究方向']}",
            f"已发表论文: {status['已发表论文']} | 毕业要求: {status['毕业要求']}",
        ]
        if "导师" in status:
            lines.append(f"导师: {status['导师']} | 能力: {status['导师能力']} | 性格: {status['导师性格']}")
        lines.append("-" * 30)
        return [
            self.mutation_system.get_corrupted_status_text(line, self.player.mutation)
            for line in lines
        ]

    def display_status(self):
        """Compatibility wrapper that returns status lines instead of printing."""
        return self.get_status_lines()

    # ========== 行动执行 ==========
    def do_action(self, action: str) -> bool:
        """执行行动

        Returns:
            是否继续游戏
        """
        if self.state_actions.is_course_selection_input_state():
            return self.state_actions.do_course_state_action(action, costs_action_point=False)

        if self.state_actions.is_temporary_input_state():
            return self.state_actions.do_temporary_input_action(action)

        # 退出
        if action == "q":
            self.game_state.game_over = True
            return False

        # 查看状态
        if action == "0":
            for line in self.get_status_lines():
                self.log(line)
            self.log(self.research_system.get_idea_status())
            return False

        if self.state_actions.is_graduation_state_action(action):
            return self.state_actions.do_graduation_state_action(action)

        if self.state_actions.uses_research_state_machine() and self.state_actions.is_research_state_action(action):
            return self.state_actions.do_research_state_action(action)

        if self.state_actions.uses_holiday_state_machine() and self.state_actions.is_holiday_state_action(action):
            return self.state_actions.do_holiday_state_action(action)

        if self.state_actions.is_side_activity_action(action):
            return self.state_actions.do_side_activity_action(action)

        if self.state_actions.uses_course_state_machine():
            return self.state_actions.do_course_state_action(action, costs_action_point=True)

        if not self._is_valid_action(action):
            self.log(ui_text("invalid_action"))
            return True

        if not self._consume_action_for_state_action():
            return not self.game_state.is_ended()

        return self._continue_turn("after_action")

    def _is_valid_action(self, action: str) -> bool:
        """Return whether the input matches any currently available action id."""
        normalized = action.strip().lower()
        if not normalized:
            return False
        valid_ids = {str(action_id).strip().lower() for action_id, _, _ in self.get_actions()}
        return normalized in valid_ids

    def _consume_action_for_state_action(self) -> bool:
        """Compatibility wrapper for the extracted turn-flow controller."""
        return self.turn_flow.consume_action_for_state_action()

    def _check_continue_work(self) -> bool:
        """Compatibility wrapper for the extracted turn-flow controller."""
        return self.turn_flow.check_continue_work()

    def _advance_week(self, skip_pressure: bool = False) -> bool:
        """Compatibility wrapper for the extracted turn-flow controller."""
        return self.turn_flow.advance_week(skip_pressure=skip_pressure)

    def _trigger_random_event(self):
        """Compatibility wrapper for the extracted turn-flow controller."""
        return self.turn_flow.trigger_random_event()

    def _trigger_inspiration_burst(self):
        """Compatibility wrapper for the extracted turn-flow controller."""
        return self.turn_flow.trigger_inspiration_burst()

    def trigger_event(self, event: dict, label: str, next_stage: str = "after_action", post_apply=None) -> str:
        """Compatibility wrapper for the extracted event-flow controller."""
        return self.event_flow.trigger_event(event, label, next_stage=next_stage, post_apply=post_apply)

    def _queue_event_choice(self, event: dict, label: str, next_stage: str, post_apply=None) -> str:
        """Compatibility wrapper for the extracted event-flow controller."""
        return self.event_flow.queue_event_choice(event, label, next_stage, post_apply=post_apply)

    def _apply_event_result(self, event: dict, label: str, choice_id: str = None, post_apply=None) -> str:
        """Compatibility wrapper for the extracted event-flow controller."""
        return self.event_flow.apply_event_result(
            event,
            label,
            choice_id=choice_id,
            post_apply=post_apply,
        )

    def _continue_turn(self, stage: str) -> bool:
        """Compatibility wrapper for the extracted turn-flow controller."""
        return self.turn_flow.continue_turn(stage)

    # ========== 公开接口 ==========
    @property
    def game_over(self) -> bool:
        return self.game_state.is_ended()

    def get_actions(self) -> list:
        """Compatibility wrapper for the extracted action-menu provider."""
        return self.action_menu.get_actions()


# 兼容性别名
GameCore = GameEngine
