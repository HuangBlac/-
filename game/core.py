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
        self.awaiting_idea_decision = False  # 是否正在等待idea评估决定

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
        """添加消息到日志（可能受异变影响）"""
        # 根据异变值可能污染文本
        if self.player.mutation > 0 and random.random() < self.player.mutation * 0.3:
            message = self._corrupt_text(message)
        self.message_log.append(message)

    def _corrupt_text(self, text: str) -> str:
        """根据异变程度污染文本 - 用#=%等符号替换数字"""
        # 数字替换表
        digit_map = {
            '0': '〇', '1': '一', '2': '二', '3': '三', '4': '四',
            '5': '五', '6': '六', '7': '七', '8': '八', '9': '九'
        }

        # 严重时用特殊符号
        if self.player.mutation >= 1:
            digit_map = {
                '0': '☆', '1': '★', '2': '◇', '3': '◆', '4': '○',
                '5': '●', '6': '△', '7': '▲', '8': '□', '9': '■'
            }

        result = text
        for old, new in digit_map.items():
            if random.random() < self.player.mutation * 0.2:  # 概率替换
                result = result.replace(old, new)

        # 严重异变时插入不可名状的符号
        if self.player.mutation >= 0.5 and random.random() < self.player.mutation * 0.3:
            symbols = ["#@%", "&&&", "***", "???", "-%!%!", "~~~"]
            insert_pos = random.randint(0, len(result))
            result = result[:insert_pos] + random.choice(symbols) + result[insert_pos:]

        return result

    def start_game(self):
        """开始游戏"""
        self.log("=" * 50)
        self.log("欢迎来到克苏鲁研究院")
        self.log("=" * 50)
        self.log(f"研究生 {self.player.name}，你的学术生涯即将开始...")
        self.log(f"你的目标：在陷入疯狂之前，发表足够多的论文，顺利毕业！")
        self.log("")

    def display_status(self):
        """显示当前状态（受异变影响）"""
        status = self.player.get_status()

        def p(text):
            """打印经过异变处理的文本"""
            if self.player.mutation > 0:
                text = self._corrupt_text(text)
            print(text)

        p("-" * 30)
        p(f"【当前状态】{self.player.year_name} {status['学期']} {status['周数']}")
        p(f"理智: {status['理智']}")
        p(f"行动点: {status['行动点']}")
        p(f"INT: {status['INT直觉']} | SEN: {status['SEN感知']} | EDU: {status['EDU知识']}")
        p(f"STR: {status['STR耐力']} | SOC: {status['SOC社交']}")
        p(f"声望: {status['声望']} | 研究方向: {status['研究方向']}")
        p(f"已发表论文: {status['已发表论文']}")
        p("-" * 30)

    def display_skills(self):
        """显示技能（旧系统，保留用于兼容）"""
        print("【技能】")
        for skill, level in self.player.skills.items():
            print(f"  {skill}: {level}")
        print("")

    def do_action(self, action: str) -> bool:
        """执行行动

        Returns:
            是否继续游戏
        """
        # 如果正在等待idea评估决定，先处理决定
        if self.awaiting_idea_decision:
            self.awaiting_idea_decision = False
            return self._handle_idea_decision(action)

        # 检查行动点
        # STR继续工作检测：高STR(>70)时概率触发
        if self.player.STR > 70 and self.player.continue_action_count < self.player.max_continue_actions:
            trigger_chance = (self.player.STR - 70) / 2  # 例如STR=80时为5%
            if random.random() * 100 < trigger_chance:
                # 触发继续工作！
                self.player.continue_action_count += 1
                self.log("【STR继续工作】你感觉自己还有精力，可以再做一件事！")
                # 不消耗行动点，直接返回继续游戏
                self._trigger_random_event()
                self._check_game_over()
                return not self.game_over

        if not self.player.consume_action_point():
            self.log("本周行动点已用完！")
            self.player.advance_week()
            self.player.reset_action_points()
            self._check_game_over()
            return not self.game_over

        self.turn_count += 1
        action_result = ""

        # 判断是否是假期
        is_holiday = self.player.semester in (SemesterType.SUMMER, SemesterType.WINTER)

        # 根据行动执行对应功能
        if action == "1":
            if is_holiday:
                # 假期：休息
                action_result = self._do_rest()
            elif self.player.year == 1 and not self.course_system.first_semester_completed:
                # 研一且课程未完成：选课/上课
                if self.player.week_in_semester == 1 and not self.player.courses_selected:
                    action_result = self._do_select_courses()
                else:
                    action_result = self._do_class()
            else:
                # 课程已完成，进入科研：阅读文献
                if not self.player.research_direction:
                    action_result = self.research_system.assign_research_direction()
                else:
                    action_result = self.research_system.read_literature()

        elif action == "2":
            # 研一：期末考试 或 科研（课程完成后）
            if self.player.year == 1:
                if not self.course_system.first_semester_completed and self._is_final_week():
                    # 课程未完成且是期末周：考试
                    action_result = self._do_final_exam()
                elif self.course_system.first_semester_completed:
                    # 课程已完成：进入科研
                    if not self.player.research_direction:
                        action_result = self.research_system.assign_research_direction()
                    else:
                        action_result = self.research_system.read_literature()
                else:
                    action_result = "现在是上课时间，请先完成课程！"
            else:
                # 研二及以上：科研
                if not self.player.research_direction:
                    action_result = self.research_system.assign_research_direction()
                else:
                    action_result = self.research_system.read_literature()
        elif action.lower() == "e":
            # 评估Idea - 设置状态等待玩家决定
            self.awaiting_idea_decision = True
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
        elif action == "b" or action == "B":
            # Debug: 跳转到研二（测试小论文系统）
            self._debug_go_to_year2()
            return False
        elif action.lower() == "m":
            # Debug: 异变+1（测试异变效果）
            self.player.mutation += 1
            self.log(f"[DEBUG] 异变值+1，当前异变值: {self.player.mutation:.2f} ({self.player.mutation_level})")
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

        # 异变效果：每轮理智减少 + 显示异变信息
        self._apply_mutation_effect()

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

    def _debug_go_to_year2(self):
        """Debug功能：跳转到研二（直接测试小论文系统）"""
        from .character import ResearchDirection

        self.player.year = 2
        self.player.semester = SemesterType.SPRING
        self.player.week_in_semester = 1
        self.player.courses_selected = True

        # 标记第一学期已完成（直接进入科研）
        self.course_system.first_semester_completed = True

        # 赋予一个研究方向（随机）
        if not self.player.research_direction:
            self.player.research_direction = random.choice(list(ResearchDirection))

        # 重置行动点
        self.player.reset_action_points()

        self.log("[DEBUG] ===== 跳转到研二 =====")
        self.log(f"当前状态：{self.player.year_name} {self.player.semester_name} 第{self.player.week_in_semester}周")
        self.log(f"研究方向：{self.player.research_direction.value}")
        self.log(f"INT:{self.player.INT} | SEN:{self.player.SEN} | EDU:{self.player.EDU}")
        self.log(f"STR:{self.player.STR} | SOC:{self.player.SOC} | 声望:{self.player.reputation}")
        self.log("你现在可以开始阅读文献获取idea了！")
        self.log("按2阅读文献 -> 获得idea -> 按E评估 -> 按3实验 -> 按4写初稿 -> 按5投稿")

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

    def _handle_idea_decision(self, decision: str) -> bool:
        """处理idea评估决定

        Args:
            decision: 决定字符串，如 "1a", "2d", "3i"

        Returns:
            是否继续游戏
        """
        from .research import IdeaStatus

        raw_ideas = [i for i in self.research_system.ideas if i.status == IdeaStatus.RAW]

        if not raw_ideas:
            self.log("没有需要评估的idea！")
            return True

        # 解析决定：格式为 "序号+决定"
        decision = decision.strip().lower()

        if len(decision) < 2:
            self.log("无效输入！格式如：1a（评估第1个idea，接受为初步想法）")
            self.log("a=接受，d=丢弃，i=改进")
            self.awaiting_idea_decision = True  # 重新等待输入
            return True

        try:
            # 解析序号和决定
            index = int(decision[:-1]) - 1  # 转换为0-based
            action = decision[-1]

            if index < 0 or index >= len(raw_ideas):
                self.log(f"无效序号！有效范围：1-{len(raw_ideas)}")
                self.awaiting_idea_decision = True
                return True

            # 获取对应的idea
            idea = raw_ideas[index]

            # 映射决定到evaluate_idea的参数
            if action == "a":
                result = self.research_system.evaluate_idea(
                    self.research_system.ideas.index(idea), "accept")
            elif action == "d":
                result = self.research_system.evaluate_idea(
                    self.research_system.ideas.index(idea), "discard")
            elif action == "i":
                result = self.research_system.evaluate_idea(
                    self.research_system.ideas.index(idea), "improve")
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

    def _do_class(self) -> str:
        """上课（研一时进行）"""
        # 获取当前需要上的课程
        active_courses = self.course_system.get_active_courses()

        if not active_courses:
            return "你已完成所有课程，可以开始科研了！"

        # 随机选择一门课上
        course = random.choice(active_courses)

        # 增加学习次数
        course.study_count += 1

        # 判定成功/失败（只是学习进度，不是考试）
        difficulty = self.player.EDU + course.study_count * 10
        roll = random.randint(1, 100)

        if roll == 1:
            # 大成功：大幅提升属性
            bonus = random.randint(2, 4)
            for attr in ["INT", "SEN", "EDU", "STR"]:
                if attr in course.attributes:
                    current = getattr(self.player, attr)
                    setattr(self.player, attr, current + bonus)
            result = f"【大成功】你对{course.name}有了突飞猛进的理解！\n{attr}+{bonus}"
        elif roll < difficulty:
            # 成功
            bonus = random.randint(1, 2)
            for attr in ["INT", "SEN", "EDU", "STR"]:
                if attr in course.attributes:
                    current = getattr(self.player, attr)
                    setattr(self.player, attr, current + bonus)
            result = f"你认真学习了{course.name}课。\n{attr}+{bonus}"
        else:
            # 失败
            result = f"你上了{course.name}课，但感觉收获不大。"

        # 理智消耗
        san_loss = random.randint(1, 3)
        self.player.change_sanity(-san_loss)
        result += f"\n理智-{san_loss}"

        return result

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

    def _apply_mutation_effect(self):
        """应用异变效果：每轮理智减少 + 显示异变信息"""
        if self.player.mutation <= 0:
            return

        # 每轮理智减少 = 异变值 × 5
        sanity_loss = int(self.player.mutation * 5)
        if sanity_loss > 0:
            self.player.change_sanity(-sanity_loss)
            self.log(f"【异变侵蚀】你感觉到不可名状的痛苦...理智-{sanity_loss}")

        # 异变信息（根据严重程度）
        mutation_messages = {
            (0, 0.5): [
                "你感觉一阵不安...",
                "有什么东西在心里躁动...",
                "你隐约听到一些奇怪的声音...",
            ],
            (0.5, 1): [
                "当你睡下，你总感觉到一阵不安...",
                "镜子里的你似乎有点不一样了...",
                "你发现手上出现了奇怪的花纹...",
            ],
            (1, 2): [
                "现实与梦境的边界开始模糊...",
                "你看到的文字开始扭曲变形...",
                "脑海中的声音越来越清晰...",
            ],
            (2, 100): [
                "你已经不属于这个世界了...",
                "是不可名状，还是本就如此？",
                "一切都没有意义了...",
            ]
        }

        # 显示异变信息
        for (min_val, max_val), messages in mutation_messages.items():
            if min_val <= self.player.mutation < max_val:
                if random.random() < 0.3:  # 30%概率触发
                    self.log(f"【{self.player.mutation_level}】{random.choice(messages)}")
                break

    def _trigger_random_event(self):
        """触发随机事件"""
        # 假期（暑假/寒假）不触发负面事件
        is_holiday = self.player.semester in (SemesterType.SUMMER, SemesterType.WINTER)

        if random.random() < 0.3:  # 30%概率触发
            event = self.event_system.get_random_event(is_holiday)
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
        # 异变值≥2：死亡
        if self.player.mutation >= 2:
            self.game_over = True
            self.ending = "异变"
            self.log("\n" + "=" * 50)
            self.log("你的异变程度已经无可挽回...")
            self.log("你变成了一个不可名状的怪物")
            self.log(f"最终结局：异变死亡（已发表{self.player.papers_published}篇论文）")
            self.log("=" * 50)

        # 理智归零（异变后恢复理智，不再直接结束）
        elif self.player.sanity <= 0:
            self.log("\n" + "【警告】你的理智彻底耗尽！但你并没有完全疯狂...")
            self.log(f"【异变+1】你的身体开始发生不可名状的变化...")
            self.log(f"当前异变值：{self.player.mutation:.2f} ({self.player.mutation_level})")
            self.log("你恢复了部分理智，但异变程度加重了！")

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

        # 判断是否进入科研阶段（研二 或 研一课程已完成）
        in_research = self.player.year >= 2 or self.course_system.first_semester_completed

        # 判断是否是假期（暑假/寒假）
        is_holiday = self.player.semester in (SemesterType.SUMMER, SemesterType.WINTER)

        if not in_research and not is_holiday:
            # 研一且课程未完成且不是假期：课程相关
            # 选课（第一周且未选课）
            if self.player.week_in_semester == 1 and not self.player.courses_selected:
                actions.append(("1", "选课", "选择本学期课程"))
            else:
                actions.append(("1", "上课", "参加课程学习"))

            # 期末考试（最后一周）
            if self._is_final_week():
                actions.append(("2", "期末考试", "参加期末考试"))

        elif is_holiday:
            # 假期期间：显示假期选项
            actions.append(("1", "假期休息", "享受假期时光"))

        # 科研阶段
        if in_research:
            actions.append(("2", "阅读文献", "获取创新idea"))
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
        actions.append(("B", "跳转研二", "[DEBUG] 快速跳转到研二测试小论文"))
        actions.append(("M", "异变+1", "[DEBUG] 测试异变效果"))
        actions.append(("q", "退出", "结束游戏"))

        return actions

    def _is_final_week(self) -> bool:
        """是否期末周"""
        semester_weeks = {SemesterType.SPRING: 18, SemesterType.SUMMER: 7,
                         SemesterType.AUTUMN: 19, SemesterType.WINTER: 5}
        return self.player.week_in_semester >= semester_weeks.get(self.player.semester, 18)
