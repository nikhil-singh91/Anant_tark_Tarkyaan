"""
Models for Autonomous Task Execution, Bounded Steps, and Audit Records.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from tarkyaan.safety.policies import RiskLevel


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TaskExecutionStatus(str, Enum):
    """Lifecycle statuses of an autonomous task or step."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    TIMED_OUT = "timed_out"


class TaskStep(BaseModel):
    """An atomic, bounded execution step within an autonomous task."""
    step_id: str = Field(default_factory=lambda: f"step_{uuid.uuid4().hex[:8]}")
    step_order: int = Field(default=1, ge=1)
    capability_name: str
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    risk_level: RiskLevel = Field(default=RiskLevel.LOW)
    status: TaskExecutionStatus = Field(default=TaskExecutionStatus.PENDING)
    output: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class StepResult(BaseModel):
    """Outcome and verification status of a single step execution."""
    success: bool
    data: Dict[str, Any] = Field(default_factory=dict)
    message: str = ""
    is_verified: bool = False
    error: Optional[str] = None


class AutonomousTask(BaseModel):
    """
    Structured autonomous task plan composed of bounded, verifiable steps.
    """
    task_id: str = Field(default_factory=lambda: f"atask_{uuid.uuid4().hex[:8]}")
    learner_id: str
    title: str
    goal: str
    steps: List[TaskStep] = Field(default_factory=list)
    max_steps: int = Field(default=10, ge=1, le=50)
    timeout_seconds: int = Field(default=120, ge=1, le=600)
    status: TaskExecutionStatus = Field(default=TaskExecutionStatus.PENDING)
    current_step_index: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=_utc_now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    audit_trail: List[Dict[str, Any]] = Field(default_factory=list)


class TaskAuditRecord(BaseModel):
    """Audit entry recording an action, parameter signature, and outcome."""
    record_id: str = Field(default_factory=lambda: f"aud_{uuid.uuid4().hex[:8]}")
    task_id: str
    step_id: str
    capability_name: str
    risk_level: RiskLevel
    status: TaskExecutionStatus
    parameters_summary: str
    timestamp: datetime = Field(default_factory=_utc_now)
