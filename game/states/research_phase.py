"""Research phase state."""

from game.action_def import ActionDef
from game.research import IdeaStatus
from game.state_machine import GameState, StateResult
from game.ui_messages import ui_text


class ResearchPhaseState(GameState):
    """State for research actions after courses unlock research."""

    @property
    def state_id(self) -> str:
        return "research.phase"

    def get_available_actions(self, ctx) -> list:
        if not ctx.player.research_direction:
            return []

        actions = [
            ActionDef("1", "摸鱼", "偷闲片刻，恢复理智"),
            ActionDef("2", "阅读文献", "获取创新idea"),
        ]
        raw_ideas = [idea for idea in ctx.research_system.ideas if idea.status == IdeaStatus.RAW]
        if raw_ideas:
            actions.append(ActionDef("E", "评估Idea", f"评估{len(raw_ideas)}个新idea"))

        actions.extend([
            ActionDef("3", "实验验证", "进行实验获得结果"),
            ActionDef("4", "撰写论文", "改写论文初稿"),
            ActionDef("5", "投稿", "提交论文发表"),
        ])
        return actions

    def get_blocking_message(self, ctx, action: str):
        """Return a no-cost validation error, or None when the action can run."""
        action = action.lower()
        if action == "3":
            return ctx.research_system.get_experiment_block_reason()
        if action == "4":
            return ctx.research_system.get_write_draft_block_reason()
        if action == "5":
            return ctx.research_system.get_submit_paper_block_reason()
        return None

    def handle_action(self, ctx, action: str) -> StateResult:
        action = action.lower()

        if action == "1":
            return StateResult(self._do_semester_entertainment(ctx))
        if action == "2":
            if not ctx.player.research_direction:
                return StateResult("尚未确定研究方向，请先通过课程考试。")
            return StateResult(ctx.research_system.read_literature())
        if action == "3":
            return StateResult(self._do_experiment(ctx))
        if action == "4":
            return StateResult(ctx.research_system.write_draft())
        if action == "5":
            return StateResult(ctx.research_system.submit_paper())
        if action == "e":
            return StateResult(push_state="research.idea_decision")

        return StateResult(ui_text("invalid_action"))

    def on_enter(self, ctx, from_state=None) -> str:
        if from_state and from_state.startswith("course."):
            return (
                f"{ui_text('phase_research')}\n"
                f"{ui_text('research_action_hint')}"
            )
        return ""

    def _do_experiment(self, ctx) -> str:
        block_reason = ctx.research_system.get_experiment_block_reason()
        if block_reason:
            return block_reason

        ideas = [idea for idea in ctx.research_system.ideas if idea.status == IdeaStatus.PRELIMINARY]
        idea = ideas[0]
        idea_index = ctx.research_system.ideas.index(idea)
        return ctx.research_system.conduct_experiment(idea_index)

    def _do_semester_entertainment(self, ctx) -> str:
        """Handle research-time slacking through entertainment events."""
        event_system = ctx.event_system
        if not event_system:
            ctx.player.change_sanity(1)
            return "你发了一会呆，感觉稍微好了一点。\n理智+1"

        event = ctx.advisor_system.get_random_entertainment_event(ctx.player, event_system)
        if not event:
            ctx.player.change_sanity(1)
            return "你发了一会呆，感觉稍微好了一点。\n理智+1"

        return ctx.trigger_event(
            event,
            "摸鱼",
            next_stage="after_action",
            post_apply=lambda selected_event, choice_id=None: self._after_semester_entertainment_event(
                ctx,
                selected_event,
                choice_id,
            ),
        )

    def _after_semester_entertainment_event(self, ctx, event: dict, choice_id: str = None) -> str:
        """Apply advisor-related adjustments after entertainment events resolve."""
        return ctx.advisor_system.apply_entertainment_adjustments(
            ctx.player,
            event,
            ctx.event_system,
            choice_id,
        )


class IdeaDecisionState(GameState):
    """Research substate for evaluating raw ideas."""

    @property
    def state_id(self) -> str:
        return "research.idea_decision"

    def get_available_actions(self, ctx) -> list:
        return [ActionDef("input", "输入Idea决策", "格式如：1a、1d、1i", costs_action_point=False)]

    def on_enter(self, ctx, from_state=None) -> str:
        raw_ideas = self._raw_ideas(ctx)
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
        return menu + "\n" + ui_text("prompt_idea_decision")

    def handle_action(self, ctx, action: str) -> StateResult:
        raw_ideas = self._raw_ideas(ctx)
        if not raw_ideas:
            return StateResult("没有需要评估的idea！", pop_state=True)

        decision = action.strip().lower()
        if len(decision) < 2:
            return StateResult(
                "无效输入！格式如：1a（评估第1个idea，接受为初步想法）\na=接受，d=丢弃，i=改进",
                prompt=ui_text("prompt_idea_decision"),
            )

        try:
            index = int(decision[:-1]) - 1
            choice = decision[-1]
        except ValueError:
            return StateResult(
                "无效输入！格式如：1a（评估第1个idea）\na=接受，d=丢弃，i=改进",
                prompt=ui_text("prompt_idea_decision"),
            )

        if index < 0 or index >= len(raw_ideas):
            return StateResult(
                f"无效序号！有效范围：1-{len(raw_ideas)}",
                prompt=ui_text("prompt_idea_decision"),
            )

        decision_map = {"a": "accept", "d": "discard", "i": "improve"}
        if choice not in decision_map:
            return StateResult(
                "无效决定！a=接受，d=丢弃，i=改进",
                prompt=ui_text("prompt_idea_decision"),
            )

        idea = raw_ideas[index]
        result = ctx.research_system.evaluate_idea(
            ctx.research_system.ideas.index(idea),
            decision_map[choice],
        )
        return StateResult(result, pop_state=True)

    def _raw_ideas(self, ctx):
        return [idea for idea in ctx.research_system.ideas if idea.status == IdeaStatus.RAW]
