"""游戏引擎 - 核心游戏控制器"""
import random
import json
import os

from .character import Player, NPC, SemesterType
from .event_system import EventSystem
from .course import CourseSystem, ExamSystem
from .research import ResearchSystem
from .graduation import GraduationThesis
from .advisor import AdvisorSystem
from .action_system import ActionSystem
from .mutation_system import MutationSystem
from .game_state import GameStateManager


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

        # 行动系统
        self.action_system = ActionSystem(
            self,
            self.player,
            self.course_system,
            self.research_system,
            self.graduation_thesis,
            self._init_npcs()
        )

        # 游戏状态管理
        self.game_state = GameStateManager()

        # 游戏状态
        self.turn_count = 0
        self.awaiting_idea_decision = False  # 是否正在等待idea评估决定
        self.awaiting_event_choice = False  # 是否正在等待事件选择

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
    def display_status(self):
        """显示当前状态（受异变影响）"""
        status = self.player.get_status()

        def p(text):
            """打印经过异变处理的文本"""
            text = self.mutation_system.get_corrupted_status_text(text, self.player.mutation)
            print(text)

        p("-" * 30)
        p(f"【当前状态】{self.player.year_name} {status['学期']} {status['周数']}")
        p(f"理智: {status['理智']}")
        p(f"行动点: {status['行动点']}")
        p(f"INT: {status['INT直觉']} | SEN: {status['SEN感知']} | EDU: {status['EDU知识']}")
        p(f"STR: {status['STR耐力']} | SOC: {status['SOC社交']}")
        p(f"声望: {status['声望']} | 研究方向: {status['研究方向']}")
        p(f"已发表论文: {status['已发表论文']} | 毕业要求: {status['毕业要求']}")
        if '导师' in status:
            p(f"导师: {status['导师']} | 能力: {status['导师能力']} | 性格: {status['导师性格']}")
        p("-" * 30)

    # ========== 行动执行 ==========
    def do_action(self, action: str) -> bool:
        """执行行动

        Returns:
            是否继续游戏
        """
        # 子系统等待输入时，不消耗行动点，也不推进随机事件。
        if self.action_system.awaiting_course_selection:
            action_result, _ = self.action_system.do_action(action, self.log)
            if action_result:
                self.log(action_result)
            return not self.game_state.is_ended()

        # 如果正在等待idea评估决定，先处理决定
        if self.awaiting_idea_decision:
            self.awaiting_idea_decision = False
            return self._handle_idea_decision(action)

        # 退出
        if action == "q":
            self.game_state.game_over = True
            return False

        # 查看状态
        if action == "0":
            self.display_status()
            self.log(self.research_system.get_idea_status())
            return False

        # 消耗行动点
        if not self.player.consume_action_point():
            if self._check_continue_work():
                self.player.action_points += 1
                self.player.consume_action_point()
            else:
                self.log("本周行动点已用完！")
                self._advance_week()
                return not self.game_state.is_ended()

        self.turn_count += 1

        # 处理评估Idea的特殊情况
        if action.lower() == "e":
            self.awaiting_idea_decision = True
            action_result = self._do_evaluate_idea()
            if action_result:
                self.log(action_result)
            return True

        # 执行行动
        action_result, _ = self.action_system.do_action(action, self.log)
        if action_result:
            # 评估Idea需要玩家输入
            if action_result == "__EVALUATE_IDEA__":
                self.awaiting_idea_decision = True
                return True
            self.log(action_result)

        # 触发随机事件
        self._trigger_random_event()

        # 回合末检查灵感爆发。随机事件、假期活动等只负责积累灵感，爆发由引擎统一结算。
        self._trigger_inspiration_burst()

        # 应用异变效果
        self.mutation_system.apply_mutation_effect(self.player, self.log)

        # 检查行动点是否用完
        if self.player.action_points <= 0:
            self._advance_week()

        # 检查游戏结束
        self.game_state.check_game_over(self.player, self.graduation_thesis, self.log)

        return not self.game_state.is_ended()

    def _check_continue_work(self) -> bool:
        """检查STR继续工作

        Returns:
            是否触发了继续工作
        """
        if self.player.STR > 70 and self.player.continue_action_count < self.player.max_continue_actions:
            trigger_chance = (self.player.STR - 70) / 2
            if random.random() * 100 < trigger_chance:
                self.player.continue_action_count += 1
                self.log("【STR继续工作】你感觉自己还有精力，可以再做一件事！")
                return True
        return False

    def _advance_week(self):
        """推进一周"""
        self.player.advance_week()
        self.player.reset_action_points()
        self.log(f"--- 第{self.player.year}学年 {self.player.semester_name} 第{self.player.week_in_semester}周 ---")

    def _trigger_random_event(self):
        """触发随机事件"""
        is_holiday = self.player.semester in (SemesterType.SUMMER, SemesterType.WINTER)

        if random.random() < 0.3:
            event = self.event_system.get_random_event('random', self.player)
            if event:
                self.log(f"【随机事件】{event['title']}")
                self.log(event['description'])
                self.event_system.apply_event_effect(self.player, event)
                followup = self.event_system.get_followup_event(event, self.player)
                if followup:
                    self.log(followup['description'])
                    self.event_system.apply_event_effect(self.player, followup)

    def _trigger_inspiration_burst(self):
        """回合末结算灵感爆发机制。"""
        if self.player.research_progress < 100:
            return

        if not self.player.research_direction:
            return

        idea_result, triggered = self.research_system.generate_inspiration_idea()
        if not triggered:
            self.log(idea_result)
            return

        progress_loss = random.randint(1, 100)
        sanity_loss = random.randint(3, 8)
        self.player.research_progress = max(0, self.player.research_progress - progress_loss)
        self.player.change_sanity(-sanity_loss)

        self.log("【灵感爆发】你仿佛从那梦境的都市取得了最璀璨的宝石，但是你是从何而来的，你陷入了困惑……")
        self.log(f"理智-{sanity_loss}")
        self.log(idea_result)

    def _do_evaluate_idea(self) -> str:
        """评估Idea"""
        from .research import IdeaStatus

        raw_ideas = [i for i in self.research_system.ideas if i.status == IdeaStatus.RAW]

        if not raw_ideas:
            return "没有需要评估的idea！请先阅读文献获取idea。"

        menu = "\n【待评估的Idea】\n"
        for idx, idea in enumerate(raw_ideas):
            menu += f"{idx + 1}. {idea.name}\n"
            menu += f"   描述: {idea.description}\n"
            menu += f"   创新值: {idea.innovation}/10\n"
            menu += f"   方向: {idea.direction.value}\n\n"

        menu += "你可以选择:\n"
        menu += "  a - 接受第1个idea为初步想法\n"
        menu += "  d - 丢弃第1个idea（增加能力值）\n"
        menu += "  i - 第1个idea有待改进（继续研究）\n"
        menu += "  2a/2d/2i - 评估第2个idea，以此类推\n"
        return menu + "\n请输入你的决定（如：1a）："

    def _handle_idea_decision(self, decision: str) -> bool:
        """处理idea评估决定"""
        from .research import IdeaStatus

        raw_ideas = [i for i in self.research_system.ideas if i.status == IdeaStatus.RAW]

        if not raw_ideas:
            self.log("没有需要评估的idea！")
            return True

        decision = decision.strip().lower()

        if len(decision) < 2:
            self.log("无效输入！格式如：1a（评估第1个idea，接受为初步想法）")
            self.log("a=接受，d=丢弃，i=改进")
            self.awaiting_idea_decision = True
            return True

        try:
            index = int(decision[:-1]) - 1
            action = decision[-1]

            if index < 0 or index >= len(raw_ideas):
                self.log(f"无效序号！有效范围：1-{len(raw_ideas)}")
                self.awaiting_idea_decision = True
                return True

            idea = raw_ideas[index]

            if action == "a":
                result = self.research_system.evaluate_idea(self.research_system.ideas.index(idea), "accept")
            elif action == "d":
                result = self.research_system.evaluate_idea(self.research_system.ideas.index(idea), "discard")
            elif action == "i":
                result = self.research_system.evaluate_idea(self.research_system.ideas.index(idea), "improve")
            else:
                self.log("无效决定！a=接受，d=丢弃，i=改进")
                self.awaiting_idea_decision = True
                return True

            self.log(result)
            return True

        except (ValueError, IndexError):
            self.log("无效输入！格式如：1a（评估第1个idea）")
            self.log("a=接受，d=丢弃，i=改进")
            self.awaiting_idea_decision = True
            return True

    # ========== 公开接口 ==========
    @property
    def game_over(self) -> bool:
        return self.game_state.is_ended()

    def get_actions(self) -> list:
        """获取可选行动"""
        actions = self.action_system.get_actions()

        actions.append(("q", "退出", "结束游戏"))
        return actions


# 兼容性别名
GameCore = GameEngine
