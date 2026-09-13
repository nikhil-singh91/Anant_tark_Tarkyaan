"""
Teaching Engine for Tarkyaan Phase 5.
High-level orchestrator coordinating adaptive explanations, Socratic inquiries,
misconception-aware interventions, and prerequisite remediation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from tarkyaan.knowledge.prerequisite_graph import PrerequisiteDAG
from tarkyaan.learner.learner_model import LearnerModel
from tarkyaan.models.enums import ExplanationStyle, MasteryTier
from tarkyaan.models.learner import LearnerProfile
from tarkyaan.models.teaching import (
    ExplanationRequest,
    ExplanationResponse,
    MisconceptionIntervention,
    PrerequisiteRemediation,
    SocraticProbe,
)
from tarkyaan.providers.base import LLMProvider
from tarkyaan.teaching.explanation_engine import ExplanationEngine
from tarkyaan.teaching.misconception_tutor import MisconceptionTutor
from tarkyaan.teaching.prerequisite_tutor import PrerequisiteTutor
from tarkyaan.teaching.socratic_engine import SocraticEngine


class TeachingEngine:
    """
    Central pedagogical intelligence coordinator in Tarkyaan.
    Adapts explanation depth, asks Socratic questions, diagnoses misconceptions,
    and remediates prerequisite blockers.
    """

    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        dag: Optional[PrerequisiteDAG] = None,
        learner_model: Optional[LearnerModel] = None
    ) -> None:
        self.explanation_engine = ExplanationEngine(llm_provider=llm_provider)
        self.socratic_engine = SocraticEngine()
        self.misconception_tutor = MisconceptionTutor()
        self.prerequisite_tutor = PrerequisiteTutor(dag=dag, learner_model=learner_model)

    def explain_concept(
        self,
        concept_id: str,
        concept_name: Optional[str] = None,
        learner: Optional[LearnerProfile] = None,
        current_mastery: float = 0.0,
        style: Optional[ExplanationStyle] = None,
        resource_context: Optional[str] = None
    ) -> ExplanationResponse:
        """
        Generate an adaptive explanation calibrated to the learner's actual mastery level.
        """
        tier = MasteryTier.INTRODUCED
        if current_mastery >= 0.88:
            tier = MasteryTier.MASTERED
        elif current_mastery >= 0.70:
            tier = MasteryTier.COMPETENT
        elif current_mastery >= 0.40:
            tier = MasteryTier.PRACTICING

        # If user explicitly requested a style, use it; otherwise pick from tier
        effective_style = style
        if not effective_style:
            if tier in (MasteryTier.UNEXPLORED, MasteryTier.INTRODUCED):
                effective_style = ExplanationStyle.SIMPLE_ANALOGY
            elif tier == MasteryTier.PRACTICING:
                effective_style = ExplanationStyle.TECHNICAL
            else:
                effective_style = ExplanationStyle.DEEP_FORMAL

        request = ExplanationRequest(
            concept_id=concept_id,
            concept_name=concept_name or concept_id.replace("_", " ").title(),
            learner_id=learner.learner_id if learner else "learner_default",
            target_tier=tier,
            preferred_style=effective_style,
            resource_context=resource_context
        )
        return self.explanation_engine.explain(request)

    def probe_understanding(
        self,
        concept_id: str,
        concept_name: Optional[str] = None,
        probe_index: int = 0
    ) -> SocraticProbe:
        """Present a Socratic probe to check or deepen understanding."""
        return self.socratic_engine.generate_probe(
            concept_id=concept_id,
            concept_name=concept_name,
            probe_index=probe_index
        )

    def evaluate_socratic_response(
        self,
        probe: SocraticProbe,
        response_text: str
    ) -> Dict[str, Any]:
        """Evaluate learner answer to a Socratic probe."""
        return self.socratic_engine.evaluate_probe_response(probe, response_text)

    def remediate_misconception(
        self,
        concept_id: str,
        misconception_text: str
    ) -> MisconceptionIntervention:
        """Build a 5-step cognitive intervention targeting an observed misconception."""
        return self.misconception_tutor.generate_intervention(concept_id, misconception_text)

    def check_and_remediate_prerequisite(
        self,
        target_concept_id: str,
        target_concept_name: str,
        learner_model: Optional[LearnerModel] = None
    ) -> Optional[PrerequisiteRemediation]:
        """
        Check if an unmastered prerequisite is blocking progress.
        Returns remediation mini-lesson if blocked, None if clean to proceed.
        """
        weak_p = self.prerequisite_tutor.find_weak_prerequisite(target_concept_id, learner_model)
        if weak_p:
            return self.prerequisite_tutor.build_remediation(target_concept_id, target_concept_name, weak_p)
        return None
