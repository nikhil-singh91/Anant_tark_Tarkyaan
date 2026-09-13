"""
Tarkyaan Learning Decision Engine — Phase 6.
Explainable autonomous decision-making layer over learner evidence.

Every decision Tarkyaan makes is:
- Evidence-grounded (references specific signals)
- Explainable (rationale in plain language)
- Auditable (stored as a structured LearningDecision)
- Conservative (prefers minimal intervention)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from tarkyaan.models.enums import HealthStatus, ReplanningTrigger


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Decision Types
# ---------------------------------------------------------------------------

class DecisionType(str, Enum):
    """Classification of autonomous decisions Tarkyaan can make."""
    CONTINUE = "continue"             # No action needed; learning is healthy
    SCHEDULE_REVIEW = "schedule_review"  # Inject spaced-repetition tasks
    REPLAN = "replan"                 # Trigger full curriculum replanning
    ADJUST_DIFFICULTY = "adjust_difficulty"  # Recommend difficulty change
    SUGGEST_BREAK = "suggest_break"   # Suggest rest/break for overloaded learner
    CHANGE_STRATEGY = "change_strategy"  # Switch learning strategy
    FLAG_FOR_ATTENTION = "flag_for_attention"  # Requires learner/system attention
    MILESTONE_REVIEW = "milestone_review"  # Trigger milestone reassessment


class DecisionConfidence(str, Enum):
    """Confidence level of a decision based on evidence quality."""
    HIGH = "high"       # Strong, converging evidence from multiple signals
    MEDIUM = "medium"   # Moderate evidence; decision is reasonable
    LOW = "low"         # Weak or single-signal evidence; proceed cautiously


# ---------------------------------------------------------------------------
# LearningDecision Model
# ---------------------------------------------------------------------------

class LearningDecision(BaseModel):
    """
    A structured, explainable autonomous decision produced by LearningDecisionEngine.
    Every decision carries its evidence, rationale, and confidence level.
    """
    decision_id: str = Field(default_factory=lambda: f"dec_{uuid.uuid4().hex[:8]}")
    learner_id: str
    decision_type: DecisionType
    confidence: DecisionConfidence
    rationale: str                                   # Plain-language explanation
    evidence_signals: List[str] = Field(default_factory=list)   # Supporting evidence
    triggers: List[ReplanningTrigger] = Field(default_factory=list)
    health_status: HealthStatus = HealthStatus.HEALTHY
    parameters: Dict[str, Any] = Field(default_factory=dict)  # Decision-specific context
    decided_at: datetime = Field(default_factory=_utc_now)
    is_autonomous: bool = True                       # True = Tarkyaan decided autonomously


# ---------------------------------------------------------------------------
# LearningDecisionEngine
# ---------------------------------------------------------------------------

class LearningDecisionEngine:
    """
    Explainable autonomous decision engine.

    Takes a LearningHealthReport and produces a structured LearningDecision
    with explicit rationale, confidence, and evidence references.

    Design principles:
    - Minimal intervention: prefer CONTINUE over REPLAN where possible
    - Explainability: every decision is traceable to specific evidence signals
    - Confidence-weighted: weak evidence → LOW confidence → less aggressive action
    - Audit trail: decisions are structured Pydantic models (caller can persist them)
    """

    # Thresholds for decision escalation
    REPLAN_MIN_TRIGGERS: int = 1         # Any actionable trigger can trigger replan
    HIGH_CONFIDENCE_SIGNALS: int = 2     # >= 2 signals = HIGH confidence
    MEDIUM_CONFIDENCE_SIGNALS: int = 1   # 1 signal = MEDIUM confidence

    @classmethod
    def decide(
        cls,
        learner_id: str,
        health_status: HealthStatus,
        triggers: List[ReplanningTrigger],
        signals: List[str],
        plan_id: Optional[str] = None,
        extra_context: Optional[Dict[str, Any]] = None,
    ) -> LearningDecision:
        """
        Make the primary autonomous decision from health evidence.

        Decision priority chain:
        REGRESSION / OVERLOAD → REPLAN (critical)
        STALL (long) → REPLAN
        GAP_PERSISTENCE → REPLAN
        PLATEAU → CHANGE_STRATEGY
        VELOCITY_DROP (mild) → SCHEDULE_REVIEW
        HEALTHY → CONTINUE

        :param learner_id:    Learner the decision is for
        :param health_status: Classified HealthStatus
        :param triggers:      All fired ReplanningTriggers
        :param signals:       Human-readable evidence strings
        :param plan_id:       Active plan ID (optional, added to parameters)
        :param extra_context: Additional context to include
        :return: LearningDecision with rationale and confidence
        """
        # Determine confidence level
        n_signals = len(signals)
        if n_signals >= cls.HIGH_CONFIDENCE_SIGNALS:
            confidence = DecisionConfidence.HIGH
        elif n_signals >= cls.MEDIUM_CONFIDENCE_SIGNALS:
            confidence = DecisionConfidence.MEDIUM
        else:
            confidence = DecisionConfidence.LOW

        params: Dict[str, Any] = {}
        if plan_id:
            params["plan_id"] = plan_id
        if extra_context:
            params.update(extra_context)

        # Decision logic
        decision_type, rationale = cls._select_decision(
            health_status=health_status,
            triggers=triggers,
            signals=signals,
            confidence=confidence,
        )

        return LearningDecision(
            learner_id=learner_id,
            decision_type=decision_type,
            confidence=confidence,
            rationale=rationale,
            evidence_signals=signals,
            triggers=triggers,
            health_status=health_status,
            parameters=params,
        )

    @classmethod
    def _select_decision(
        cls,
        health_status: HealthStatus,
        triggers: List[ReplanningTrigger],
        signals: List[str],
        confidence: DecisionConfidence,
    ) -> tuple[DecisionType, str]:
        """
        Select decision type and generate rationale based on priority chain.
        Returns (DecisionType, rationale_string).
        """
        trigger_set = set(triggers)

        # 1. Critical: Regression always replans
        if ReplanningTrigger.REGRESSION in trigger_set:
            return (
                DecisionType.REPLAN,
                f"Mastery regression detected ({confidence.value} confidence). "
                f"Curriculum requires restructuring to address declining mastery. "
                f"Evidence: {signals[0] if signals else 'regression signal'}."
            )

        # 2. Critical: Overload → suggest break + replan
        if ReplanningTrigger.OVERLOAD in trigger_set:
            return (
                DecisionType.REPLAN,
                f"Difficulty overload detected ({confidence.value} confidence). "
                f"Plan will be restructured with reduced difficulty progression. "
                f"Evidence: {signals[0] if signals else 'overload signal'}."
            )

        # 3. Stall → replan with recall-heavy strategy
        if ReplanningTrigger.STALL in trigger_set:
            return (
                DecisionType.REPLAN,
                f"Learning stall detected ({confidence.value} confidence). "
                f"Replanning with recall-first strategy to break the stall. "
                f"Evidence: {signals[0] if signals else 'stall signal'}."
            )

        # 4. Persistent gaps → replan to re-address gaps
        if ReplanningTrigger.GAP_PERSISTENCE in trigger_set:
            return (
                DecisionType.REPLAN,
                f"Persistent knowledge gaps unresolved ({confidence.value} confidence). "
                f"Plan restructured to re-target gap concepts before advancing. "
                f"Evidence: {signals[0] if signals else 'gap persistence signal'}."
            )

        # 5. Misconception loop → replan with corrective tasks
        if ReplanningTrigger.MISCONCEPTION_LOOP in trigger_set:
            return (
                DecisionType.REPLAN,
                f"Recurring misconception loop detected ({confidence.value} confidence). "
                f"Corrective tasks injected; plan restructured to address root errors. "
                f"Evidence: {signals[0] if signals else 'misconception loop signal'}."
            )

        # 6. Plateau → change strategy (not full replan yet)
        if ReplanningTrigger.PLATEAU in trigger_set:
            return (
                DecisionType.CHANGE_STRATEGY,
                f"Mastery plateau detected ({confidence.value} confidence). "
                f"Recommend shifting to more varied practice types (apply, debug, compare). "
                f"Evidence: {signals[0] if signals else 'plateau signal'}."
            )

        # 7. Velocity drop → schedule reviews
        if ReplanningTrigger.VELOCITY_DROP in trigger_set:
            return (
                DecisionType.SCHEDULE_REVIEW,
                f"Learning velocity has dropped ({confidence.value} confidence). "
                f"Injecting spaced-repetition review tasks to consolidate progress. "
                f"Evidence: {signals[0] if signals else 'velocity drop signal'}."
            )

        # 8. Milestone missed → flag for attention
        if ReplanningTrigger.MILESTONE_MISSED in trigger_set:
            return (
                DecisionType.MILESTONE_REVIEW,
                f"Milestone target date missed ({confidence.value} confidence). "
                f"Milestone reassessment recommended to adjust timeline or scope. "
                f"Evidence: {signals[0] if signals else 'milestone missed'}."
            )

        # 9. HEALTHY — continue
        return (
            DecisionType.CONTINUE,
            f"Learning health is {health_status.value}. No intervention required. "
            f"Continue current plan and monitor progress."
        )

    @classmethod
    def decide_from_report(
        cls,
        learner_id: str,
        report: Any,       # LearningHealthReport from adaptive.py
        plan_id: Optional[str] = None,
    ) -> LearningDecision:
        """
        Convenience method: produce a decision directly from a LearningHealthReport.

        :param learner_id:  Learner the decision is for
        :param report:      LearningHealthReport from AdaptiveLearningEngine
        :param plan_id:     Active plan ID
        """
        return cls.decide(
            learner_id=learner_id,
            health_status=report.health_status,
            triggers=report.triggers_detected,
            signals=report.signals,
            plan_id=plan_id,
        )


# Backward and ergonomic alias
AutonomousDecisionEngine = LearningDecisionEngine
