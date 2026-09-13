"""
Teaching Models for Tarkyaan Phase 5.
Defines structured explanations, Socratic probes, misconception interventions,
and prerequisite remediation data contracts.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from tarkyaan.models.enums import ExplanationStyle, MasteryTier


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ExplanationRequest(BaseModel):
    """Input specification for generating an adaptive concept explanation."""
    concept_id: str
    concept_name: str
    learner_id: str
    target_tier: MasteryTier = MasteryTier.INTRODUCED
    preferred_style: ExplanationStyle = ExplanationStyle.CONCEPTUAL
    learner_level_description: str = "beginner"
    prior_knowledge: List[str] = Field(default_factory=list)
    active_gaps: List[str] = Field(default_factory=list)
    recent_misconceptions: List[str] = Field(default_factory=list)
    resource_context: Optional[str] = None


class ExplanationSection(BaseModel):
    """Discrete subsection of an educational explanation."""
    heading: str
    content: str
    code_snippet: Optional[str] = None
    analogy: Optional[str] = None
    diagram_ascii: Optional[str] = None


class ExplanationResponse(BaseModel):
    """Complete, pedagogically grounded response to an explanation request."""
    explanation_id: str = Field(default_factory=lambda: f"exp_{uuid.uuid4().hex[:8]}")
    concept_id: str
    concept_name: str
    style_applied: ExplanationStyle
    target_tier: MasteryTier
    summary: str
    sections: List[ExplanationSection] = Field(default_factory=list)
    analogies: List[str] = Field(default_factory=list)
    examples: List[str] = Field(default_factory=list)
    counterexamples: List[str] = Field(default_factory=list)
    key_invariants: List[str] = Field(default_factory=list)
    common_pitfalls: List[str] = Field(default_factory=list)
    verification_question: Optional[str] = None
    created_at: datetime = Field(default_factory=_utc_now)


class SocraticProbe(BaseModel):
    """Inquiry-based question designed to guide the learner toward insight."""
    probe_id: str = Field(default_factory=lambda: f"soc_{uuid.uuid4().hex[:8]}")
    concept_id: str
    probe_question: str
    pedagogical_intent: str
    target_insight: str
    expected_keywords: List[str] = Field(default_factory=list)
    followup_if_correct: str
    followup_if_struggling: str
    created_at: datetime = Field(default_factory=_utc_now)


class MisconceptionIntervention(BaseModel):
    """Targeted pedagogical response to correct a cognitive misconception."""
    intervention_id: str = Field(default_factory=lambda: f"misc_int_{uuid.uuid4().hex[:8]}")
    misconception_id: str
    concept_id: str
    misconception_description: str
    why_tempting: str
    flawed_mental_model: str
    correct_mental_model: str
    counterexample: str
    corrective_check_question: str
    expected_reasoning: str
    created_at: datetime = Field(default_factory=_utc_now)


class PrerequisiteRemediation(BaseModel):
    """Structured detour to teach a weak prerequisite before resuming target concept."""
    remediation_id: str = Field(default_factory=lambda: f"prereq_rem_{uuid.uuid4().hex[:8]}")
    target_concept_id: str
    target_concept_name: str
    prerequisite_concept_id: str
    prerequisite_concept_name: str
    reason_for_detour: str
    remediation_summary: str
    mini_check_question: str
    return_bridge: str
    created_at: datetime = Field(default_factory=_utc_now)
