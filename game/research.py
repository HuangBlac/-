"""科研系统 - Idea获取、实验验证、论文攥写与投稿"""
import random
from enum import Enum
from typing import List, Optional, Dict
from .character import Player, ResearchDirection, ability_check, CheckResult


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

    def __init__(self, name: str, method: str, quality: int,
                 theory: int = None, experiment: int = None, depth: int = None):
        self.name = name
        self.method = method  # 实验方法
        self.quality = quality  # 质量 1-5
        # 三维数值（如果未提供，则从quality推导）
        self.theory = theory if theory is not None else quality
        self.experiment = experiment if experiment is not None else quality
        self.depth = depth if depth is not None else quality


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
        """计算论文质量（使用三维数值）"""
        if not self.ideas:
            return 0

        # 创新值平均
        avg_innovation = sum(i.innovation for i in self.ideas) / len(self.ideas)

        # 汇总实验结果的三维数值
        total_theory = sum(r.theory for i in self.ideas for r in i.experiment_results)
        total_experiment = sum(r.experiment for i in self.ideas for r in i.experiment_results)
        total_depth = sum(r.depth for i in self.ideas for r in i.experiment_results)

        # 理论深度 = 理论密度之和
        total_theory_density = total_theory

        # 契合性（同一方向）
        directions = set(i.direction for i in self.ideas)
        coherence = 10 if len(directions) == 1 else 5

        # 综合评分 = 创新值×2 + 实验支撑×2 + 理论深度
        base_quality = int(avg_innovation * 2 + total_experiment * 2 + total_theory_density + coherence)

        # EDU知识加成
        edu_bonus = 1 + self.ideas[0].experiment_results[0].depth / 200 if self.ideas and self.ideas[0].experiment_results else 1

        quality = int(base_quality * edu_bonus)
        return min(100, quality)

    def get_stats(self) -> dict:
        """获取论文统计数据（用于期刊投递）"""
        if not self.ideas:
            return {"创新值": 0, "理论深度": 0, "实验支撑": 0}

        avg_innovation = sum(i.innovation for i in self.ideas) / len(self.ideas)
        total_theory = sum(r.theory for i in self.ideas for r in i.experiment_results)
        total_experiment = sum(r.experiment for i in self.ideas for r in i.experiment_results)

        return {
            "创新值": avg_innovation,
            "理论深度": total_theory,
            "实验支撑": total_experiment
        }


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
        """阅读文献获取idea（使用新判定系统）

        1. 先进行感知(SEN)判定决定阅读进度
        2. 达到100%时进行直觉(INT)判定决定idea创新值
        """
        if not self.can_start_research():
            return "只有研二及以上才能开始科研！"

        if not self.player.research_direction:
            return "请先选择研究方向！"

        # 获取导师效率修正
        efficiency_mod = self._get_efficiency_modifier()

        # ===== 第一步：感知判定决定阅读进度 =====
        current_progress = self.literature_progress

        # 进行SEN感知判定
        check_result, roll = ability_check(self.player, "SEN")
        result_msg = [f"【阅读文献】判定结果: {check_result} (骰点:{roll})"]

        # 根据判定结果计算进度（应用导师效率修正）
        edu_bonus = 1 + self.player.EDU / 100
        sen_bonus = self.player.SEN / 10

        if check_result == CheckResult.CRITICAL_SUCCESS:
            # 大成功：进度 = max(70, i*2)
            progress_gain = max(70, current_progress * 2) - current_progress
            result_msg.append("你感觉这篇文章的知识直接流入了你的脑海！")
        elif check_result in [CheckResult.EXTREME_SUCCESS, CheckResult.HARD_SUCCESS, CheckResult.SUCCESS]:
            # 成功：正常进度
            base_progress = 10 + sen_bonus
            progress_gain = int(base_progress * edu_bonus * efficiency_mod)
            result_msg.append("你仔细阅读这篇文章，收获颇丰。")
        elif check_result == CheckResult.FAILURE:
            # 失败：进度不良
            progress_gain = int(10 * edu_bonus * efficiency_mod)
            result_msg.append("你感觉这篇文章有些晦涩难懂，进度不良。")
        else:
            # 大失败：进度倒退
            progress_gain = -current_progress + min(30, current_progress // 2)
            result_msg.append("你感觉你过往所认知的知识全都是错误的...搞错了搞错了！")

        self.literature_progress = max(0, min(100, current_progress + progress_gain))

        result_msg.append(f"文献阅读进度: {self.literature_progress}%")

        # ===== 第二步：进度达到100%时生成idea =====
        if self.literature_progress >= 100:
            idea_result, idea_roll = self._generate_idea_with_check()
            result_msg.append("")
            result_msg.append(idea_result)

        return "\n".join(result_msg)

    def _get_efficiency_modifier(self) -> float:
        """获取导师科研效率修正"""
        if self.player.advisor:
            return self.player.advisor.efficiency_modifier
        return 1.0

    def _get_sanity_consumption_modifier(self) -> float:
        """获取导师理智消耗修正"""
        if self.player.advisor:
            return self.player.advisor.sanity_consumption_modifier
        return 1.0

    def _generate_idea_with_check(self) -> str:
        """生成idea（使用INT判定决定创新值）"""
        # 进行INT直觉判定
        check_result, roll = ability_check(self.player, "INT")

        # 从池中获取基础创新值
        pool = IDEAS_POOL.get(self.player.research_direction, [])
        name, desc, base_innovation = random.choice(pool)

        if check_result == CheckResult.CRITICAL_SUCCESS:
            # 大成功：创新值10
            innovation = 10
            msg = f"【大成功】你感觉你才思泉涌，想到了一个从未有过的天才想法！"
        elif check_result in [CheckResult.EXTREME_SUCCESS, CheckResult.HARD_SUCCESS, CheckResult.SUCCESS]:
            # 成功：按公式计算创新值
            innovation = int(base_innovation * (1 + self.player.INT / 50))
            innovation = max(1, min(10, innovation))
            msg = f"【成功】你冥思苦想，想到了一个不错的点子。"
        elif check_result == CheckResult.FAILURE:
            # 失败：不生成idea，进度回退
            self.literature_progress = random.randint(70, 80)
            return f"【失败】你未能理解这篇文章的核心思想，无法产生有效的idea。\n文献阅读进度回退到{self.literature_progress}%。", roll
        else:
            # 大失败：进度清零，异变值+0.05
            self.literature_progress = 0
            self.player.mutation += 0.05
            return f"【大失败】你的精神受到了冲击，感觉自己过往的学习就是一团灰尘...  \n文献阅读进度清零。\n【异变+0.05】", roll

        # 创建idea
        idea = Idea(name, desc, innovation, self.player.research_direction)
        self.ideas.append(idea)
        self.literature_progress = 0

        msg += f"\n你获得了新的idea: {idea.name}\n{idea.description}\n创新值: {idea.innovation}/10"
        return msg

    def _generate_idea(self) -> Idea:
        """生成新idea（旧版兼容）"""
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
            # 丢弃，随机提升一个学术属性
            ability_gain = random.randint(1, 3)
            attr = random.choice(["INT", "SEN", "EDU"])
            setattr(self.player, attr, getattr(self.player, attr) + ability_gain)
            self.ideas.remove(idea)
            return f"你放弃了这个idea。\n{attr}+{ability_gain}"

        elif decision == "improve":
            # 有待改进，进度重置，随机提升一个学术属性
            idea.progress = 0
            ability_gain = random.randint(1, 2)
            attr = random.choice(["INT", "SEN", "EDU"])
            setattr(self.player, attr, getattr(self.player, attr) + ability_gain)
            return f"idea需要改进。\n{attr}+{ability_gain}，请继续研究"

        elif decision == "accept":
            # 接受为初步想法
            idea.status = IdeaStatus.PRELIMINARY
            return f"你接受了这个idea作为初步想法！\n现在可以进行实验验证。"

        return "无效的决定！"

    def conduct_experiment(self, idea_index: int) -> str:
        """对idea进行实验验证（使用新判定系统）

        使用INT+SEN+EDU综合判定
        """
        if idea_index >= len(self.ideas):
            return "无效的idea索引！"

        idea = self.ideas[idea_index]

        if idea.status != IdeaStatus.PRELIMINARY:
            return "只有初步想法才能进行实验！"

        # 获取导师效率修正
        efficiency_mod = self._get_efficiency_modifier()
        sanity_mod = self._get_sanity_consumption_modifier()

        # 根据研究方向选择实验方法
        methods = EXPERIMENT_METHODS.get(self.player.research_direction, [])
        method_name, method_desc = random.choice(methods)

        # 使用综合属性进行判定（取三者的平均值作为能力值，应用效率修正）
        avg_ability = (self.player.INT + self.player.SEN + self.player.EDU) // 3
        avg_ability = int(avg_ability * efficiency_mod)
        check_result, roll = ability_check(self.player, "INT", avg_ability)

        result_msg = [f"【实验验证】判定结果: {check_result} (骰点:{roll})"]
        result_msg.append(f"实验方法: {method_name}")

        if check_result == CheckResult.CRITICAL_SUCCESS:
            # 大成功：高质量结果，三维都高
            theory = 5
            experiment = 5
            depth = 5
            result_msg.append("你取得了突破性进展！实验结果远超预期！")
            san_change = 5  # 理智回复
            self.player.change_sanity(san_change)
        elif check_result in [CheckResult.EXTREME_SUCCESS, CheckResult.HARD_SUCCESS]:
            # 极难/困难成功：高result_msg.append("实验取得了很好的结果！")
            theory = random.randint(3, 5)
            experiment = random.randint(3, 5)
            depth = random.randint(3, 5)
            san_change = 2
            self.player.change_sanity(san_change)
        elif check_result == CheckResult.SUCCESS:
            # 一般成功：正常结果（应用导师效率修正）
            theory = random.randint(2, 4)
            experiment = random.randint(2, 4)
            depth = random.randint(2, 4)
            # 进度增加
            result_msg.append("实验按预期进行，得到了有效结果。")
            san_change = 0
        elif check_result == CheckResult.FAILURE:
            # 失败：结果质量低，可能损失理智（应用导师理智消耗修正）
            theory = random.randint(1, 2)
            experiment = random.randint(1, 2)
            depth = random.randint(1, 2)
            san_loss = int(random.randint(3, 8) * sanity_mod)
            self.player.change_sanity(-san_loss)
            result_msg.append(f"实验结果不理想...理智-{san_loss}")
            san_change = 0
        else:
            # 大失败：结果丢失，可能损失理智，异变+0.05（应用导师理智消耗修正）
            theory = 0
            experiment = 0
            depth = 0
            san_loss = int(random.randint(8, 15) * sanity_mod)
            self.player.change_sanity(-san_loss)
            self.player.mutation += 0.05
            result_msg.append(f"实验完全失败，实验材料损毁...理智-{san_loss}")
            result_msg.append("【异变+0.05】")
            san_change = 0

        # 创建实验结果（三维数值）
        quality = (theory + experiment + depth) // 3
        result = ExperimentResult(
            f"实验结果{len(idea.experiment_results)+1}",
            method_name,
            quality,
            theory=theory,
            experiment=experiment,
            depth=depth
        )
        idea.experiment_results.append(result)

        # 显示结果
        result_msg.append(f"理论密度:{theory} | 实验支撑:{experiment} | 学科深度:{depth}")
        result_msg.append(f"实验结果数: {len(idea.experiment_results)}")

        # 检查是否变为成熟想法
        if len(idea.experiment_results) >= 2:
            idea.status = IdeaStatus.MATURE
            result_msg.append("idea已升级为成熟想法！")

        return "\n".join(result_msg)

    def write_draft(self, progress: int = 10) -> str:
        """撰写初稿"""
        if not self.current_paper:
            # 创建新论文
            mature_ideas = [i for i in self.ideas if i.status == IdeaStatus.MATURE]
            if len(mature_ideas) < 3:
                return f"需要3个成熟想法才能撰写论文！当前有{len(mature_ideas)}个。"
            self.current_paper = Paper(mature_ideas[:3])

        # 增加初稿进度
        writing_speed = random.randint(5, 15) + self.player.EDU // 10
        self.current_paper.draft_progress = min(100,
            self.current_paper.draft_progress + writing_speed)

        result = f"撰写初稿...\n初稿进度: {self.current_paper.draft_progress}%"

        if self.current_paper.draft_progress >= 100:
            result += "\n初稿完成！可以投稿了。"
            self.current_paper.is_complete = True
            self.current_paper.quality = self.current_paper.calculate_quality()

        return result

    def submit_paper(self) -> str:
        """投稿论文（使用新判定系统）

        使用SOC+EDU综合判定
        """
        if not self.current_paper or not self.current_paper.is_complete:
            return "没有完整的论文可以投稿！"

        # 使用SOC+EDU综合判定
        avg_ability = (self.player.SOC + self.player.EDU) // 2
        check_result, roll = ability_check(self.player, "SOC", avg_ability)

        result_msg = [f"【投稿判定】判定结果: {check_result} (骰点:{roll})"]

        # 论文统计
        stats = self.current_paper.get_stats()
        result_msg.append(f"论文质量: 创新{stats['创新值']:.1f} | 理论{stats['理论深度']} | 实验{stats['实验支撑']}")

        # 根据判定结果处理
        if check_result == CheckResult.CRITICAL_SUCCESS:
            # 大成功：直接接受
            self.player.papers_published += 1
            self.player.reputation += random.randint(15, 25)
            san_restore = random.randint(10, 15)
            self.player.change_sanity(san_restore)
            result_msg.append("【直接接受】审稿人一致认为这是开创性工作！直接发表！")
            result_msg.append(f"发表论文+1，声望+{self.player.reputation}，理智+{san_restore}")
            self._clear_paper()
        elif check_result in [CheckResult.EXTREME_SUCCESS, CheckResult.HARD_SUCCESS]:
            # 极难/困难成功：小修后接受
            self.player.papers_published += 1
            self.player.reputation += random.randint(10, 20)
            san_restore = random.randint(5, 10)
            self.player.change_sanity(san_restore)
            result_msg.append("【小修后接受】论文经过小修后被接受！")
            result_msg.append(f"发表论文+1，声望+{self.player.reputation}，理智+{san_restore}")
            self._clear_paper()
        elif check_result == CheckResult.SUCCESS:
            # 一般成功：可能小修或大修
            if random.random() < 0.5:
                self.player.papers_published += 1
                self.player.reputation += random.randint(10, 15)
                san_restore = random.randint(5, 10)
                self.player.change_sanity(san_restore)
                result_msg.append("【接受】论文被接受！")
                result_msg.append(f"发表论文+1，声望+{self.player.reputation}，理智+{san_restore}")
                self._clear_paper()
            else:
                # 小修
                self.current_paper.draft_progress = random.randint(70, 90)
                self.current_paper.is_complete = False
                result_msg.append("【小修】论文需要小修！看来得稍微修改点了。")
        elif check_result == CheckResult.FAILURE:
            # 失败：大修或拒稿
            if random.random() < 0.5:
                # 大修
                self.current_paper.draft_progress = random.randint(30, 60)
                self.current_paper.is_complete = False
                # 损失实验结果
                for idea in self.current_paper.ideas[:2]:
                    if idea.experiment_results:
                        idea.experiment_results.pop()
                result_msg.append("【大修】论文需要大修！不但大部分都得重写，好多结果也得重做了...")
            else:
                # 拒稿
                san_loss = random.randint(5, 10)
                self.player.change_sanity(-san_loss)
                result_msg.append(f"【拒稿】论文被拒绝...理智-{san_loss}")
                self.current_paper = None
        else:
            # 大失败：Desk Reject，异变+0.05
            san_loss = random.randint(10, 20)
            self.player.change_sanity(-san_loss)
            self.player.mutation += 0.05
            result_msg.append(f"【Desk Reject】论文未经送审直接被拒！\n论文被摧毁...理智-{san_loss}")
            result_msg.append("你感觉自己被学术界彻底否定了...")
            self.current_paper = None

        return "\n".join(result_msg)

    def _clear_paper(self):
        """清除当前论文（发表成功后）"""
        published_paper = self.current_paper
        self.current_paper = None
        # 清除已用掉的成熟想法
        for idea in published_paper.ideas:
            if idea in self.ideas:
                self.ideas.remove(idea)

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
