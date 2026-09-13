"""
Priority Engine for Tarkyaan Planning Brain.
Computes deterministic, explainable priority rankings for candidate concepts,
knowledge gaps, and prerequisite deficits.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from tarkyaan.knowledge.prerequisite_graph import PrerequisiteDAG
from tarkyaan.models.gaps import KnowledgeGap
from tarkyaan.models.goals import LearningGoal
from tarkyaan.models.mastery import TopicMastery


class ConceptPriorityScore(BaseModel):
    """
    Transparent, explainable scoring breakdown for a prioritized concept or gap.
    """
    concept_id: str
    final_score: float = Field(ge=0.0, le=100.0)
    goal_relevance: float = Field(ge=0.0, le=1.0)
    prerequisite_impact: float = Field(ge=0.0, le=1.0)
    severity_score: float = Field(ge=0.0, le=1.0)
    downstream_dependents_count: int = Field(ge=0)
    weakness_score: float = Field(ge=0.0, le=1.0)
    uncertainty: float = Field(ge=0.0, le=1.0)
    rationale: str = Field(default="")


class PriorityEngine:
    """
    Ranks concepts and knowledge gaps mathematically using a transparent, multi-factor scoring model.
    """

    # Weights summing to 100.0
    WEIGHT_GOAL_RELEVANCE: float = 25.0
    WEIGHT_PREREQ_IMPACT: float = 25.0
    WEIGHT_SEVERITY: float = 20.0
    WEIGHT_WEAKNESS: float = 15.0
    WEIGHT_UNCERTAINTY: float = 10.0
    WEIGHT_DOWNSTREAM: float = 5.0

    SEVERITY_WEIGHTS = {
        "critical": 1.0,
        "high": 0.8,
        "medium": 0.5,
        "low": 0.2
    }

    @classmethod
    def rank_concepts(
        cls,
        candidate_concept_ids: List[str],
        goal: LearningGoal,
        mastery_map: Optional[Dict[str, TopicMastery]] = None,
        gaps: Optional[List[KnowledgeGap]] = None,
        dag: Optional[PrerequisiteDAG] = None,
        target_concept_ids: Optional[List[str]] = None
    ) -> List[ConceptPriorityScore]:
        """
        Score and sort concepts in descending order of pedagogical urgency.
        """
        masteries = mastery_map or {}
        active_gaps = {g.concept_id: g for g in (gaps or []) if not g.resolved}
        target_set = set(target_concept_ids or [])
        goal_text = f"{goal.title} {goal.target_outcome}".lower()

        scores: List[ConceptPriorityScore] = []

        for cid in candidate_concept_ids:
            # 1. Goal Relevance (0.0 to 1.0)
            is_direct_target = cid in target_set or cid.lower() in goal_text
            relevance = 1.0 if is_direct_target else 0.65

            # 2. Downstream Dependents & Prerequisite Impact
            dependents_count = 0
            prereq_impact = 0.2
            if dag and dag.has_concept(cid):
                dependents = dag.get_dependents(cid)
                dependents_count = len(dependents)
                descendants = dag.get_descendants(cid)
                # If this concept blocks an actual target concept, impact is highest
                blocks_target = any(d in target_set for d in descendants)
                if blocks_target:
                    prereq_impact = 1.0
                elif dependents_count > 2:
                    prereq_impact = 0.8
                elif dependents_count > 0:
                    prereq_impact = 0.5
                else:
                    prereq_impact = 0.2

            # 3. Severity Score from active gaps (0.0 to 1.0)
            gap = active_gaps.get(cid)
            severity_score = 0.1
            severity_label = "low"
            if gap:
                severity_label = gap.severity.lower()
                severity_score = cls.SEVERITY_WEIGHTS.get(severity_label, 0.5)

            # 4. Weakness Score (1.0 - mastery score)
            m_obj = masteries.get(cid)
            mastery_score = m_obj.mastery_score if m_obj else 0.0
            uncertainty = m_obj.uncertainty if m_obj else 0.8
            weakness_score = max(0.0, 1.0 - mastery_score)

            # 5. Calculate composite final score (0 - 100)
            downstream_normalized = min(1.0, dependents_count / 5.0)

            score_val = (
                cls.WEIGHT_GOAL_RELEVANCE * relevance
                + cls.WEIGHT_PREREQ_IMPACT * prereq_impact
                + cls.WEIGHT_SEVERITY * severity_score
                + cls.WEIGHT_WEAKNESS * weakness_score
                + cls.WEIGHT_UNCERTAINTY * uncertainty
                + cls.WEIGHT_DOWNSTREAM * downstream_normalized
            )
            final_score = round(min(100.0, max(0.0, score_val)), 2)

            # 6. Compose clear, human-readable rationale
            rationale_parts = []
            if gap:
                rationale_parts.append(f"has a {severity_label}-severity gap")
            if prereq_impact >= 0.8:
                rationale_parts.append(f"blocks {dependents_count} downstream concepts")
            if is_direct_target:
                rationale_parts.append("is directly required for your goal")
            elif weakness_score > 0.6:
                rationale_parts.append(f"current mastery is low ({round(mastery_score, 2)})")

            rationale_summary = ", and ".join(rationale_parts) if rationale_parts else "is scheduled as a foundational topic"
            full_rationale = f"'{cid}' is prioritized (score: {final_score:.1f}) because it {rationale_summary}."

            scores.append(ConceptPriorityScore(
                concept_id=cid,
                final_score=final_score,
                goal_relevance=round(relevance, 2),
                prerequisite_impact=round(prereq_impact, 2),
                severity_score=round(severity_score, 2),
                downstream_dependents_count=dependents_count,
                weakness_score=round(weakness_score, 2),
                uncertainty=round(uncertainty, 2),
                rationale=full_rationale
            ))

        # Sort descending by final score
        scores.sort(key=lambda s: s.final_score, reverse=True)
        return scores
