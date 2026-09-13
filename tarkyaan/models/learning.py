"""
Learning Sessions, Tasks, Plans, Resources, and Progress Models.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from tarkyaan.models.enums import TaskStatus


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class LearningTask(BaseModel):
    """Atomic study unit within a session or study phase."""
    task_id: str = Field(default_factory=lambda: f"task_{uuid.uuid4().hex[:8]}")
    goal_id: Optional[str] = None
    title: str = Field(..., min_length=2)
    topic_id: str
    estimated_minutes: int = Field(default=30, ge=5, le=360)
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    completed_at: Optional[datetime] = None

    def complete(self) -> None:
        self.status = TaskStatus.COMPLETED
        self.completed_at = _utc_now()


class StudyPhase(BaseModel):
    """Milestone block grouping multiple learning tasks."""
    phase_id: str = Field(default_factory=lambda: f"phase_{uuid.uuid4().hex[:8]}")
    name: str = Field(..., min_length=2)
    milestone_order: int = Field(default=1)
    tasks: List[LearningTask] = Field(default_factory=list)
    is_completed: bool = Field(default=False)


class LearningPlan(BaseModel):
    """Curriculum roadmap tailored to a goal."""
    plan_id: str = Field(default_factory=lambda: f"plan_{uuid.uuid4().hex[:8]}")
    learner_id: str
    goal_id: str
    title: str
    phases: List[StudyPhase] = Field(default_factory=list)
    total_estimated_hours: float = Field(default=10.0, ge=0.5)
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)


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
    """Curated learning resource discovered or referenced for a topic."""
    resource_id: str = Field(default_factory=lambda: f"res_{uuid.uuid4().hex[:8]}")
    topic_id: str
    title: str
    url: str
    resource_type: str = Field(default="article", description="article, video, problem, doc")
    evaluation: Optional[ResourceEvaluationScore] = None
    recommended_order: int = 1


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
