"""毕业论文系统"""
import random
from enum import Enum
from typing import Optional


class ThesisStage(Enum):
    """毕业论文阶段"""
    NOT_STARTED = "未开始"
    PROPOSAL = "开题报告"
    MIDTERM = "中期检查"
    BLIND_REVIEW = "盲审"
    SECOND_REVIEW = "二审"
    DEFENSE = "毕业答辩"
    COMPLETED = "已完成"


class GraduationThesis:
    """毕业论文"""

    def __init__(self, player):
        self.player = player
        self.stage = ThesisStage.NOT_STARTED
        self.progress = 0  # 各阶段进度 0-100
        self.title = ""
        self.passed = False

    def can_start(self) -> bool:
        """是否可以开始毕业论文"""
        return self.player.papers_published >= self.required_papers

    @property
    def required_papers(self) -> int:
        """开始毕业论文所需的小论文数量。"""
        return getattr(self.player, "graduation_required_papers", 1)

    def get_start_requirement_text(self) -> str:
        """获取开始毕业论文的要求文案。"""
        return f"需要至少{self.required_papers}篇小论文，当前{self.player.papers_published}篇"

    def start_thesis(self, title: str) -> str:
        """开始毕业论文"""
        if not self.can_start():
            return f"{self.get_start_requirement_text()}，才能开始毕业论文！"

        if self.stage != ThesisStage.NOT_STARTED:
            return "毕业论文已经开始！"

        self.title = title
        self.stage = ThesisStage.PROPOSAL
        self.progress = 0

        return f"你开始撰写毕业论文：{title}\n当前阶段：{self.stage.value}"

    def work_on_thesis(self, effort: int = 10) -> str:
        """推进毕业论文进度"""
        if self.stage == ThesisStage.NOT_STARTED:
            return "请先开始毕业论文！"

        if self.stage == ThesisStage.COMPLETED:
            return "毕业论文已完成！"

        # 进度增加
        progress_gain = random.randint(5, 15) + self.player.EDU // 10
        self.progress = min(100, self.progress + progress_gain)

        result = f"正在{self.stage.value}...\n进度: {self.progress}%"

        if self.progress >= 100:
            result += "\n" + self._advance_stage()

        return result

    def _advance_stage(self) -> str:
        """进入下一阶段"""
        if self.stage == ThesisStage.PROPOSAL:
            self.stage = ThesisStage.MIDTERM
            return "开题报告通过！进入中期检查阶段。"
        elif self.stage == ThesisStage.MIDTERM:
            # 中期检查后进入盲审
            self.stage = ThesisStage.BLIND_REVIEW
            return "中期检查通过！进入盲审阶段。"
        elif self.stage == ThesisStage.BLIND_REVIEW:
            # 盲审结果
            success_rate = 0.6 + self.player.reputation * 0.005 + self.player.papers_published * 0.1
            if random.random() < success_rate:
                self.stage = ThesisStage.SECOND_REVIEW
                self.progress = 0
                return "盲审通过！进入二审阶段。"
            else:
                self.progress = 50
                return "盲审未通过！需要修改。"
        elif self.stage == ThesisStage.SECOND_REVIEW:
            # 二审
            success_rate = 0.7 + self.player.reputation * 0.005
            if random.random() < success_rate:
                self.stage = ThesisStage.DEFENSE
                self.progress = 0
                return "二审通过！进入毕业答辩。"
            else:
                self.progress = 50
                return "二审需要修改！"
        elif self.stage == ThesisStage.DEFENSE:
            # 毕业答辩
            success_rate = 0.8 + self.player.INT * 0.01
            if random.random() < success_rate:
                self.stage = ThesisStage.COMPLETED
                self.passed = True
                return "恭喜！毕业论文答辩通过！你顺利毕业了！"
            else:
                self.progress = 50
                return "答辩未通过，需要修改论文。"
        return ""

    def get_status(self) -> str:
        """获取毕业论文状态"""
        if self.stage == ThesisStage.NOT_STARTED:
            status = "毕业论文：未开始"
            if not self.can_start():
                status += f"\n（{self.get_start_requirement_text()}）"
            return status
        else:
            return f"毕业论文：{self.stage.value}\n进度: {self.progress}%"
