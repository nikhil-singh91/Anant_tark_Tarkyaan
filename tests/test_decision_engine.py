"""
Tests for Phase 6: Learning Decision Engine
Covers: LearningDecisionEngine, LearningDecision, DecisionType, DecisionConfidence
"""
from __future__ import annotations

import pytest

from tarkyaan.models.enums import HealthStatus, ReplanningTrigger
from tarkyaan.planning.decision_engine import (
    DecisionConfidence,
    DecisionType,
    LearningDecision,
    LearningDecisionEngine,
)


# ---------------------------------------------------------------------------
# LearningDecisionEngine — Decision Logic
# ---------------------------------------------------------------------------

class TestLearningDecisionEngine:
    def _decide(self, health_status, triggers, signals=None):
        return LearningDecisionEngine.decide(
            learner_id="learner_d",
            health_status=health_status,
            triggers=triggers,
            signals=signals or [],
        )

    def test_healthy_returns_continue(self):
        decision = self._decide(HealthStatus.HEALTHY, [])
        assert decision.decision_type == DecisionType.CONTINUE

    def test_regression_returns_replan(self):
        decision = self._decide(
            HealthStatus.REGRESSING,
            [ReplanningTrigger.REGRESSION],
            ["Mastery dropped by 10%"],
        )
        assert decision.decision_type == DecisionType.REPLAN

    def test_stall_returns_replan(self):
        decision = self._decide(
            HealthStatus.STALLED,
            [ReplanningTrigger.STALL],
            ["No progress in 5 sessions"],
        )
        assert decision.decision_type == DecisionType.REPLAN

    def test_overload_returns_replan(self):
        decision = self._decide(
            HealthStatus.OVERLOADED,
            [ReplanningTrigger.OVERLOAD],
            ["70% task failure rate"],
        )
        assert decision.decision_type == DecisionType.REPLAN

    def test_gap_persistence_returns_replan(self):
        decision = self._decide(
            HealthStatus.AT_RISK,
            [ReplanningTrigger.GAP_PERSISTENCE],
            ["3 gaps unresolved"],
        )
        assert decision.decision_type == DecisionType.REPLAN

    def test_misconception_loop_returns_replan(self):
        decision = self._decide(
            HealthStatus.AT_RISK,
            [ReplanningTrigger.MISCONCEPTION_LOOP],
            ["loops topic recurring"],
        )
        assert decision.decision_type == DecisionType.REPLAN

    def test_plateau_returns_change_strategy(self):
        decision = self._decide(
            HealthStatus.PLATEAUED,
            [ReplanningTrigger.PLATEAU],
        )
        assert decision.decision_type == DecisionType.CHANGE_STRATEGY

    def test_velocity_drop_returns_schedule_review(self):
        decision = self._decide(
            HealthStatus.AT_RISK,
            [ReplanningTrigger.VELOCITY_DROP],
        )
        assert decision.decision_type == DecisionType.SCHEDULE_REVIEW

    def test_milestone_missed_returns_milestone_review(self):
        decision = self._decide(
            HealthStatus.AT_RISK,
            [ReplanningTrigger.MILESTONE_MISSED],
        )
        assert decision.decision_type == DecisionType.MILESTONE_REVIEW

    def test_regression_priority_over_plateau(self):
        # REGRESSION should take priority over PLATEAU
        decision = self._decide(
            HealthStatus.REGRESSING,
            [ReplanningTrigger.REGRESSION, ReplanningTrigger.PLATEAU],
        )
        assert decision.decision_type == DecisionType.REPLAN

    def test_confidence_high_with_multiple_signals(self):
        decision = self._decide(
            HealthStatus.REGRESSING,
            [ReplanningTrigger.REGRESSION],
            ["Signal 1", "Signal 2", "Signal 3"],
        )
        assert decision.confidence == DecisionConfidence.HIGH

    def test_confidence_medium_with_one_signal(self):
        decision = self._decide(
            HealthStatus.STALLED,
            [ReplanningTrigger.STALL],
            ["One signal"],
        )
        assert decision.confidence == DecisionConfidence.MEDIUM

    def test_confidence_low_with_no_signals(self):
        decision = self._decide(HealthStatus.HEALTHY, [])
        assert decision.confidence == DecisionConfidence.LOW

    def test_rationale_is_non_empty(self):
        decision = self._decide(
            HealthStatus.REGRESSING,
            [ReplanningTrigger.REGRESSION],
            ["Mastery dropped"],
        )
        assert len(decision.rationale) > 20

    def test_decision_has_learner_id(self):
        decision = LearningDecisionEngine.decide(
            learner_id="unique_learner",
            health_status=HealthStatus.HEALTHY,
            triggers=[],
            signals=[],
        )
        assert decision.learner_id == "unique_learner"

    def test_decision_has_unique_id(self):
        d1 = self._decide(HealthStatus.HEALTHY, [])
        d2 = self._decide(HealthStatus.HEALTHY, [])
        assert d1.decision_id != d2.decision_id

    def test_plan_id_in_parameters(self):
        decision = LearningDecisionEngine.decide(
            learner_id="l",
            health_status=HealthStatus.STALLED,
            triggers=[ReplanningTrigger.STALL],
            signals=["stalled"],
            plan_id="plan_xyz",
        )
        assert decision.parameters.get("plan_id") == "plan_xyz"

    def test_decide_from_report(self):
        from tarkyaan.planning.adaptive import LearningHealthReport
        report = LearningHealthReport(
            health_status=HealthStatus.STALLED,
            triggers_detected=[ReplanningTrigger.STALL],
            signals=["No progress in 4 sessions"],
        )
        decision = LearningDecisionEngine.decide_from_report(
            learner_id="l", report=report, plan_id="plan_1"
        )
        assert decision.decision_type == DecisionType.REPLAN
        assert decision.parameters.get("plan_id") == "plan_1"

    def test_is_autonomous_default_true(self):
        decision = self._decide(HealthStatus.HEALTHY, [])
        assert decision.is_autonomous

    def test_evidence_signals_preserved(self):
        signals = ["Signal A", "Signal B"]
        decision = self._decide(HealthStatus.HEALTHY, [], signals)
        assert decision.evidence_signals == signals

    def test_triggers_preserved(self):
        triggers = [ReplanningTrigger.REGRESSION, ReplanningTrigger.STALL]
        decision = self._decide(HealthStatus.REGRESSING, triggers, ["s1", "s2", "s3"])
        assert ReplanningTrigger.REGRESSION in decision.triggers
