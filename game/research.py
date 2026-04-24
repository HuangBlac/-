"""科研系统 - Idea获取、实验验证、论文攥写与投稿"""
import json
import random
from enum import Enum
from pathlib import Path
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




def _load_json_data(filename: str) -> dict:
    """从data目录加载JSON数据"""
    data_dir = Path(__file__).parent / "data"
    filepath = data_dir / filename
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[警告] 找不到数据文件: {filepath}")
        return {}


def _parse_ideas_pool(raw: dict) -> Dict[ResearchDirection, List[tuple]]:
    """将JSON原始数据解析为IDEAS_POOL格式"""
    pool = {}
    for dir_name, ideas in raw.items():
        direction = ResearchDirection[dir_name]
        pool[direction] = [
            (idea["name"], idea["description"], idea["innovation"])
            for idea in ideas
        ]
    return pool


def _parse_experiment_methods(raw: dict) -> Dict[ResearchDirection, List[tuple]]:
    """将JSON原始数据解析为EXPERIMENT_METHODS格式"""
    methods = {}
    for dir_name, method_list in raw.items():
        direction = ResearchDirection[dir_name]
        methods[direction] = [
            (method["name"], method["description"])
            for method in method_list
        ]
    return methods


# 加载数据文件
_IDEAS_POOL_RAW = _load_json_data("ideas.json")
_EXPERIMENT_METHODS_RAW = _load_json_data("experiment_methods.json")

