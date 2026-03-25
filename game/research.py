"""科研系统 - Idea获取、实验验证、论文攥写与投稿"""
import random
from enum import Enum
from typing import List, Optional, Dict
from .character import Player, ResearchDirection


class IdeaStatus(Enum):
    """Idea状态"""
    RAW = "原始idea"           # 刚获取的idea
    PRELIMINARY = "初步想法"    # 经过评估的想法
    MATURE = "成熟想法"         # 经过实验验证的想法


class Idea:
    """创新想法"""

    def __init__(self, name: str, description: str, innovation: int,
                 direction: ResearchDirection):
        self.name = name
        self.description = description
        self.innovation = innovation  # 创新值 1-10
        self.direction = direction
        self.status = IdeaStatus.RAW
        self.experiment_results: List['ExperimentResult'] = []
        self.progress = 0  # 评估/实验进度

    def __repr__(self):
        return f"<Idea: {self.name} ({self.status.value})>"


class ExperimentResult:
    """实验结果"""

    def __init__(self, name: str, method: str, quality: int):
        self.name = name
        self.method = method  # 实验方法
        self.quality = quality  # 质量 1-5


# 不同研究方向的idea池
IDEAS_POOL = {
    ResearchDirection.ARCANE_ANALYSIS: [
        ("法术能量模型", "建立描述法术能量的数学模型", 7),
        ("召唤法阵优化", "研究如何提高召唤法阵的成功率", 8),
        ("超自然科技史", "分析古代文明遗留的超自然科技", 6),
        ("附魔材料研究", "探索附魔所需材料的特性", 5),
        ("灵阵编码", "将魔法阵转化为可解读的编码系统", 9),
    ],
    ResearchDirection.MYTHOS_RITUAL: [
        ("文本溯源分析", "通过文本比对确定古籍抄写年代", 7),
        ("失传语言破译", "破解古代祭祀用语的含义", 8),
        ("仪式流程重建", "还原古代召唤仪式的完整步骤", 9),
        ("神话地理考证", "比对神话地点与现实地理位置", 6),
        ("预言文本解读", "分析预言文本的模糊性特征", 8),
    ],
    ResearchDirection.DEITY_RACE: [
        ("深潜者社会结构", "研究深潜者种群的社会组织形式", 7),
        ("神话生物基因分析", "分析混血种族的遗传特征", 8),
        ("附庸种族演化", "研究神明附庸种族的进化历程", 6),
        ("跨种族交流", "探索与神话生物沟通的可能性", 9),
        ("神话生物学", "建立神话生物的分类学体系", 7),
    ],
    ResearchDirection.OUTER_GOD: [
        ("克苏鲁混沌模型", "建立描述阿撒托斯周围混沌能量的数学模型", 8),
        ("旧日支配者意识探查", "通过量子纠缠探测古神意识场", 9),
        ("纬度入侵理论", "研究旧日支配者跨越维度的入侵机制", 10),
        ("外神心理分析", "分析外神的思维模式与动机", 8),
        ("触手运动学", "分析大量触手怪物的运动模式", 5),
    ],
}

# 不同研究方向对应的实验方法
EXPERIMENT_METHODS = {
    ResearchDirection.ARCANE_ANALYSIS: [
        ("形式科学建模分析", "建立数学模型进行形式化分析"),
        ("计算机模拟", "使用计算机模拟法术效果"),
        ("数据收集与统计", "收集法术实验数据进行统计分析"),
    ],
    ResearchDirection.MYTHOS_RITUAL: [
        ("钻研典籍", "深入阅读分析古代文献"),
        ("文本比对", "对比多个版本的文本差异"),
        ("考古验证", "通过考古发现验证文本内容"),
    ],
    ResearchDirection.DEITY_RACE: [
        ("田野调查", "实地考察神话种族聚居地"),
        ("DNA分析", "提取并分析神话生物的遗传物质"),
        ("社会学研究", "通过访谈和观察研究其社会结构"),
    ],
    ResearchDirection.OUTER_GOD: [
        ("理论研究", "构建纯理论框架进行分析"),
        ("数学建模", "使用高等数学描述外神特性"),
        ("哲学思辨", "从哲学角度理解超越性存在"),
    ],
}


