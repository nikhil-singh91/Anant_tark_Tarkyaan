"""
Session Models for Tarkyaan Phase 5.
Defines dialogue turn records, stage transition logs, and post-session summaries.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from tarkyaan.models.enums import SessionStage, SessionStatus


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SessionInteraction(BaseModel):
    """Single turn or event log within a learning session."""
    interaction_id: str = Field(default_factory=lambda: f"turn_{uuid.uuid4().hex[:8]}")
    session_id: str
    turn_index: int = 0
    speaker: str  # "learner", "companion", "system"
    stage: SessionStage
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=_utc_now)


class StageTransitionRecord(BaseModel):
    """Log of state transitions in the session state machine."""
    from_stage: SessionStage
    to_stage: SessionStage
    reason: str
    timestamp: datetime = Field(default_factory=_utc_now)


class MasteryDeltaRecord(BaseModel):
    """Quantified delta in concept mastery resulting from session activities."""
    concept_id: str
    prior_mastery: float
    new_mastery: float
    delta: float
    evidence_count: int


class SessionSummary(BaseModel):
    """Structured, honest educational synthesis produced upon session completion."""
    session_id: str
    learner_id: str
    objective: str
    duration_minutes: float
    stages_traversed: List[SessionStage] = Field(default_factory=list)
    concepts_covered: List[str] = Field(default_factory=list)
    questions_attempted: int = 0
    questions_correct: int = 0
    hints_requested: int = 0
    strengths_demonstrated: List[str] = Field(default_factory=list)
    remaining_weaknesses: List[str] = Field(default_factory=list)
    misconceptions_addressed: List[str] = Field(default_factory=list)
    mastery_changes: List[MasteryDeltaRecord] = Field(default_factory=list)
    recommended_next_task_id: Optional[str] = None
    recommended_next_action: str = ""
    created_at: datetime = Field(default_factory=_utc_now)
