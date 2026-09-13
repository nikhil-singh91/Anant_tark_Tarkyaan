"""
Knowledge Gap and Misconception Models.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field

from tarkyaan.models.enums import MisconceptionCategory


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class KnowledgeGap(BaseModel):
    """
    Identified prerequisite deficit blocking forward progress.
    """
    gap_id: str = Field(default_factory=lambda: f"gap_{uuid.uuid4().hex[:8]}")
    learner_id: str = Field(..., description="Foreign key reference to learner")
    concept_id: str = Field(..., description="Deficient prerequisite topic_id")
    blocking_topic_id: str = Field(..., description="Target topic blocked by this deficit")
    severity: str = Field(default="high", description="low, medium, high, critical")
    diagnostic_evidence: str = Field(..., min_length=5)
    detected_at: datetime = Field(default_factory=_utc_now)
    resolved: bool = Field(default=False)
    resolved_at: Optional[datetime] = None

    def resolve(self) -> None:
        """Mark the knowledge gap as resolved."""
        self.resolved = True
        self.resolved_at = _utc_now()


class MisconceptionRecord(BaseModel):
    """
    Cataloged cognitive error or conceptual flaw observed during practice.
    """
    record_id: str = Field(default_factory=lambda: f"misc_{uuid.uuid4().hex[:8]}")
    learner_id: str = Field(..., description="Foreign key reference to learner")
    topic_id: str = Field(..., description="Related concept topic_id")
    category: MisconceptionCategory = Field(default=MisconceptionCategory.CONCEPTUAL)
    description: str = Field(..., min_length=5)
    observed_code_snippet: Optional[str] = None
    corrective_action_taken: str = Field(default="")
    timestamp: datetime = Field(default_factory=_utc_now)