IDEAS_POOL = _parse_ideas_pool(_IDEAS_POOL_RAW)
EXPERIMENT_METHODS = _parse_experiment_methods(_EXPERIMENT_METHODS_RAW)


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

    def __init__(self, player: Player, mutation_system=None):
        self.player = player
        self.mutation_system = mutation_system
        self.ideas: List[Idea] = []  # 所有idea
        self.current_paper: Optional[Paper] = None
        self.literature_progress = 0  # 文献阅读进度 0-100

    @staticmethod
    def _has_enough_experiment_results(idea: Idea) -> bool:
        """Return whether an idea has enough experiment support to stay mature."""
        return len(idea.experiment_results) >= 2

    def _refresh_idea_status(self, idea: Idea) -> None:
        """Keep PRELIMINARY/MATURE in sync with experiment result count."""
        if idea.status == IdeaStatus.RAW:
            return

        if self._has_enough_experiment_results(idea):
            idea.status = IdeaStatus.MATURE
        else:
            idea.status = IdeaStatus.PRELIMINARY

    def _get_mature_ideas(self) -> List[Idea]:
        """Return ideas that still satisfy the mature-paper threshold."""
        mature_ideas = []
        for idea in self.ideas:
            self._refresh_idea_status(idea)
            if idea.status == IdeaStatus.MATURE:
                mature_ideas.append(idea)
        return mature_ideas

    def _paper_has_valid_ideas(self, paper: Paper) -> bool:
        """Check whether every idea inside the paper still has enough support."""
        invalid_found = False
        for idea in paper.ideas:
            self._refresh_idea_status(idea)
            if idea.status != IdeaStatus.MATURE:
                invalid_found = True
        return not invalid_found

    def get_experiment_block_reason(self) -> Optional[str]:
        """Return the reason experiment cannot proceed, or None if it can."""
        ideas = [idea for idea in self.ideas if idea.status == IdeaStatus.PRELIMINARY]
        if not ideas:
            return "没有初步想法可以实验。\n请先通过阅读文献获得idea，然后评估为初步想法。"
        return None

    def get_write_draft_block_reason(self) -> Optional[str]:
        """Return the reason draft writing cannot proceed, or None if it can."""
        if self.current_paper and not self._paper_has_valid_ideas(self.current_paper):
            self.current_paper.is_complete = False
            return "当前论文依赖的成熟想法实验结果不足，请先补做实验再继续写作！"

        if not self.current_paper:
            mature_ideas = self._get_mature_ideas()
            if len(mature_ideas) < 3:
                return f"需要3个成熟想法才能撰写论文！当前有{len(mature_ideas)}个。"

        return None

    def get_submit_paper_block_reason(self) -> Optional[str]:
        """Return the reason paper submission cannot proceed, or None if it can."""
        if not self.current_paper or not self.current_paper.is_complete:
            return "没有完整的论文可以投稿！"

        if not self._paper_has_valid_ideas(self.current_paper):
            self.current_paper.is_complete = False
            return "当前论文的实验结果支撑不足，请先补做实验再投稿！"

        return None

    def can_start_research(self) -> bool:
        """是否可以开始科研（通过课程考试解锁）"""
        return getattr(self.player, "research_unlocked", False)

    def assign_research_direction(self) -> str:
        """研究方向由课程考试决定，科研系统不再自行分配。"""
        if self.player.research_direction:
            return f"你已有研究方向：{self.player.research_direction.value}"
        return "请先通过课程考试解锁科研方向。"

    def start_research(self) -> str:
        """开始科研（选择研究方向）"""
        if not self.can_start_research():
            return "请先通过课程考试解锁科研！"

        if not self.player.research_direction:
            return "尚未确定研究方向，请先通过课程考试。"

        return f"你开始跟随{self.player.relationships.get('导师', '导师')}进行{self.player.research_direction.value}..."

    def read_literature(self) -> str:
        """阅读文献获取idea（使用新判定系统）

        1. 先进行感知(SEN)判定决定阅读进度
        2. 达到100%时进行直觉(INT)判定决定idea创新值
        """
        if not self.can_start_research():
            return "请先通过课程考试解锁科研！"

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

    def generate_inspiration_idea(self) -> tuple[str, bool]:
        """通过灵感爆发生成idea，不影响文献阅读进度。

        Returns:
            (消息文本, 是否实际触发)
        """
        idea_result, _ = self._generate_idea_with_check(affect_literature_progress=False)
        return idea_result, not idea_result.startswith("【警告】")

    def _generate_idea_with_check(self, affect_literature_progress: bool = True) -> tuple[str, int]:
        """生成idea（使用INT判定决定创新值）

        创新值规则：
        - 普通成功：base + (INT-20)//10，截断到 9
        - 大成功：创新值 10（邪神级 idea，仅大成功出现）
        - 创新值 ≥9：异变增加（窥见真理的代价）
        - 灵感爆发复用同一逻辑，但不修改文献阅读进度

        Returns:
            (消息文本, 骰点值)
        """
        # 从池中获取基础创新值
        pool = IDEAS_POOL.get(self.player.research_direction, [])
        if not pool:
            return "【警告】当前研究方向没有可用idea池，无法生成idea。", 0

        # 进行INT直觉判定
        check_result, roll = ability_check(self.player, "INT")
        name, desc, base_innovation = random.choice(pool)

        if check_result == CheckResult.CRITICAL_SUCCESS:
            # 大成功：邪神级 idea（创新值 10）
            innovation = 10
            msg = f"【大成功·邪神级】你感觉你才思泉涌，想到了一个从未有过的天才想法！\n这个念头让你浑身发冷，仿佛有什么东西透过这个想法注视着你..."
        elif check_result in [CheckResult.EXTREME_SUCCESS, CheckResult.HARD_SUCCESS, CheckResult.SUCCESS]:
            # 成功：base + INT加成，截断到 9
            innovation = base_innovation + (self.player.INT - 20) // 10
            innovation = max(1, min(9, innovation))
            msg = f"【{check_result}】你冥思苦想，想到了一个不错的点子。"
        elif check_result == CheckResult.FAILURE:
            # 失败：不生成idea，进度回退
            if affect_literature_progress:
                self.literature_progress = random.randint(70, 80)
                return f"【失败】你未能理解这篇文章的核心思想，无法产生有效的idea。\n文献阅读进度回退到{self.literature_progress}%。", roll
            return "【失败】灵感转瞬即逝，你未能将它整理成有效的idea。", roll
        else:
            # 大失败：进度清零，异变值+0.05
            if affect_literature_progress:
                self.literature_progress = 0
            self.player.mutation += 0.05
            if affect_literature_progress:
                return f"【大失败】你的精神受到了冲击，感觉自己过往的学习就是一团灰尘...  \n文献阅读进度清零。\n【异变+0.05】", roll
            return "【大失败】你的灵感坍缩成无法名状的噪声，精神受到了冲击...\n【异变+0.05】", roll

        # 创建idea
        idea = Idea(name, desc, innovation, self.player.research_direction)
        self.ideas.append(idea)
        if affect_literature_progress:
            self.literature_progress = 0

        # 高创新值的异变代价（窥见真理）
        if self.mutation_system and innovation >= 9:
            mutation_msg = []
            self.mutation_system.apply_idea_mutation(self.player, innovation, mutation_msg.append)
            if mutation_msg:
                msg += "\n" + "\n".join(mutation_msg)

        msg += f"\n你获得了新的idea: {idea.name}\n{idea.description}\n创新值: {idea.innovation}/10"
        return msg, roll

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
        previous_status = idea.status
        self._refresh_idea_status(idea)
        if previous_status != IdeaStatus.MATURE and idea.status == IdeaStatus.MATURE:
            result_msg.append("idea已升级为成熟想法！")

        return "\n".join(result_msg)

    def write_draft(self, progress: int = 10) -> str:
        """撰写初稿"""
        block_reason = self.get_write_draft_block_reason()
        if block_reason:
            return block_reason

        if not self.current_paper:
            # 创建新论文
            mature_ideas = self._get_mature_ideas()
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
        block_reason = self.get_submit_paper_block_reason()
        if block_reason:
            return block_reason

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
                    self._refresh_idea_status(idea)
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
            result_msg.append("你感觉自己被学术界彻底否定了...但这或许是好事？")
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
