"""
Practice and Assessment Models for Tarkyaan Phase 5.
Defines interactive practice questions, 5-tier progressive hints,
and multi-dimensional answer evaluations with reasoning analysis.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from tarkyaan.models.enums import HintLevel, PracticeQuestionType


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PracticeQuestion(BaseModel):
    """Structured question/exercise generated for practice or formative assessment."""
    question_id: str = Field(default_factory=lambda: f"pq_{uuid.uuid4().hex[:8]}")
    learner_id: str = ""
    session_id: Optional[str] = None
    concept_id: str
    concept_name: str = ""
    task_id: Optional[str] = None
    question_type: PracticeQuestionType
    difficulty: int = Field(default=2, ge=1, le=5)
    prompt: str
    code_context: Optional[str] = None
    options: List[str] = Field(default_factory=list)  # For MCQ
    expected_reasoning: str = ""
    evaluation_criteria: List[str] = Field(default_factory=list)
    hints: List[str] = Field(default_factory=list)  # 5 progressive hint strings (Anti-Answer-Dumping)
    solution_explanation: str = ""
    created_at: datetime = Field(default_factory=_utc_now)


class HintRequest(BaseModel):
    """Request for progressive pedagogical guidance."""
    question_id: str
    session_id: Optional[str] = None
    requested_level: HintLevel
    attempt_count: int = 0
    previous_answer: Optional[str] = None


class HintResponse(BaseModel):
    """Progressive hint delivery with strict anti-answer-dumping enforcement."""
    question_id: str
    hint_level: HintLevel
    hint_text: str
    remaining_hints: int
    is_final_hint: bool = False
    pedagogical_nudge: str = ""


class AnswerEvaluation(BaseModel):
    """
    Multidimensional evaluation of learner answer.
    Separates correctness from reasoning quality and partial conceptual understanding.
    """
    evaluation_id: str = Field(default_factory=lambda: f"eval_{uuid.uuid4().hex[:8]}")
    question_id: str
    concept_id: str
    learner_response: str
    is_correct: bool
    score: float = Field(default=0.0, ge=0.0, le=1.0)
    reasoning_quality: float = Field(default=0.0, ge=0.0, le=1.0)
    conceptual_understanding: float = Field(default=0.0, ge=0.0, le=1.0)
    partial_credit: bool = False
    detected_misconceptions: List[str] = Field(default_factory=list)
    feedback: str = ""
    suggested_action: str = Field(
        default="continue",
        description="continue, give_hint, revise_concept, increase_difficulty, decrease_difficulty"
    )
    evaluated_at: datetime = Field(default_factory=_utc_now)
