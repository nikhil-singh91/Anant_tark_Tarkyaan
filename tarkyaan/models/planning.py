"""
Planning Models for Tarkyaan.
Defines LearningPlan, StudyPhase, LearningTask, Milestone, PlanExplanation,
WorkloadEstimate, and PlanValidationResult.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator

from tarkyaan.models.enums import (
    LearningStrategy,
    MilestoneStatus,
    PlanStatus,
    PlanValidationStatus,
    TaskStatus,
    TaskType,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class LearningTask(BaseModel):
    """
    Actionable pedagogical study or practice unit within a study phase.
    """
    task_id: str = Field(default_factory=lambda: f"task_{uuid.uuid4().hex[:8]}")
    plan_id: Optional[str] = None
    phase_id: Optional[str] = None
    learner_id: Optional[str] = None
    goal_id: Optional[str] = None
    topic_id: str = Field(default="")
    concept_id: str = Field(default="")
    title: str = Field(..., min_length=2)
    description: str = Field(default="")
    task_type: TaskType = Field(default=TaskType.PRACTICE)
    objective: str = Field(default="")
    difficulty: int = Field(default=2, ge=1, le=5)
    estimated_minutes: int = Field(default=30, ge=5, le=360)
    priority: float = Field(default=1.0, ge=0.0)
    prerequisite_task_ids: List[str] = Field(default_factory=list)
    prerequisite_concept_ids: List[str] = Field(default_factory=list)
    expected_evidence: str = Field(default="")
    completion_criteria: List[str] = Field(default_factory=list)
    mastery_target: float = Field(default=0.70, ge=0.0, le=1.0)
    task_order: int = Field(default=1, ge=1)
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    rationale: str = Field(default="")
    resource_ids: List[str] = Field(default_factory=list, description="Clean Phase 4 resource extension point")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    completed_at: Optional[datetime] = None

    @model_validator(mode="before")
    @classmethod
    def _sync_concept_topic(cls, values: Any) -> Any:
        if isinstance(values, dict):
            # Sync topic_id and concept_id if one is provided
            t_id = values.get("topic_id")
            c_id = values.get("concept_id")
            if c_id and not t_id:
                values["topic_id"] = c_id
            elif t_id and not c_id:
                values["concept_id"] = t_id
            elif not t_id and not c_id:
                values["topic_id"] = "general"
                values["concept_id"] = "general"
        return values

    def complete(self) -> None:
        self.status = TaskStatus.COMPLETED
        self.completed_at = _utc_now()


class StudyPhase(BaseModel):
    """
    Coherent milestone block grouping multiple actionable tasks toward a sub-objective.
    """
    phase_id: str = Field(default_factory=lambda: f"phase_{uuid.uuid4().hex[:8]}")
    plan_id: Optional[str] = None
    name: str = Field(default="", description="Phase display name")
    title: str = Field(default="", min_length=0)
    objective: str = Field(default="")
    concepts: List[str] = Field(default_factory=list)
    prerequisite_phase_ids: List[str] = Field(default_factory=list)
    task_ids: List[str] = Field(default_factory=list)
    tasks: List[LearningTask] = Field(default_factory=list)
    estimated_minutes: int = Field(default=0, ge=0)
    milestone_order: int = Field(default=1, ge=1)
    phase_order: int = Field(default=1, ge=1)
    completion_criteria: List[str] = Field(default_factory=list)
    status: str = Field(default="pending")
    is_completed: bool = Field(default=False)

    @model_validator(mode="before")
    @classmethod
    def _sync_title_name(cls, values: Any) -> Any:
        if isinstance(values, dict):
            name = values.get("name", "")
            title = values.get("title", "")
            if name and not title:
                values["title"] = name
            elif title and not name:
                values["name"] = title
            elif not name and not title:
                values["name"] = "Phase"
                values["title"] = "Phase"
        return values


class Milestone(BaseModel):
    """
    Measurable checkpoint representing concrete mastery or competency attainment.
    """
    milestone_id: str = Field(default_factory=lambda: f"ms_{uuid.uuid4().hex[:8]}")
    plan_id: Optional[str] = None
    title: str = Field(..., min_length=2)
    objective: str = Field(default="")
    required_task_ids: List[str] = Field(default_factory=list)
    required_concepts: List[str] = Field(default_factory=list)
    completion_criteria: List[str] = Field(default_factory=list)
    status: MilestoneStatus = Field(default=MilestoneStatus.PENDING)
    milestone_order: int = Field(default=1, ge=1)
    target_date: Optional[datetime] = None
    achieved_at: Optional[datetime] = None


class PlanExplanation(BaseModel):
    """
    Structured, transparent rationale explaining why the plan was synthesized as it was.
    """
    summary: str = Field(default="")
    goal_relevance: str = Field(default="")
    strengths_acknowledged: List[str] = Field(default_factory=list)
    prioritized_gaps: List[Dict[str, Any]] = Field(default_factory=list)
    deferred_topics: List[Dict[str, Any]] = Field(default_factory=list)
    prerequisite_rationale: List[str] = Field(default_factory=list)
    strategy_rationale: str = Field(default="")
    workload_rationale: str = Field(default="")


class WorkloadEstimate(BaseModel):
    """
    Realistic study workload pacing calculations and capacity warning metrics.
    """
    total_minutes: int = Field(default=0, ge=0)
    total_hours: float = Field(default=0.0, ge=0.0)
    estimated_sessions: int = Field(default=0, ge=0)
    daily_minutes: float = Field(default=0.0, ge=0.0)
    weekly_hours: float = Field(default=0.0, ge=0.0)
    target_days: int = Field(default=1, ge=1)
    is_overloaded: bool = Field(default=False)
    overload_reason: Optional[str] = None


class PlanValidationResult(BaseModel):
    """
    Deterministic plan validation outcome with explicit errors and warnings.
    """
    is_valid: bool = Field(default=True)
    status: PlanValidationStatus = Field(default=PlanValidationStatus.VALID)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class LearningPlan(BaseModel):
    """
    Curriculum roadmap tailored to a learner's goal, state, gaps, and prerequisites.
    """
    plan_id: str = Field(default_factory=lambda: f"plan_{uuid.uuid4().hex[:8]}")
    learner_id: str
    goal_id: str
    title: str = Field(..., min_length=2)
    description: str = Field(default="")
    objective: str = Field(default="")
    status: PlanStatus = Field(default=PlanStatus.PROPOSED)
    strategy: LearningStrategy = Field(default=LearningStrategy.BALANCED)
    version: int = Field(default=1, ge=1)
    parent_plan_id: Optional[str] = None
    revision_reason: Optional[str] = None
    phases: List[StudyPhase] = Field(default_factory=list)
    milestones: List[Milestone] = Field(default_factory=list)
    tasks: List[LearningTask] = Field(default_factory=list)
    dependencies: Dict[str, List[str]] = Field(default_factory=dict)
    assumptions: List[str] = Field(default_factory=list)
    expected_outcomes: List[str] = Field(default_factory=list)
    validation_status: PlanValidationStatus = Field(default=PlanValidationStatus.VALID)
    provenance: Dict[str, Any] = Field(default_factory=dict)
    explanation: Optional[PlanExplanation] = None
    total_estimated_hours: float = Field(default=10.0, ge=0.0)
    estimated_total_minutes: int = Field(default=600, ge=0)
    priority: int = Field(default=3, ge=1, le=5)
    start_date: Optional[datetime] = None
    target_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)
