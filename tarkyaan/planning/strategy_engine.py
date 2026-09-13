"""
Strategy Engine for Tarkyaan Planning Brain.
Selects optimal pedagogical learning strategies based on learner mastery state,
prerequisite health, gaps, and deadlines.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from tarkyaan.knowledge.prerequisite_graph import PrerequisiteDAG
from tarkyaan.models.enums import LearningStrategy, MasteryTier
from tarkyaan.models.gaps import KnowledgeGap
from tarkyaan.models.goals import LearningGoal
from tarkyaan.models.learner import LearnerProfile
from tarkyaan.models.mastery import TopicMastery


class StrategyDecision(BaseModel):
    """Pedagogical strategy selection with transparent reasoning."""
    strategy: LearningStrategy
    rationale: str
    primary_factors: List[str] = Field(default_factory=list)


class StrategyEngine:
    """
    Evaluates learner diagnostic state, prerequisites, and timeline to select
    the most effective curriculum strategy.
    """

    @classmethod
    def select_strategy(
        cls,
        goal: LearningGoal,
        learner: Optional[LearnerProfile] = None,
        mastery_map: Optional[Dict[str, TopicMastery]] = None,
        gaps: Optional[List[KnowledgeGap]] = None,
        dag: Optional[PrerequisiteDAG] = None,
        target_concept_ids: Optional[List[str]] = None
    ) -> StrategyDecision:
        """
        Determine the optimal LearningStrategy based on diagnostic factors.
        """
        masteries = mastery_map or {}
        active_gaps = [g for g in (gaps or []) if not g.resolved]
        targets = target_concept_ids or []
        factors: List[str] = []

        # 1. Timeline Check (Exam / Deadline urgency)
        if goal.deadline:
            now = datetime.now(timezone.utc)
            deadline = goal.deadline
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=timezone.utc)
            days_left = (deadline - now).total_seconds() / 86400.0
            if days_left <= 14.0:
                factors.append(f"Tight deadline approaching in {int(days_left)} days")
                return StrategyDecision(
                    strategy=LearningStrategy.EXAM_FOCUSED,
                    rationale="An impending deadline requires focusing strictly on high-yield, exam-critical topics and immediate practice.",
                    primary_factors=factors
                )

        # 2. Prerequisite Health Check
        blocking_prereqs: List[str] = []
        if dag and targets:
            for t in targets:
                if dag.has_concept(t):
                    blocks = dag.find_blocking_prerequisites(
                        t,
                        {cid: m.mastery_score for cid, m in masteries.items()},
                        competence_threshold=0.60
                    )
                    blocking_prereqs.extend(blocks)
            blocking_prereqs = list(dict.fromkeys(blocking_prereqs))  # Deduplicate

        if len(blocking_prereqs) >= 2:
            factors.append(f"{len(blocking_prereqs)} foundational prerequisites are below competence ({', '.join(blocking_prereqs[:3])})")
            return StrategyDecision(
                strategy=LearningStrategy.PREREQUISITE_FIRST,
                rationale="Several downstream target concepts depend on weak prerequisite foundations, so the roadmap begins by strengthening those root concepts first.",
                primary_factors=factors
            )

        # 3. Critical Gap Concentration Check
        critical_gaps = [g for g in active_gaps if g.severity.lower() in ("critical", "high")]
        prereqs_mastered = (len(blocking_prereqs) == 0)
        if critical_gaps and prereqs_mastered:
            factors.append(f"{len(critical_gaps)} high/critical severity gaps identified while foundational prerequisites are stable")
            return StrategyDecision(
                strategy=LearningStrategy.GAP_FIRST,
                rationale="Foundational prerequisites are already sound, allowing the plan to directly address high-severity knowledge gaps on the target concepts.",
                primary_factors=factors
            )

        # 4. Low Overall Baseline Check
        avg_mastery = (
            sum(m.mastery_score for m in masteries.values()) / len(masteries)
            if masteries else 0.0
        )
        if masteries and avg_mastery < 0.25:
            factors.append(f"Low overall baseline mastery ({avg_mastery:.2f}) across candidate topics")
            return StrategyDecision(
                strategy=LearningStrategy.FOUNDATION_FIRST,
                rationale="The learner is at an introductory stage across the domain; the roadmap prioritizes step-by-step conceptual foundations before advanced problem solving.",
                primary_factors=factors
            )

        # 5. Conceptual Understanding vs Application Check
        competent_count = sum(1 for m in masteries.values() if m.tier in (MasteryTier.COMPETENT, MasteryTier.PRACTICING))
        if competent_count >= max(2, len(targets)):
            factors.append(f"Demonstrated conceptual grasp across {competent_count} topics; requires practical synthesis")
            return StrategyDecision(
                strategy=LearningStrategy.PRACTICE_HEAVY,
                rationale="Foundational concepts are understood; the roadmap focuses on deliberate problem solving, edge case debugging, and algorithmic synthesis.",
                primary_factors=factors
            )

        # 6. Default: Balanced
        factors.append("Standard balanced progression across exposure, understanding, and application")
        return StrategyDecision(
            strategy=LearningStrategy.BALANCED,
            rationale="A balanced pedagogical strategy combining conceptual instruction with structured recall and incremental problem-solving practice.",
            primary_factors=factors
        )
