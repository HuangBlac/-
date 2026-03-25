"""核心游戏系统"""
import random
from .character import Player, NPC, SemesterType
from .event_system import EventSystem
from .course import CourseSystem, ExamSystem
from .research import ResearchSystem
from .graduation import GraduationThesis


class GameCore:
    """游戏核心控制器"""

    def __init__(self, player_name: str):
        self.player = Player(player_name)
        self.event_system = EventSystem()
        self.game_over = False
        self.ending = None
        self.message_log = []  # 消息日志

        # 初始化各系统
        self.course_system = CourseSystem()
        self.exam_system = ExamSystem(self.course_system)
        self.research_system = ResearchSystem(self.player)
        self.graduation_thesis = GraduationThesis(self.player)

        # 初始化NPC
        self.npcs = self._init_npcs()

        # 游戏状态
        self.turn_count = 0
        self.election_opened = False  # 选课是否已开放

    def _init_npcs(self) -> dict:
        """初始化NPC"""
        return {
            "导师": NPC("黄教授", "导师", "克苏鲁研究院资深教授，研究方向：量子神话学"),
            "评审1": NPC("深海学者", "评审", "来自深潜者一族的资深评审"),
            "评审2": NPC("外星教授", "评审", "米-格星域来的访问学者"),
            "同门1": NPC("张同学", "同门", "热衷于古代文本研究的同学"),
            "同门2": NPC("李同学", "同门", "相信科学的研究生"),
        }

    def log(self, message: str):
        """添加消息到日志"""
        self.message_log.append(message)

    def start_game(self):
        """开始游戏"""
        self.log("=" * 50)
        self.log("欢迎来到克苏鲁研究院")
        self.log("=" * 50)
        self.log(f"研究生 {self.player.name}，你的学术生涯即将开始...")
        self.log(f"你的目标：在陷入疯狂之前，发表足够多的论文，顺利毕业！")
        self.log("")

    def display_status(self):
        """显示当前状态"""
        status = self.player.get_status()
        print("-" * 30)
        print(f"【当前状态】{self.player.year_name} {status['学期']} {status['周数']}")
        print(f"理智: {status['理智']}")
        print(f"行动点: {status['行动点']}")
        print(f"知识: {status['知识']} | 灵感: {status['灵感']} | 声望: {status['声望']}")
        print(f"研究方向: {status['研究方向']} | 已发表论文: {status['已发表论文']}")
        print("-" * 30)

    def display_skills(self):
        """显示技能"""
        print("【技能】")
        for skill, level in self.player.skills.items():
            print(f"  {skill}: {level}")
        print("")

    def do_action(self, action: str) -> bool:
        """执行行动

        Returns:
            是否继续游戏
        """
        # 检查行动点
        if not self.player.consume_action_point():
            self.log("本周行动点已用完！")
            self.player.advance_week()
            self.player.reset_action_points()
            self._check_game_over()
            return not self.game_over

        self.turn_count += 1
        action_result = ""

        # 根据行动执行对应功能
        if action == "1":
            if self.player.year == 1 and self.player.week_in_semester == 1 and not self.player.courses_selected:
                action_result = self._do_select_courses()
            else:
                action_result = self._do_class()
        elif action == "2":
            if self.player.year == 1 and self._is_final_week() and self.player.courses_selected:
                action_result = self._do_final_exam()
            elif self.player.year >= 2:
                # 研二及以上，检查是否有研究方向
                if not self.player.research_direction:
                    action_result = self.research_system.assign_research_direction()
                else:
                    action_result = self.research_system.read_literature()
            else:
                action_result = self._do_research()
        elif action.lower() == "e":
            # 评估Idea - 简化版：评估所有原始idea
            action_result = self._do_evaluate_idea()
            return True  # 需要继续让玩家做决定
        elif action == "3":
            if self.player.year >= 2:
                # 研二及以上，检查是否有研究方向
                if not self.player.research_direction:
                    action_result = self.research_system.assign_research_direction()
                else:
                    action_result = self._do_experiment()
            else:
                action_result = self._do_investigation()
        elif action == "4":
            if self.player.year >= 2:
                action_result = self.research_system.write_draft()
            else:
                action_result = self._do_social()
        elif action == "5":
            if self.player.year >= 2:
                action_result = self.research_system.submit_paper()
            else:
                action_result = self._do_read()
        elif action == "6":
            if self.player.year >= 3 and self.player.papers_published >= 1:
                action_result = self._do_graduation()
            else:
                action_result = self._do_investigation()
        elif action == "7":
            action_result = self._do_social()
        elif action == "8":
            action_result = self._do_graduation()
        elif action == "9":
            action_result = self._do_rest()
        elif action == "0":
            self.display_status()
            self.display_skills()
            self.log(self.research_system.get_idea_status())
            return False
        elif action == "a" or action == "A":
            # Debug: 快进一周
            self._debug_skip_week()
            return False
        elif action == "q":
            self.game_over = True
            return False
        else:
            self.log("无效选择，请重试")
            return True
        # 处理行动结果
        if action_result:
            self.log(action_result)

        # 触发随机事件
        self._trigger_random_event()

        # 检查行动点是否用完，用完则推进一周
        if self.player.action_points <= 0:
            self.player.advance_week()
            self.player.reset_action_points()
            self.log(f"--- 第{self.player.year}学年 {self.player.semester_name} 第{self.player.week_in_semester}周 ---")

        # 检查游戏结束条件
        self._check_game_over()

        return not self.game_over

    def _do_select_courses(self) -> str:
        """选课"""
        if self.player.courses_selected:
            return "你已经选过课了！"

        menu = self.course_system.get_course_selection_menu()
        self.log(menu)
        # 这里应该等待用户输入，但在do_action中我们只能返回提示
        # 实际选课逻辑需要在前端处理
        return "选课系统：\n必修课已自动选择：\n- 拉莱亚语言初步\n- 神话文本阅读\n- 形式科学导论\n\n请选择3门选修课（输入编号如：1 2 3）"

    def _do_final_exam(self) -> str:
        """期末考试"""
        if not hasattr(self, '_exam_done') or not self._exam_done:
            result = self.exam_system.hold_final_exams(self.player)
            self._exam_done = True
            # 根据选课决定研究方向
            self.player.research_direction = self.exam_system.get_research_direction_from_courses()
            self.player.courses_selected = True
            return f"【期末考试成绩】\n{result}\n\n根据你的选课，你的研究方向是：{self.player.research_direction.value}"
        return "你已完成期末考试！"

    def _do_experiment(self) -> str:
        """进行实验"""
        ideas = [i for i in self.research_system.ideas if i.status.value == "初步想法"]
        if not ideas:
            return "没有初步想法可以实验！\n请先通过阅读文献获取idea，然后评估为初步想法。"

        # 选择一个初步想法进行实验
        idea = ideas[0]
        idea_index = self.research_system.ideas.index(idea)
        return self.research_system.conduct_experiment(idea_index)

    def _do_graduation(self) -> str:
        """毕业论文"""
        if self.graduation_thesis.stage.value == "未开始":
            return "请先输入毕业论文题目。\n（当前系统需要手动输入题目）"

        return self.graduation_thesis.work_on_thesis()

    def _debug_skip_week(self):
        """Debug功能：快进一周（不改变其它数值）"""
        self.player.advance_week()
        self.log(f"[DEBUG] 时间快进：现在是第{self.player.year}学年 {self.player.semester_name} 第{self.player.week_in_semester}周")

    def _do_evaluate_idea(self) -> str:
        """评估Idea - 简化版：自动评估第一个原始idea"""
        from .research import IdeaStatus

        raw_ideas = [i for i in self.research_system.ideas if i.status == IdeaStatus.RAW]

        if not raw_ideas:
            return "没有需要评估的idea！请先阅读文献获取idea。"

        # 显示所有原始idea
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
        self.log(menu)

        return "\n请输入你的决定（如：1a）："

    def _do_class(self) -> str:
        """上课"""
        courses = ["神话学", "密码学", "神秘生物学", "量子克苏鲁学"]
        course = random.choice(courses)

        san_loss = random.randint(1, 5)
        knowledge_gain = random.randint(1, 3)
        inspiration_gain = random.randint(0, 2)

        self.player.change_sanity(-san_loss)
        self.player.add_skill(course, knowledge_gain)
        self.player.knowledge += knowledge_gain
        self.player.inspiration += inspiration_gain

        return f"你上了{course}课。\n知识+{knowledge_gain}，灵感+{inspiration_gain}，理智-{san_loss}"

    def _do_research(self) -> str:
        """进行研究"""
        progress = random.randint(3, 8)
        san_loss = random.randint(0, 3)

        self.player.research_progress += progress
        self.player.change_sanity(-san_loss)
        self.player.knowledge += 1

        result = f"你在进行研究...\n研究进度+{progress}"

        # 检查是否可以投稿
        if self.player.research_progress >= 100:
            result += "\n" + self._submit_paper()

        return result

    def _submit_paper(self) -> str:
        """投稿论文"""
        # 模拟投稿过程
        reviewers = [self.npcs["评审1"], self.npcs["评审2"]]
        reviewer = random.choice(reviewers)

        # 简单判定：声望越高，成功率越高（基础50%）
        success_rate = 0.5 + (self.player.reputation * 0.01)
        success_rate += self.player.knowledge * 0.02

        if random.random() < success_rate:
            self.player.papers_published += 1
            self.player.reputation += random.randint(5, 15)
            self.player.research_progress = 0
            return f"论文被 {reviewer.name} 接受！\n发表论文+1，声望+{self.player.reputation}"
        else:
            # 被拒稿，扣理智（减少）
            san_loss = random.randint(3, 8)
            self.player.change_sanity(-san_loss)
            return f"论文被 {reviewer.name} 拒绝！\n理智-{san_loss}，需要继续研究"

    def _do_investigation(self) -> str:
        """进行调查"""
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

    def _do_social(self) -> str:
        """社交"""
        targets = ["导师", "同门", "同门1", "同门2"]
        target = random.choice(targets)

        favor_change = random.randint(-5, 10)
        if target in self.player.relationships:
            self.player.relationships[target] = max(0, min(100,
                self.player.relationships[target] + favor_change))

        san_change = random.randint(-2, 3)

        self.player.change_sanity(san_change)

        return f"你与{target}交流了一下\n好感度变化: {favor_change:+d}，理智{san_change:+d}"

    def _do_read(self) -> str:
        """阅读禁忌文本"""
        san_loss = random.randint(10, 20)
        knowledge_gain = random.randint(3, 10)
        inspiration_gain = random.randint(5, 10)

        self.player.change_sanity(-san_loss)
        self.player.knowledge += knowledge_gain
        self.player.inspiration += inspiration_gain

        books = [
            "《克苏鲁的呼唤》手稿",
            "《阿撒托斯之书》残页",
            "《纳斯·叶格文本》复制版",
            "古代深潜者的日记",
        ]
        book = random.choice(books)

        return f"你阅读了 {book}\n知识+{knowledge_gain}，灵感+{inspiration_gain}，理智-{san_loss}"

    def _do_rest(self) -> str:
        """休息"""
        san_restore = random.randint(10, 20)
        self.player.change_sanity(san_restore)

        return f"你好好休息了一周\n理智+{san_restore}"

    def _trigger_random_event(self):
        """触发随机事件"""
        if random.random() < 0.3:  # 30%概率触发
            event = self.event_system.get_random_event()
            if event:
                self.log(f"【随机事件】{event['title']}")
                self.log(event['description'])

                # 应用效果
                if 'sanity' in event.get('effect', {}):
                    self.player.change_sanity(event['effect']['sanity'])
                if 'knowledge' in event.get('effect', {}):
                    self.player.knowledge += event['effect']['knowledge']

    def _check_game_over(self):
        """检查游戏结束条件"""
        # 理智归零
        if self.player.sanity <= 0:
            self.game_over = True
            self.ending = "疯狂"
            self.log("\n" + "=" * 50)
            self.log("你彻底失去了理智...")
            self.log("你的研究生涯在此终结")
            self.log(f"最终结局：陷入疯狂（已发表{self.player.papers_published}篇论文）")
            self.log("=" * 50)

        # 毕业论文完成
        elif self.graduation_thesis.passed:
            self.game_over = True
            self.ending = "毕业"
            self.log("\n" + "=" * 50)
            self.log("恭喜！你顺利毕业了！")
            self.log(f"最终结局：获得硕士学位（已发表{self.player.papers_published}篇论文）")
            self.log("=" * 50)

        # 超过研三
        elif self.player.year > 3:
            self.game_over = True
            if self.player.papers_published >= 1 and self.graduation_thesis.stage.value != "未开始":
                self.ending = "毕业"
                self.log("\n" + "=" * 50)
                self.log("恭喜！你顺利毕业了！")
                self.log(f"最终结局：获得硕士学位（已发表{self.player.papers_published}篇论文）")
            else:
                self.ending = "延期"
                self.log("\n" + "=" * 50)
                self.log("你未能完成学业...")
                self.log("请继续努力！")
            self.log("=" * 50)

    def get_actions(self) -> list:
        """获取可选行动"""
        actions = []

        # 研一：课程相关
        if self.player.year == 1:
            # 选课（第一周）
            if self.player.week_in_semester == 1 and not self.player.courses_selected:
                actions.append(("1", "选课", "选择本学期课程"))
            else:
                actions.append(("1", "上课", "参加课程学习"))

            # 期末考试（最后一周）
            if self._is_final_week() and self.player.courses_selected:
                actions.append(("2", "期末考试", "参加期末考试"))

        # 研二及以上：科研相关
        if self.player.year >= 2:
            actions.append(("2", "阅读文献", "获取创新idea"))
            # 如果有原始idea，显示评估选项
            raw_ideas = [i for i in self.research_system.ideas if i.status.value == "原始idea"]
            if raw_ideas:
                actions.append(("E", "评估Idea", f"评估{len(raw_ideas)}个新idea"))
            actions.append(("3", "实验验证", "进行实验获得结果"))
            actions.append(("4", "撰写论文", "攥写论文初稿"))
            actions.append(("5", "投稿", "提交论文发表"))

        # 毕业论文（研三且有小论文）
        if self.player.year >= 3 and self.player.papers_published >= 1:
            if self.graduation_thesis.stage.value == "未开始":
                actions.append(("8", "开题", "开始毕业论文"))
            else:
                actions.append(("8", "毕业论文", "继续毕业论文"))

        # 通用行动
        actions.append(("6", "调查", "参与神秘调查"))
        actions.append(("7", "社交", "与NPC交流"))
        actions.append(("9", "休息", "恢复理智"))
        actions.append(("0", "状态", "查看当前状态"))
        actions.append(("A", "快进", "[DEBUG] 时间快进一周"))
        actions.append(("q", "退出", "结束游戏"))

        return actions

    def _is_final_week(self) -> bool:
        """是否期末周"""
        semester_weeks = {SemesterType.SPRING: 18, SemesterType.SUMMER: 7,
                         SemesterType.AUTUMN: 19, SemesterType.WINTER: 5}
        return self.player.week_in_semester >= semester_weeks.get(self.player.semester, 18)
