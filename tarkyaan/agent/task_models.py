"""
Agent Task Models and Schemas for Phase 7 Autonomous Task Engine.
Defines bounded tasks, verifiable steps, risk tiers, and execution decisions.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from tarkyaan.models.enums import AgentRiskLevel, AgentStepStatus, AgentTaskStatus


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TaskGoal(BaseModel):
    """Educational or assistance outcome requested by or planned for the learner."""
    goal_id: str = Field(default_factory=lambda: f"goal_{uuid.uuid4().hex[:8]}")
    description: str
    target_concept: Optional[str] = None
    success_criteria: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    risk_level: AgentRiskLevel = AgentRiskLevel.LOW


class VerificationResult(BaseModel):
    """Outcome of observing and verifying an action's postconditions."""
    is_verified: bool
    notes: str = ""
    evidence_observed: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class AgentStep(BaseModel):
    """An atomic, observable, verifiable action planned by the agent."""
    step_id: str = Field(default_factory=lambda: f"astep_{uuid.uuid4().hex[:8]}")
    task_id: str
    step_index: int = 1
    action: str
    capability_id: str
    description: str = ""
    parameters: Dict[str, Any] = Field(default_factory=dict)
    risk_level: AgentRiskLevel = AgentRiskLevel.LOW
    status: AgentStepStatus = AgentStepStatus.PENDING
    requires_confirmation: bool = False
    verification_criteria: str = ""
    retry_count: int = 0
    max_retries: int = 2
    result: Dict[str, Any] = Field(default_factory=dict)
    verification_status: str = "pending"
    verification_notes: str = ""
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class AgentDecision(BaseModel):
    """Traceable, explainable autonomous decision."""
    decision_id: str = Field(default_factory=lambda: f"dec_{uuid.uuid4().hex[:8]}")
    step_id: Optional[str] = None
    action_chosen: str
    rationale: str
    evidence: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 1.0
    alternatives_considered: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=_utc_now)


class AutonomousTask(BaseModel):
    """
    A bounded, multi-step autonomous task running under the Observe->Plan->Act->Verify loop.
    Enforces budget limits, cancellation, and step-by-step verification.
    """
    task_id: str = Field(default_factory=lambda: f"atask_{uuid.uuid4().hex[:8]}")
    learner_id: str
    goal: TaskGoal
    status: AgentTaskStatus = AgentTaskStatus.CREATED
    steps: List[AgentStep] = Field(default_factory=list)
    current_step_index: int = 0
    max_steps: int = 10
    timeout_seconds: int = 120
    is_cancelled: bool = False
    cancellation_reason: Optional[str] = None
    result_summary: str = ""
    created_at: datetime = Field(default_factory=_utc_now)
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def is_budget_exhausted(self) -> bool:
        """Check if maximum allowed steps were reached."""
        return self.current_step_index >= self.max_steps
