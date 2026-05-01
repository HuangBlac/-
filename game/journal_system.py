"""JournalSystem - 论文期刊分层与非常规审稿系统.

All gameplay values are data-driven from JSON config files.
"""

import json
import random
from pathlib import Path
from typing import Optional, Tuple

from .research import Paper


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))


class JournalSystem:
    """Manuscript tier evaluation, submission review, and anomaly events."""

    _TIERS_PATH = Path(__file__).parent / "data" / "journal_tiers.json"
    _ANOMALY_PATH = Path(__file__).parent / "data" / "review_anomaly_events.json"

    def __init__(self, player, event_flow_controller=None, mutation_system=None):
        self.player = player
        self.event_flow_controller = event_flow_controller
        self.mutation_system = mutation_system
        self._tiers = self._load_json(self._TIERS_PATH)
        self._anomaly_config = self._load_json(self._ANOMALY_PATH)
        self._next_submission_reputation_bonus = 0

    @staticmethod
    def _load_json(path: Path) -> dict:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    # ------------------------------------------------------------------ #
    #  Scoring
    # ------------------------------------------------------------------ #

    @staticmethod
    def calculate_innovation_score(paper: Paper) -> int:
        """Return innovation score (0-100) from paper ideas."""
        if not paper or not paper.ideas:
            return 0
        avg = sum(i.innovation for i in paper.ideas) / len(paper.ideas)
        return _clamp(round(avg * 10), 0, 100)

    @staticmethod
    def calculate_experiment_score(paper: Paper) -> int:
        """Return experiment score (0-100) from result quantity, quality, and balance."""
        if not paper or not paper.ideas:
            return 0

        all_results = [r for idea in paper.ideas for r in idea.experiment_results]
        valid_results = [r for r in all_results if (r.theory + r.experiment + r.depth) >= 3]
        valid_count = len(valid_results)
        if valid_count == 0:
            return 0

        avg_power = sum(r.theory + r.experiment + r.depth for r in valid_results) / valid_count

        quantity_score = _clamp(24 + (valid_count - 3) * 8, 0, 40)
        quality_score = _clamp(round(avg_power / 15 * 60), 0, 60)

        total_theory = sum(r.theory for r in valid_results)
        total_experiment = sum(r.experiment for r in valid_results)
        total_depth = sum(r.depth for r in valid_results)
        balance_bonus = 5 if min(total_theory, total_experiment, total_depth) >= valid_count * 2 else 0

        return _clamp(quantity_score + quality_score + balance_bonus, 0, 100)

    def calculate_reputation_score(self) -> int:
        """Return reputation score (0-100) from papers, advisor, and social history."""
        paper_reputation = _clamp(getattr(self.player, "reputation", 0), 0, 80)

        advisor = getattr(self.player, "advisor", None)
        if advisor is None:
            advisor_bonus = -5
        elif getattr(advisor, "is_nyarrothotep", False):
            advisor_bonus = 25
        else:
            av = getattr(advisor, "ability_value", 0)
            if av <= 40:
                advisor_bonus = 0
            elif av <= 60:
                advisor_bonus = 5
            elif av <= 80:
                advisor_bonus = 10
            elif av <= 94:
                advisor_bonus = 15
            else:
                advisor_bonus = 20

        # Social system compatibility: default to 0 until social system is fully implemented.
        social_bonus = _clamp(
            getattr(self.player, "successful_social_events", 0) * 2
            + getattr(self.player, "academic_network_level", 0) * 5,
            0,
            25,
        )

        return _clamp(paper_reputation + advisor_bonus + social_bonus, 0, 100)

    @staticmethod
    def calculate_tier_score(innovation_score: int, experiment_score: int, reputation_score: int) -> int:
        """Return composite tier score (0-100)."""
        return _clamp(
            round(innovation_score * 0.42 + experiment_score * 0.38 + reputation_score * 0.20),
            0,
            100,
        )

    def get_score_breakdown(self, paper: Paper) -> dict:
        """Return all scores for a paper."""
        innovation = self.calculate_innovation_score(paper)
        experiment = self.calculate_experiment_score(paper)
        reputation = self.calculate_reputation_score()
        tier = self.calculate_tier_score(innovation, experiment, reputation)
        return {
            "innovation_score": innovation,
            "experiment_score": experiment,
            "reputation_score": reputation,
            "tier_score": tier,
        }

    # ------------------------------------------------------------------ #
    #  Submission gating
    # ------------------------------------------------------------------ #

    def can_submit_to(
        self,
        tier_id: str,
        tier_score: Optional[int] = None,
        innovation_score: Optional[int] = None,
        experiment_score: Optional[int] = None,
        reputation_score: Optional[int] = None,
    ) -> Tuple[bool, str]:
        """Return (is_allowed, reason) for submitting to *tier_id*."""
        tiers = self._tiers.get("tiers", {})
        tier = tiers.get(tier_id)
        if tier is None:
            return False, f"未知期刊层级: {tier_id}"

        if tier_score is None or innovation_score is None or experiment_score is None or reputation_score is None:
            return False, "评分尚未计算"

        min_sub = self._tiers.get("min_submission_score", 30)
        if tier_score < min_sub:
            return False, "论文尚不足以形成可发表成果，请继续完善研究。"

        if innovation_score < tier.get("min_innovation", 0):
            return False, f"创新值未达到{tier['name']}要求。"
        if experiment_score < tier.get("min_experiment_score", 0):
            return False, f"实验质量未达到{tier['name']}要求。"
        if reputation_score < tier.get("min_reputation_score", 0):
            return False, f"学术声望未达到{tier['name']}要求。"

        return True, ""

    # ------------------------------------------------------------------ #
    #  Review outcome
    # ------------------------------------------------------------------ #

    def review_paper(
        self,
        tier_id: str,
        tier_score: Optional[int] = None,
        innovation_score: Optional[int] = None,
        experiment_score: Optional[int] = None,
        reputation_score: Optional[int] = None,
    ) -> dict:
        """Run the review process and return the outcome dict."""
        tiers = self._tiers.get("tiers", {})
        tier = tiers.get(tier_id)
        if tier is None:
            return {"outcome": "error", "message": f"未知期刊层级: {tier_id}"}

        if tier_score is None:
            return {"outcome": "error", "message": "评分尚未计算"}

        can, reason = self.can_submit_to(tier_id, tier_score, innovation_score, experiment_score, reputation_score)
        if not can:
            return {"outcome": "desk_reject", "message": reason}

        target_threshold = tier["tier_score_threshold"]

        soc = getattr(self.player, "SOC", 50)
        edu = getattr(self.player, "EDU", 50)
        social_review_bonus = round(((soc + edu) // 2 - 55) * 0.25)
        review_roll = random.randint(-10, 10)
        review_score = tier_score + social_review_bonus + review_roll
        score_gap = review_score - target_threshold

        # Desk reject if hard requirements are not met and gap is large enough
        hard_met = True
        if innovation_score is not None and innovation_score < tier.get("min_innovation", 0):
            hard_met = False
        if experiment_score is not None and experiment_score < tier.get("min_experiment_score", 0):
            hard_met = False
        if reputation_score is not None and reputation_score < tier.get("min_reputation_score", 0):
            hard_met = False

        if not hard_met and score_gap <= -15:
            return {
                "outcome": "desk_reject",
                "tier_id": tier_id,
                "review_score": review_score,
                "score_gap": score_gap,
                "message": f"【Desk Reject】{tier['name']}认为论文不符合基本门槛，未进入审稿流程。",
            }

        thresholds = self._tiers.get("outcome_thresholds", {})
        if score_gap >= thresholds.get("direct_accept", 10):
            outcome = "direct_accept"
            message = f"【直接接受】{tier['name']}接受了你的论文！"
        elif score_gap >= thresholds.get("minor_revision", 0):
            outcome = "minor_revision"
            message = f"【小修后接受】{tier['name']}要求小修，修回后即可发表。"
        elif score_gap >= thresholds.get("downgrade", -10):
            outcome = "downgrade"
            message = f"【降档接受】{tier['name']}拒稿，但建议转投低层级期刊。"
        elif score_gap >= thresholds.get("major_revision", -20):
            outcome = "major_revision"
            message = f"【大修】{tier['name']}要求大修，需要补充实验或重写。"
        else:
            outcome = "reject"
            message = f"【拒稿】{tier['name']}拒绝了你的论文。"

        return {
            "outcome": outcome,
            "tier_id": tier_id,
            "review_score": review_score,
            "score_gap": score_gap,
            "message": message,
        }

    # ------------------------------------------------------------------ #
    #  Anomaly events
    # ------------------------------------------------------------------ #

    def get_anomaly_chance(self, tier_id: str, paper: Paper) -> float:
        """Return the probability (0.0-1.0) of triggering a review anomaly."""
        tiers = self._tiers.get("tiers", {})
        tier = tiers.get(tier_id)
        if tier is None:
            return 0.0

        base = tier.get("base_anomaly_chance", 0.0)
        mods = self._anomaly_config.get("anomaly_chance_modifiers", {})

        avg_innovation = 0.0
        if paper and paper.ideas:
            avg_innovation = sum(i.innovation for i in paper.ideas) / len(paper.ideas)

        innovation_bonus = mods.get("innovation_bonus", {})
        inv_bonus = innovation_bonus.get("value", 0.0) if avg_innovation >= innovation_bonus.get("threshold", 999) else 0.0

        outer_god_bonus = 0.0
        if paper and paper.ideas:
            target_dir = mods.get("outer_god_bonus", {}).get("direction", "")
            if any(str(i.direction) == target_dir or i.direction.name == target_dir for i in paper.ideas):
                outer_god_bonus = mods.get("outer_god_bonus", {}).get("value", 0.0)

        mutation = getattr(self.player, "mutation", 0.0)
        mut_bonus = min(mods.get("mutation_cap", 0.1), mutation * mods.get("mutation_multiplier", 0.05))

        advisor = getattr(self.player, "advisor", None)
        adv_bonus = 0.0
        if advisor and getattr(advisor, "is_eldritch", False):
            adv_bonus = mods.get("eldritch_advisor_bonus", 0.08)

        max_chance = mods.get("max_anomaly_chance", 0.45)
        return min(max_chance, base + inv_bonus + outer_god_bonus + mut_bonus + adv_bonus)

    def roll_anomaly_event(self, tier_id: str, paper: Paper) -> Optional[dict]:
        """Roll for and return an anomaly event dict, or None if no anomaly."""
        chance = self.get_anomaly_chance(tier_id, paper)
        if random.random() >= chance:
            return None

        events = self._anomaly_config.get("events", [])
        eligible = []
        for event in events:
            cond = event.get("conditions", {})
            min_tier = cond.get("min_tier")
            if min_tier and self._tier_rank(tier_id) < self._tier_rank(min_tier):
                continue
            eligible.append(event)

        if not eligible:
            return None

        weights = [e.get("weight", 1) for e in eligible]
        total = sum(weights)
        if total <= 0:
            return None

        pick = random.randint(1, total)
        cumulative = 0
        for event, w in zip(eligible, weights):
            cumulative += w
            if pick <= cumulative:
                return event
        return eligible[-1]

    @staticmethod
    def _tier_rank(tier_id: str) -> int:
        order = {"school": 0, "water": 1, "good": 2, "disciplinary": 3, "top": 4}
        return order.get(tier_id, -1)

    # ------------------------------------------------------------------ #
    #  Submission entry point
    # ------------------------------------------------------------------ #

    def submit_paper(self, paper: Paper, tier_id: Optional[str] = None) -> str:
        """Submit *paper* to *tier_id* and return player-facing result text."""
        if paper is None:
            return "没有可投稿的论文。"

        breakdown = self.get_score_breakdown(paper)
        tier_score = breakdown["tier_score"]
        innovation = breakdown["innovation_score"]
        experiment = breakdown["experiment_score"]
        reputation = breakdown["reputation_score"]

        if tier_id is None:
            return (
                f"论文评分:\n"
                f"  创新分: {innovation}/100\n"
                f"  实验分: {experiment}/100\n"
                f"  声望分: {reputation}/100\n"
                f"  综合分: {tier_score}/100\n"
                f"请输入目标期刊层级 (top/disciplinary/good/water/school)"
            )

        can, reason = self.can_submit_to(tier_id, tier_score, innovation, experiment, reputation)
        if not can:
            return reason

        result = self.review_paper(tier_id, tier_score, innovation, experiment, reputation)
        outcome = result["outcome"]
        tier_name = self._tiers.get("tiers", {}).get(tier_id, {}).get("name", tier_id)

        lines = [result["message"]]

        if outcome in ("direct_accept", "minor_revision"):
            self._apply_publication(tier_id, tier_name)
            anomaly = self.roll_anomaly_event(tier_id, paper)
            if anomaly and self.event_flow_controller:
                # Caller is responsible for pushing the event through the flow controller.
                result["anomaly_event"] = anomaly
            lines.append(self._format_publication_rewards())

        elif outcome == "downgrade":
            downgrade_tier = self._get_downgrade_tier(tier_id)
            if downgrade_tier:
                lines.append(f"论文被转投至{downgrade_tier['name']}。")
                self._apply_publication(downgrade_tier["id"], downgrade_tier["name"])
                lines.append(self._format_publication_rewards())
            else:
                lines.append("连学报都无法发表，论文被拒稿。")
                self._apply_rejection_sanity_loss()

        elif outcome == "major_revision":
            paper.draft_progress = random.randint(30, 60)
            paper.is_complete = False
            for idea in paper.ideas[:2]:
                if idea.experiment_results:
                    idea.experiment_results.pop()
            lines.append("论文进度回退，部分实验结果被移除。")

        elif outcome in ("reject", "desk_reject"):
            self._apply_rejection_sanity_loss()

        return "\n".join(lines)

    def _get_downgrade_tier(self, tier_id: str) -> Optional[dict]:
        order = ["top", "disciplinary", "good", "water", "school"]
        idx = order.index(tier_id)
        if idx + 1 >= len(order):
            return None
        next_id = order[idx + 1]
        tier = self._tiers.get("tiers", {}).get(next_id)
        if tier is None:
            return None
        tier = dict(tier)
        tier["id"] = next_id
        return tier

    def _apply_publication(self, tier_id: str, tier_name: str) -> None:
        tiers = self._tiers.get("tiers", {})
        tier = tiers.get(tier_id, {})

        rep_gain = random.randint(tier.get("reputation_gain_min", 0), tier.get("reputation_gain_max", 0))
        san_gain = random.randint(tier.get("sanity_restore_min", 0), tier.get("sanity_restore_max", 0))

        rep_gain += self._next_submission_reputation_bonus
        self._next_submission_reputation_bonus = 0

        self.player.reputation += rep_gain
        if san_gain:
            self.player.change_sanity(san_gain)

        # Track tier-specific paper count
        if not hasattr(self.player, "papers_by_tier"):
            self.player.papers_by_tier = {"top": 0, "disciplinary": 0, "good": 0, "water": 0, "school": 0}
        self.player.papers_by_tier[tier_id] = self.player.papers_by_tier.get(tier_id, 0) + 1
        self.player.papers_published += 1

        self._last_publication = {
            "tier_id": tier_id,
            "tier_name": tier_name,
            "reputation_gain": rep_gain,
            "sanity_gain": san_gain,
        }

    def _apply_rejection_sanity_loss(self) -> None:
        san_loss = random.randint(5, 10)
        self.player.change_sanity(-san_loss)

    def _format_publication_rewards(self) -> str:
        pub = getattr(self, "_last_publication", None)
        if pub is None:
            return ""
        lines = [f"发表论文+1（{pub['tier_name']}）"]
        lines.append(f"声望 +{pub['reputation_gain']}（累计 {self.player.reputation}）")
        if pub.get("sanity_gain", 0):
            lines.append(f"理智 +{pub['sanity_gain']}")
        return "\n".join(lines)