class Paper:
    """学术论文"""

    def __init__(self, ideas: List[Idea]):
        self.ideas = ideas  # 包含的成熟想法
        self.draft_progress = 0  # 初稿进度 0-100
        self.title = ""
        self.is_complete = False
        self.quality = 0  # 论文质量

    def calculate_quality(self) -> int:
        """计算论文质量"""
        if not self.ideas:
            return 0

        # 创新值平均
        avg_innovation = sum(i.innovation for i in self.ideas) / len(self.ideas)

        # 实验丰富程度
        total_experiments = sum(len(i.experiment_results) for i in self.ideas)

        # 契合性（同一方向）
        directions = set(i.direction for i in self.ideas)
        coherence = 10 if len(directions) == 1 else 5

        # 多样性
        diversity = min(10, len(set(r.method for i in self.ideas for r in i.experiment_results)))

        # 综合评分
        quality = int(avg_innovation * 2 + total_experiments * 2 + coherence + diversity)
        return min(100, quality)


class ResearchSystem:
    """科研管理系统"""

    def __init__(self, player: Player):
        self.player = player
        self.ideas: List[Idea] = []  # 所有idea
        self.current_paper: Optional[Paper] = None
        self.literature_progress = 0  # 文献阅读进度 0-100

    def can_start_research(self) -> bool:
        """是否可以开始科研（研二及以上）"""
        return self.player.year >= 2

    def assign_research_direction(self) -> str:
        """分配研究方向（研二时自动调用）"""
        if self.player.research_direction:
            return f"你已有研究方向：{self.player.research_direction.value}"

        # 随机分配一个研究方向
        direction = random.choice(list(ResearchDirection))
        self.player.research_direction = direction

        direction_names = {
            ResearchDirection.ARCANE_ANALYSIS: "法术与超自然科技分析",
            ResearchDirection.MYTHOS_RITUAL: "神话文本与仪式构造",
            ResearchDirection.DEITY_RACE: "神明附属种族与独立种族",
            ResearchDirection.OUTER_GOD: "旧日支配者与外神",
        }

        return f"根据你的课程学习，你被分配到{direction_names[direction]}方向进行研究！"

    def start_research(self) -> str:
        """开始科研（选择研究方向）"""
        if not self.can_start_research():
            return "只有研二及以上才能开始科研！"

        # 如果没有研究方向，自动分配一个
        if not self.player.research_direction:
            return self.assign_research_direction()

        return f"你开始跟随{self.player.relationships.get('导师', '导师')}进行{self.player.research_direction.value}..."

    def read_literature(self) -> str:
        """阅读文献获取idea"""
        if not self.can_start_research():
            return "只有研二及以上才能开始科研！"

        if not self.player.research_direction:
            return "请先选择研究方向！"

        # 进度增加
        progress_gain = random.randint(10, 20) + self.player.knowledge // 10
        self.literature_progress = min(100, self.literature_progress + progress_gain)

        result = f"你正在阅读文献...\n文献阅读进度: {self.literature_progress}%"

        # 进度达到100%时获得新idea
        if self.literature_progress >= 100:
            idea = self._generate_idea()
            self.ideas.append(idea)
            self.literature_progress = 0
            result += f"\n你获得了新的idea: {idea.name}\n{idea.description}\n创新值: {idea.innovation}/10"

        return result

    def _generate_idea(self) -> Idea:
        """生成新idea"""
        pool = IDEAS_POOL.get(self.player.research_direction, [])
        name, desc, innovation = random.choice(pool)
        # 添加一些随机变化
        innovation = max(1, min(10, innovation + random.randint(-1, 1)))
        return Idea(name, desc, innovation, self.player.research_direction)

    def evaluate_idea(self, idea_index: int, decision: str) -> str:
        """评估idea

        Args:
            idea_index: idea索引
            decision: "discard"(丢弃), "improve"(改进), "accept"(接受)

        Returns:
            评估结果
        """
        if idea_index >= len(self.ideas):
            return "无效的idea索引！"

        idea = self.ideas[idea_index]

        if decision == "discard":
            # 丢弃，增加能力值
            ability_gain = random.randint(1, 3)
            skill = random.choice(list(self.player.skills.keys()))
            self.player.skills[skill] += ability_gain
            self.ideas.remove(idea)
            return f"你放弃了这个idea。\n+{ability_gain} {skill}"

        elif decision == "improve":
            # 有待改进，进度重置，增加能力
            idea.progress = 0
            ability_gain = random.randint(1, 2)
            skill = random.choice(list(self.player.skills.keys()))
            self.player.skills[skill] += ability_gain
            return f"idea需要改进。\n+{ability_gain} {skill}，请继续研究"

        elif decision == "accept":
            # 接受为初步想法
            idea.status = IdeaStatus.PRELIMINARY
            return f"你接受了这个idea作为初步想法！\n现在可以进行实验验证。"

        return "无效的决定！"

    def conduct_experiment(self, idea_index: int) -> str:
        """对idea进行实验验证"""
        if idea_index >= len(self.ideas):
            return "无效的idea索引！"

        idea = self.ideas[idea_index]

        if idea.status != IdeaStatus.PRELIMINARY:
            return "只有初步想法才能进行实验！"

        # 根据研究方向选择实验方法
        methods = EXPERIMENT_METHODS.get(self.player.research_direction, [])
        method_name, method_desc = random.choice(methods)

        # 实验成功概率
        success_rate = 0.5 + (self.player.knowledge * 0.02) + (self.player.inspiration * 0.01)
        # 导师加成
        advisor_favor = self.player.relationships.get("导师", 50)
        success_rate += advisor_favor * 0.001

        if random.random() < success_rate:
            # 实验成功，产生结果
            quality = random.randint(2, 5)
            result = ExperimentResult(f"实验结果{len(idea.experiment_results)+1}",
                                      method_name, quality)
            idea.experiment_results.append(result)

            # 检查是否变为成熟想法
            if len(idea.experiment_results) >= 2:
                idea.status = IdeaStatus.MATURE

            return f"实验成功！\n{method_desc}\n结果质量: {quality}/5\n实验结果数: {len(idea.experiment_results)}"
        else:
            # 实验失败
            san_loss = random.randint(1, 3)
            self.player.change_sanity(-san_loss)
            return f"实验失败...\n{method_desc}\n理智-{san_loss}"

    def write_draft(self, progress: int = 10) -> str:
        """撰写初稿"""
        if not self.current_paper:
            # 创建新论文
            mature_ideas = [i for i in self.ideas if i.status == IdeaStatus.MATURE]
            if len(mature_ideas) < 3:
                return f"需要3个成熟想法才能撰写论文！当前有{len(mature_ideas)}个。"
            self.current_paper = Paper(mature_ideas[:3])

        # 增加初稿进度
        writing_speed = random.randint(5, 15) + self.player.knowledge // 10
        self.current_paper.draft_progress = min(100,
            self.current_paper.draft_progress + writing_speed)

        result = f"撰写初稿...\n初稿进度: {self.current_paper.draft_progress}%"

        if self.current_paper.draft_progress >= 100:
            result += "\n初稿完成！可以投稿了。"
            self.current_paper.is_complete = True
            self.current_paper.quality = self.current_paper.calculate_quality()

        return result

    def submit_paper(self) -> str:
        """投稿论文"""
        if not self.current_paper or not self.current_paper.is_complete:
            return "没有完整的论文可以投稿！"

        # 计算投稿成功率
        base_success = 0.3
        quality_bonus = self.current_paper.quality * 0.004
        experience_bonus = self.player.papers_published * 0.05
        reputation_bonus = self.player.reputation * 0.002

        success_rate = base_success + quality_bonus + experience_bonus + reputation_bonus

        roll = random.random()

        if roll < 0.1:
            # Desk Reject
            self.current_paper = None
            return "【Desk Reject】\n论文未经送审直接被拒！\n论文被摧毁。"
        elif roll < 0.1 + success_rate * 0.3:
            # Major Reject
            self.current_paper.draft_progress = random.randint(30, 60)
            self.current_paper.is_complete = False
            # 损失2个结果
            for idea in self.current_paper.ideas[:2]:
                if idea.experiment_results:
                    idea.experiment_results.pop()
            return "【Major Reject】\n论文需要大修！\n初稿进度降至30%-60%，损失2个实验结果。"
        elif roll < 0.1 + success_rate * 0.6:
            # Minor Reject
            self.current_paper.draft_progress = random.randint(70, 90)
            self.current_paper.is_complete = False
            # 损失0-1个结果
            if self.current_paper.ideas[0].experiment_results:
                self.current_paper.ideas[0].experiment_results.pop()
            return "【Minor Reject】\n论文需要小修！\n初稿进度降至70%-90%。"
        else:
            # Accept
            self.player.papers_published += 1
            self.player.reputation += random.randint(10, 20)
            san_restore = random.randint(5, 10)
            self.player.change_sanity(san_restore)

            # 保存论文
            published_paper = self.current_paper
            self.current_paper = None
            # 清除已用掉的成熟想法
            for idea in published_paper.ideas:
                if idea in self.ideas:
                    self.ideas.remove(idea)

            return f"【Accept】\n恭喜！论文被接受！\n发表论文+1，声望+{published_paper.quality // 2}，理智+{san_restore}"

    def get_idea_status(self) -> str:
        """获取所有idea的状态"""
        if not self.ideas:
            return "尚无私有idea。"

        status = ["【Idea列表】"]
        for i, idea in enumerate(self.ideas):
            status.append(f"{i}. {idea.name} ({idea.status.value})")
            status.append(f"   创新值: {idea.innovation}/10")
            status.append(f"   实验结果: {len(idea.experiment_results)}个")
        return "\n".join(status)
