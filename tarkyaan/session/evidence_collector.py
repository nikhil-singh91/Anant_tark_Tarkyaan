"""
Mastery Evidence Collector for Tarkyaan Phase 5.
Translates practice and assessment session evaluations into calibrated Bayesian evidence
and feeds directly into Phase 1 MasteryEngine.
"""

from __future__ import annotations

from typing import Dict, List, Optional
from tarkyaan.learner.learner_model import LearnerModel
from tarkyaan.learner.mastery_engine import MasteryEngine, MasteryUpdateResult
from tarkyaan.models.assessment import AssessmentResult
from tarkyaan.models.practice import AnswerEvaluation


class MasteryEvidenceCollector:
    """
    Translates learning session outcomes into Bayesian evidence scores.
    Reuses existing Phase 1 MasteryEngine to prevent duplicate mastery systems.
    """

    def __init__(self, learner_model: Optional[LearnerModel] = None) -> None:
        self.learner_model = learner_model

    def compute_composite_evidence(
        self,
        evaluations: List[AnswerEvaluation],
        total_hints_used: int = 0
    ) -> float:
        """
        Compute calibrated evidence score E in [0.0, 1.0] from a batch of evaluations.
        Accounts for correctness, reasoning quality, partial credit, and hint penalties.
        """
        if not evaluations:
            return 0.50  # Neutral prior if no empirical evidence

        total_weight = 0.0
        weighted_sum = 0.0

        for i, ev in enumerate(evaluations):
            # Recency weighting: later attempts have slightly higher weight
            recency_weight = 1.0 + (i * 0.1)
            # Combine accuracy and reasoning
            component_score = (ev.score * 0.60) + (ev.reasoning_quality * 0.40)
            weighted_sum += component_score * recency_weight
            total_weight += recency_weight

        raw_evidence = weighted_sum / max(1.0, total_weight)

        # Apply progressive hint discount (clamped to max 0.30 total deduction)
        hint_penalty = min(0.30, total_hints_used * 0.08)
        calibrated_e = max(0.10, min(1.0, raw_evidence - hint_penalty))
        return round(calibrated_e, 4)

    def apply_session_evidence_to_mastery(
        self,
        concept_id: str,
        evaluations: List[AnswerEvaluation],
        total_hints_used: int = 0,
        task_id: Optional[str] = None,
        learner_model: Optional[LearnerModel] = None
    ) -> Optional[AssessmentResult]:
        """
        Feed calibrated session evidence directly into LearnerModel.update_mastery_from_assessment.
        Returns the AssessmentResult containing prior and new mastery scores and tiers.
        """
        model = learner_model or self.learner_model
        if not model:
            return None

        evidence_score = self.compute_composite_evidence(evaluations, total_hints_used)

        # Extract identified misconceptions
        misconceptions: List[str] = []
        for ev in evaluations:
            misconceptions.extend(ev.detected_misconceptions)

        feedback_summary = (
            f"Session practice evidence score {evidence_score:.2f} based on "
            f"{len(evaluations)} attempts and {total_hints_used} hints."
        )

        return model.update_mastery_from_assessment(
            topic_id=concept_id,
            score=evidence_score,
            task_id=task_id,
            feedback=feedback_summary,
            identified_misconceptions=list(set(misconceptions))
        )
