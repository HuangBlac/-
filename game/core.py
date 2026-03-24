"""核心游戏系统"""
import random
from .character import Player, NPC
from .event_system import EventSystem


class GameCore:
    """游戏核心控制器"""

    def __init__(self, player_name: str):
        self.player = Player(player_name)
        self.event_system = EventSystem()
        self.game_over = False
        self.ending = None
        self.message_log = []  # 消息日志

        # 初始化NPC
        self.npcs = self._init_npcs()

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
        print(f"【当前状态】{self.player.year_name} {status['周数']}")
        print(f"理智: {status['理智']}")
        print(f"知识: {status['知识']} | 灵感: {status['灵感']} | 声望: {status['声望']}")
        print(f"研究进度: {status['研究进度']} | 已发表论文: {status['已发表论文']}")
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
        self.turn_count += 1
        action_result = ""

        if action == "1":  # 上课
            action_result = self._do_class()
        elif action == "2":  # 研究
            action_result = self._do_research()
        elif action == "3":  # 调查
            action_result = self._do_investigation()
        elif action == "4":  # 社交
            action_result = self._do_social()
        elif action == "5":  # 阅读
            action_result = self._do_read()
        elif action == "6":  # 休息
            action_result = self._do_rest()
        elif action == "7":  # 状态
            self.display_status()
            self.display_skills()
            return False  # 查看状态不需要等待
        elif action == "q":  # 退出
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

        # 推进一周
        self.player.advance_week()

        # 检查游戏结束条件
        self._check_game_over()

        return not self.game_over

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

        # 正常毕业
        elif self.player.year > 3:
            self.game_over = True
            if self.player.papers_published >= 3:
                self.ending = "毕业"
                self.log("\n" + "=" * 50)
                self.log("恭喜！你顺利毕业了！")
                self.log(f"最终结局：成为讲师（已发表{self.player.papers_published}篇论文）")
            else:
                self.ending = "延期"
                self.log("\n" + "=" * 50)
                self.log("你未能达到毕业要求...")
                self.log("请继续努力！")
            self.log("=" * 50)

    def get_actions(self) -> list:
        """获取可选行动"""
        return [
            ("1", "上课", "学习课程知识"),
            ("2", "研究", "推进研究进度"),
            ("3", "调查", "参与神秘调查"),
            ("4", "社交", "与NPC交流"),
            ("5", "阅读", "阅读禁忌文本"),
            ("6", "休息", "恢复理智"),
            ("7", "状态", "查看当前状态"),
            ("q", "退出", "结束游戏"),
        ]
