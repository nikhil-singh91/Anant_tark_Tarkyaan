"""
Learning Goal model representing target achievements, deadlines, and study pace.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class LearningGoal(BaseModel):
    """
    Structured learning objective with deadline and time allocation.
    """
    goal_id: str = Field(default_factory=lambda: f"goal_{uuid.uuid4().hex[:8]}")
    learner_id: str = Field(..., description="Foreign key reference to learner")
    title: str = Field(..., min_length=2, max_length=200, description="e.g. 'Master DSA for Placement Interviews'")
    target_outcome: str = Field(..., min_length=2, description="Target competency or benchmark")
    deadline: Optional[datetime] = None
    priority: int = Field(default=3, ge=1, le=5, description="1 (lowest) to 5 (highest)")
    target_level: str = Field(default="competent", description="introduced, practicing, competent, mastered")
    daily_hours: float = Field(default=2.0, ge=0.5, le=10.0)
    milestones: List[str] = Field(default_factory=list)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)
    completed_at: Optional[datetime] = None

    def mark_completed(self) -> None:
        """Mark the goal as completed."""
        now = _utc_now()
        self.is_active = False
        self.updated_at = now
        self.completed_at = now
