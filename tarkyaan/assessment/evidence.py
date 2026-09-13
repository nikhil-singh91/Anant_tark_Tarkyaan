"""
Diagnostic Evidence Architecture.
Provides explicit separation between verified observed user evidence
and model-inferred evaluations.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from tarkyaan.models.enums import EpistemicStatus, MasteryTier


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ObservedEvidence(BaseModel):
    """
    Ground-truth factual observation of what the learner submitted.
    Zero hallucination or subjective interpretation.
    """
    evidence_id: str = Field(default_factory=lambda: f"ev_{uuid.uuid4().hex[:8]}")
    question_id: str
    concept_id: str
    raw_response_text: str
    submitted_code: Optional[str] = None
    time_taken_seconds: float = Field(default=0.0, ge=0.0)
    epistemic_status: EpistemicStatus = Field(default=EpistemicStatus.FACT)
    observed_at: datetime = Field(default_factory=_utc_now)


class InferredEvaluation(BaseModel):
    """
    Analytical model interpretation of the observed evidence.
    Always carries confidence metrics and critique notes.
    """
    evaluation_id: str = Field(default_factory=lambda: f"eval_{uuid.uuid4().hex[:8]}")
    correctness: float = Field(..., ge=0.0, le=1.0, description="Accuracy of factual content")
    reasoning_quality: float = Field(default=0.5, ge=0.0, le=1.0, description="Soundness of logical thought")
    application_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Execution/implementation validity")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0, description="Certainty of this evaluation")
    evaluated_tier: MasteryTier = Field(default=MasteryTier.PRACTICING)
    detected_errors: List[str] = Field(default_factory=list)
    candidate_misconceptions: List[str] = Field(default_factory=list)
    reasoning_critique: str = Field(default="")
    epistemic_status: EpistemicStatus = Field(default=EpistemicStatus.INFERENCE)
    inferred_at: datetime = Field(default_factory=_utc_now)


class DiagnosticEvidence(BaseModel):
    """
    Unified record combining factual observation and model inference.
    Provides composite score for ingestion into MasteryEngine.
    """
    evidence_id: str = Field(default_factory=lambda: f"diag_ev_{uuid.uuid4().hex[:8]}")
    learner_id: str
    session_id: Optional[str] = None
    concept_id: str
    observation: ObservedEvidence
    evaluation: InferredEvaluation

    @property
    def composite_score(self) -> float:
        """
        Calculates weighted composite score E in [0.0, 1.0] for the MasteryEngine.
        Formula: 0.5 * correctness + 0.3 * reasoning_quality + 0.2 * application_score
        """
        score = (
            0.50 * self.evaluation.correctness +
            0.30 * self.evaluation.reasoning_quality +
            0.20 * self.evaluation.application_score
        )
        return round(max(0.0, min(1.0, score)), 4)
