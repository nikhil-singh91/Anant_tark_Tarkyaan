"""
Diagnostic Assessment Models.
Defines schemas for diagnostic questions, dimensions, sessions, and reports.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from tarkyaan.models.enums import MasteryTier


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class QuestionType(str, Enum):
    """Pedagogical inquiry style for diagnostic probes."""
    CONCEPTUAL = "conceptual"
    WHY = "why"
    WHAT_IF = "what_if"
    TRACE = "trace"
    RECALL = "recall"
    APPLICATION = "application"
    DEBUGGING = "debugging"
    CODE_READING = "code_reading"
    CODE_WRITING = "code_writing"
    COMPARISON = "comparison"
    EDGE_CASE = "edge_case"
    TRANSFER = "transfer"


class DiagnosticDimension(str, Enum):
    """Cognitive depth levels targeted by a diagnostic probe."""
    EXPOSURE = "exposure"
    UNDERSTANDING = "understanding"
    RECALL = "recall"
    APPLICATION = "application"
    MASTERY = "mastery"


class DiagnosticSessionStatus(str, Enum):
    """Lifecycle states of an interactive diagnostic assessment session."""
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class DiagnosticQuestion(BaseModel):
    """
    A targeted diagnostic probe designed to evaluate understanding of a concept.
    """
    question_id: str = Field(default_factory=lambda: f"dq_{uuid.uuid4().hex[:8]}")
    concept_id: str = Field(..., description="Concept slug being evaluated")
    difficulty: int = Field(default=3, ge=1, le=5, description="1 (basic) to 5 (nuanced)")
    diagnostic_dimension: DiagnosticDimension = Field(default=DiagnosticDimension.UNDERSTANDING)
    question_type: QuestionType = Field(default=QuestionType.CONCEPTUAL)
    prompt: str = Field(..., min_length=5, description="The probe question text")
    expected_reasoning: str = Field(..., description="Key reasoning hallmarks expected in a correct response")
    prerequisite_concepts: List[str] = Field(default_factory=list)
    evaluation_rubric: Dict[str, Any] = Field(
        default_factory=dict,
        description="Rubric elements: keywords, anti_patterns, edge_cases, candidate_misconceptions"
    )
    created_at: datetime = Field(default_factory=_utc_now)


class DiagnosticSession(BaseModel):
    """
    An ongoing or completed Socratic diagnostic assessment session.
    """
    session_id: str = Field(default_factory=lambda: f"ds_{uuid.uuid4().hex[:8]}")
    learner_id: str = Field(..., description="Foreign key ensuring learner isolation")
    goal_id: Optional[str] = None
    target_concepts: List[str] = Field(default_factory=list)
    status: DiagnosticSessionStatus = Field(default=DiagnosticSessionStatus.CREATED)
    questions_asked: List[DiagnosticQuestion] = Field(default_factory=list)
    responses: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_records: List[Dict[str, Any]] = Field(default_factory=list)
    discovered_gap_ids: List[str] = Field(default_factory=list)
    discovered_misconception_ids: List[str] = Field(default_factory=list)
    mastery_deltas: Dict[str, float] = Field(default_factory=dict)
    max_questions: int = Field(default=8, ge=1, le=30)
    started_at: datetime = Field(default_factory=_utc_now)
    completed_at: Optional[datetime] = None

    def complete(self) -> None:
        self.status = DiagnosticSessionStatus.COMPLETED
        self.completed_at = _utc_now()

    def cancel(self) -> None:
        self.status = DiagnosticSessionStatus.CANCELLED
        self.completed_at = _utc_now()

    def pause(self) -> None:
        self.status = DiagnosticSessionStatus.PAUSED


class DiagnosticReport(BaseModel):
    """
    Comprehensive diagnostic assessment report synthesizing learner knowledge state,
    pinpointed prerequisite gaps, misconceptions, and learning needs.
    """
    report_id: str = Field(default_factory=lambda: f"dr_{uuid.uuid4().hex[:8]}")
    learner_id: str
    goal_id: Optional[str] = None
    session_id: str
    overall_confidence: float = Field(ge=0.0, le=1.0)
    concept_mastery_map: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Map of concept_id -> {score, tier, uncertainty, name}"
    )
    knowledge_gaps: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of detected gaps with severity and root cause"
    )
    detected_misconceptions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of observed cognitive misconceptions with confidence"
    )
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    summary_narrative: str = Field(default="")
    next_learning_priorities: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_utc_now)
