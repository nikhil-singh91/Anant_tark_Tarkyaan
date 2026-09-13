"""
Learning Sessions, Tasks, Plans, Resources, and Progress Models.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from tarkyaan.models.enums import TaskStatus
from tarkyaan.models.planning import (
    LearningPlan,
    LearningTask,
    Milestone,
    PlanExplanation,
    PlanValidationResult,
    StudyPhase,
    WorkloadEstimate,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class LearningSession(BaseModel):
    """
    Episodic record of a focused study or practice session.
    """
    session_id: str = Field(default_factory=lambda: f"sess_{uuid.uuid4().hex[:8]}")
    learner_id: str
    goal_id: Optional[str] = None
    start_time: datetime = Field(default_factory=_utc_now)
    end_time: Optional[datetime] = None
    duration_minutes: float = Field(default=0.0, ge=0.0)
    topics_covered: List[str] = Field(default_factory=list)
    tasks_completed: List[str] = Field(default_factory=list)
    notes: str = Field(default="")

    def end_session(self, notes: str = "") -> None:
        now = _utc_now()
        self.end_time = now
        elapsed = (now - self.start_time).total_seconds() / 60.0
        self.duration_minutes = round(max(1.0, elapsed), 1)
        if notes:
            self.notes = notes


class ResourceEvaluationScore(BaseModel):
    """Composite scoring of an educational resource."""
    relevance: float = Field(ge=0, le=10)
    clarity: float = Field(ge=0, le=10)
    credibility: float = Field(ge=0, le=10)
    level_alignment: float = Field(ge=0, le=10)
    completeness: float = Field(ge=0, le=10)
    time_efficiency: float = Field(ge=0, le=10)
    composite_score: float = Field(ge=0, le=100)


class LearningResource(BaseModel):
    """Curated learning resource discovered or referenced for a topic or task."""
    resource_id: str = Field(default_factory=lambda: f"res_{uuid.uuid4().hex[:8]}")
    topic_id: str = ""
    title: str
    url: str
    resource_type: str = Field(default="article", description="article, video, coding_problem, official_docs, tutorial, etc.")
    domain: str = ""
    provider: str = "mock"
    author: Optional[str] = None
    description: str = ""
    concept_ids: List[str] = Field(default_factory=list)
    task_ids: List[str] = Field(default_factory=list)
    difficulty: int = Field(default=2, ge=1, le=5)
    language: str = "en"
    duration_minutes: Optional[int] = None
    published_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    relevance_score: float = Field(default=0.5, ge=0.0, le=1.0)
    authority_score: float = Field(default=0.5, ge=0.0, le=1.0)
    quality_score: float = Field(default=0.5, ge=0.0, le=1.0)
    learner_fit_score: float = Field(default=0.5, ge=0.0, le=1.0)
    freshness_score: float = Field(default=0.5, ge=0.0, le=1.0)
    usefulness_score: float = Field(default=0.5, ge=0.0, le=1.0)
    overall_score: float = Field(default=0.5, ge=0.0, le=1.0)
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    provenance: Optional[Any] = None  # ResourceProvenance
    evaluation_notes: List[str] = Field(default_factory=list)
    recommended_order: int = 1
    discovered_at: datetime = Field(default_factory=_utc_now)
    last_verified_at: Optional[datetime] = None
    evaluation: Optional[ResourceEvaluationScore] = None



class ReplanningRecord(BaseModel):
    """Audit log of dynamic roadmap adaptation."""
    replan_id: str = Field(default_factory=lambda: f"replan_{uuid.uuid4().hex[:8]}")
    plan_id: str
    trigger_reason: str
    changes_summary: str
    timestamp: datetime = Field(default_factory=_utc_now)


class ProgressSnapshot(BaseModel):
    """Periodic statistical summary of learner progress."""
    snapshot_id: str = Field(default_factory=lambda: f"snap_{uuid.uuid4().hex[:8]}")
    learner_id: str
    timestamp: datetime = Field(default_factory=_utc_now)
    topics_mastered_count: int = 0
    topics_practicing_count: int = 0
    active_gaps_count: int = 0
    average_mastery: float = Field(default=0.0, ge=0.0, le=1.0)
    velocity_topics_per_week: float = Field(default=0.0, ge=0.0)
