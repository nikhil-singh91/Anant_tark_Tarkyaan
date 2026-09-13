"""
Assessment Evidence and Diagnostic Result Models.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field

from tarkyaan.models.enums import MasteryTier


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AssessmentResult(BaseModel):
    """
    Empirical evidence collected from a quiz, problem, or diagnostic probe.
    """
    assessment_id: str = Field(default_factory=lambda: f"assess_{uuid.uuid4().hex[:8]}")
    learner_id: str = Field(..., description="Foreign key reference to learner")
    topic_id: str = Field(..., description="Target concept evaluated")
    task_id: Optional[str] = None
    score: float = Field(..., ge=0.0, le=1.0, description="Empirical performance score E in [0.0, 1.0]")
    prior_mastery: float = Field(default=0.0, ge=0.0, le=1.0)
    new_mastery: float = Field(default=0.0, ge=0.0, le=1.0)
    prior_uncertainty: float = Field(default=1.0, ge=0.0, le=1.0)
    new_uncertainty: float = Field(default=0.75, ge=0.0, le=1.0)
    evaluated_tier: MasteryTier = Field(default=MasteryTier.INTRODUCED)
    identified_misconceptions: List[str] = Field(default_factory=list)
    feedback_notes: str = Field(default="")
    evaluated_at: datetime = Field(default_factory=_utc_now)
