"""
Topic Mastery and Curriculum Models.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, List, Optional
from pydantic import BaseModel, Field, model_validator

from tarkyaan.models.enums import MasteryTier


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Subject(BaseModel):
    """Parent domain subject containing individual curriculum topics."""
    subject_id: str = Field(..., description="e.g. 'dsa', 'machine_learning', 'discrete_math'")
    name: str = Field(..., min_length=2)
    domain: str = Field(default="Computer Science")
    description: Optional[str] = None


class Topic(BaseModel):
    """Curriculum concept node in the learning graph."""
    topic_id: str = Field(..., description="Unique concept slug, e.g. 'binary_search_rotated_array'")
    subject_id: str = Field(..., description="Parent subject identifier")
    name: str = Field(..., min_length=2)
    description: Optional[str] = None
    prerequisites: List[str] = Field(default_factory=list, description="List of topic_ids that must precede this topic")


class TopicMastery(BaseModel):
    """
    Epistemic state of a learner for a specific concept.
    """
    learner_id: str = Field(..., description="Foreign key reference to learner")
    topic_id: str = Field(..., description="Unique concept slug")
    subject_id: str = Field(default="general", description="Parent subject identifier")
    name: str = Field(default="", description="Display name of topic")

    @model_validator(mode="before")
    @classmethod
    def _default_name(cls, values: Any) -> Any:
        if isinstance(values, dict):
            if not values.get("name") and values.get("topic_id"):
                values["name"] = values["topic_id"].replace("_", " ").title()
        return values

    mastery_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Bayesian mastery probability M(c)")
    uncertainty: float = Field(default=1.0, ge=0.0, le=1.0, description="Epistemic uncertainty U(c)")
    tier: MasteryTier = Field(default=MasteryTier.UNEXPLORED)
    prerequisites: List[str] = Field(default_factory=list)
    stability_factor: float = Field(default=14.0, ge=1.0, description="Memory stability factor S_c (days) for retention decay")
    last_practiced: Optional[datetime] = None
    successful_recalls: int = Field(default=0, ge=0)
    failed_recalls: int = Field(default=0, ge=0)
    updated_at: datetime = Field(default_factory=_utc_now)
