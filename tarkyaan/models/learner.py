"""
Learner Profile model representing personal background, preferences, and study budget.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List
from pydantic import BaseModel, Field

from tarkyaan.models.enums import AutonomyLevel


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class LearnerProfile(BaseModel):
    """
    Persistent profile of a learner in Tarkyaan.
    """
    learner_id: str = Field(
        default_factory=lambda: f"learner_{uuid.uuid4().hex[:12]}",
        description="Unique persistent identifier for the learner"
    )
    display_name: str = Field(default="Learner", min_length=1, max_length=100)
    primary_domain: str = Field(default="Computer Science / DSA", min_length=1)
    preferred_language: str = Field(default="C++", min_length=1)
    preferred_learning_style: str = Field(default="hands_on_practice", description="visual, hands_on_practice, theoretical, etc.")
    preferred_explanation_style: str = Field(default="first_principles_socratic", description="socratic, intuitive, analogy_rich, etc.")
    daily_time_budget_minutes: int = Field(default=120, ge=15, le=720)
    current_autonomy_level: AutonomyLevel = Field(default=AutonomyLevel.LEVEL_3)
    known_strengths: List[str] = Field(default_factory=list)
    known_weaknesses: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)
    last_active_at: datetime = Field(default_factory=_utc_now)

    def touch(self) -> None:
        """Update the last_active_at and updated_at timestamps to current UTC."""
        now = _utc_now()
        self.last_active_at = now
        self.updated_at = now
