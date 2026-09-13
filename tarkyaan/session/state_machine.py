"""
Session State Machine for Tarkyaan Phase 5.
Governs deterministic and adaptive state transitions across the pedagogical session lifecycle:
INITIALIZE -> RECALL -> TEACH -> CHECK -> PRACTICE -> ASSESS -> REVIEW -> COMPLETE.
"""

from __future__ import annotations

from typing import Dict, List, Set
from tarkyaan.models.enums import SessionStage, SessionStatus
from tarkyaan.models.session import StageTransitionRecord


class InvalidStageTransitionError(Exception):
    """Raised when an illegal stage transition is attempted."""
    pass


class SessionStateMachine:
    """
    Deterministic transition rules for learning session stages.
    Enforces sound pedagogical sequencing while enabling dynamic remediation loops.
    """

    # Legal forward and branch transitions between stages
    ALLOWED_TRANSITIONS: Dict[SessionStage, Set[SessionStage]] = {
        SessionStage.INITIALIZE: {SessionStage.RECALL, SessionStage.TEACH, SessionStage.COMPLETE},
        SessionStage.RECALL: {SessionStage.TEACH, SessionStage.PRACTICE, SessionStage.COMPLETE},
        SessionStage.TEACH: {SessionStage.CHECK, SessionStage.PRACTICE, SessionStage.COMPLETE},
        SessionStage.CHECK: {SessionStage.PRACTICE, SessionStage.TEACH, SessionStage.REVIEW, SessionStage.COMPLETE},
        SessionStage.PRACTICE: {SessionStage.ASSESS, SessionStage.TEACH, SessionStage.CHECK, SessionStage.REVIEW, SessionStage.COMPLETE},
        SessionStage.ASSESS: {SessionStage.REVIEW, SessionStage.PRACTICE, SessionStage.TEACH, SessionStage.COMPLETE},
        SessionStage.REVIEW: {SessionStage.COMPLETE, SessionStage.TEACH, SessionStage.PRACTICE},
        SessionStage.COMPLETE: set(),  # Terminal stage
    }

    @classmethod
    def can_transition(cls, current_stage: SessionStage, target_stage: SessionStage) -> bool:
        """Check whether a transition between stages is legally permitted."""
        allowed = cls.ALLOWED_TRANSITIONS.get(current_stage, set())
        return target_stage in allowed

    @classmethod
    def validate_transition(cls, current_stage: SessionStage, target_stage: SessionStage) -> None:
        """Validate transition, raising InvalidStageTransitionError if illegal."""
        if not cls.can_transition(current_stage, target_stage):
            raise InvalidStageTransitionError(
                f"Illegal session stage transition from {current_stage.value} to {target_stage.value}. "
                f"Allowed destinations: {[s.value for s in cls.ALLOWED_TRANSITIONS.get(current_stage, set())]}"
            )

    @classmethod
    def create_transition_record(
        cls,
        from_stage: SessionStage,
        to_stage: SessionStage,
        reason: str
    ) -> StageTransitionRecord:
        """Create an audit record of a validated stage transition."""
        cls.validate_transition(from_stage, to_stage)
        return StageTransitionRecord(
            from_stage=from_stage,
            to_stage=to_stage,
            reason=reason
        )
