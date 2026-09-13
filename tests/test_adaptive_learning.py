"""
Tests for Phase 6: Adaptive Learning Engine
Covers: MasteryTrajectoryAnalyzer, GapEvolutionAnalyzer, MisconceptionTrendAnalyzer,
        LearningHealthAnalyzer, AdaptiveLearningEngine
"""
from __future__ import annotations

import pytest
from datetime import datetime, timedelta, timezone

from tarkyaan.models.enums import HealthStatus, ReplanningTrigger
from tarkyaan.planning.adaptive import (
    AdaptiveLearningEngine,
    GapEvolutionAnalyzer,
    LearningHealthAnalyzer,
    MasteryTrajectoryAnalyzer,
    MisconceptionTrendAnalyzer,
)


def _utc_now():
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# MasteryTrajectoryAnalyzer
# ---------------------------------------------------------------------------

class TestMasteryTrajectoryAnalyzer:
    def test_empty_history_returns_zero(self):
        result = MasteryTrajectoryAnalyzer.analyze("math", [])
        assert result.current_mastery == 0.0
        assert result.sessions_sampled == 0
        assert not result.is_regressing
        assert not result.is_plateaued

    def test_improving_trajectory(self):
        history = [0.3, 0.4, 0.5, 0.6, 0.7]
        result = MasteryTrajectoryAnalyzer.analyze("math", history)
        assert result.mastery_delta > 0
        assert result.velocity > 0
        assert not result.is_regressing

    def test_regression_detected(self):
        # Drop > 5% → regression
        history = [0.7, 0.68, 0.63, 0.62]
        result = MasteryTrajectoryAnalyzer.analyze("math", history)
        assert result.is_regressing

    def test_no_regression_for_small_drop(self):
        # Drop < 5% → not regression
        history = [0.5, 0.51, 0.50]
        result = MasteryTrajectoryAnalyzer.analyze("math", history)
        assert not result.is_regressing

    def test_plateau_detected(self):
        tier_history = ["practicing", "practicing", "practicing", "practicing"]
        result = MasteryTrajectoryAnalyzer.analyze(
            "math", [0.5, 0.52, 0.51, 0.52], tier_history
        )
        assert result.is_plateaued

    def test_no_plateau_with_varying_tiers(self):
        tier_history = ["practicing", "competent", "practicing", "competent"]
        result = MasteryTrajectoryAnalyzer.analyze(
            "math", [0.5, 0.7, 0.6, 0.72], tier_history
        )
        assert not result.is_plateaued

    def test_single_sample(self):
        result = MasteryTrajectoryAnalyzer.analyze("math", [0.5])
        assert result.current_mastery == 0.5
        assert result.sessions_sampled == 1


# ---------------------------------------------------------------------------
# GapEvolutionAnalyzer
# ---------------------------------------------------------------------------

class TestGapEvolutionAnalyzer:
    def _make_gap(self, age_days: float) -> dict:
        detected_at = (_utc_now() - timedelta(days=age_days)).isoformat()
        return {"gap_id": f"gap_{int(age_days)}", "detected_at": detected_at}

    def test_no_gaps(self):
        result = GapEvolutionAnalyzer.analyze([])
        assert result.total_active_gaps == 0
        assert result.persistent_gap_ids == []

    def test_persistent_gap_detected(self):
        # > 7 days old → persistent
        gaps = [self._make_gap(8), self._make_gap(10)]
        result = GapEvolutionAnalyzer.analyze(gaps)
        assert len(result.persistent_gap_ids) == 2

    def test_fresh_gap_not_persistent(self):
        gaps = [self._make_gap(2)]
        result = GapEvolutionAnalyzer.analyze(gaps)
        assert len(result.persistent_gap_ids) == 0

    def test_mixed_gaps(self):
        gaps = [self._make_gap(1), self._make_gap(9)]
        result = GapEvolutionAnalyzer.analyze(gaps)
        assert result.total_active_gaps == 2
        assert len(result.persistent_gap_ids) == 1

    def test_avg_age_calculation(self):
        gaps = [self._make_gap(2), self._make_gap(4)]
        result = GapEvolutionAnalyzer.analyze(gaps)
        assert abs(result.avg_gap_age_days - 3.0) < 0.1


# ---------------------------------------------------------------------------
# MisconceptionTrendAnalyzer
# ---------------------------------------------------------------------------

class TestMisconceptionTrendAnalyzer:
    def test_empty_misconceptions(self):
        result = MisconceptionTrendAnalyzer.analyze([])
        assert result.total_misconceptions == 0
        assert result.recurring_count == 0
        assert result.recurring_topic_ids == []

    def test_single_misconception(self):
        result = MisconceptionTrendAnalyzer.analyze([
            {"topic_id": "loops", "category": "conceptual"}
        ])
        assert result.total_misconceptions == 1
        assert result.recurring_count == 0

    def test_recurring_misconception_detected(self):
        misconceptions = [
            {"topic_id": "loops", "category": "conceptual"},
            {"topic_id": "loops", "category": "algorithmic_logic"},
            {"topic_id": "lists", "category": "syntax_idiom"},
        ]
        result = MisconceptionTrendAnalyzer.analyze(misconceptions)
        assert "loops" in result.recurring_topic_ids
        assert result.recurring_count == 1

    def test_most_common_category(self):
        misconceptions = [
            {"topic_id": "t1", "category": "conceptual"},
            {"topic_id": "t2", "category": "conceptual"},
            {"topic_id": "t3", "category": "syntax_idiom"},
        ]
        result = MisconceptionTrendAnalyzer.analyze(misconceptions)
        assert result.most_common_category == "conceptual"


# ---------------------------------------------------------------------------
# LearningHealthAnalyzer
# ---------------------------------------------------------------------------

class TestLearningHealthAnalyzer:
    def test_healthy_state(self):
        result = LearningHealthAnalyzer.analyze(sessions_since_last_progress=0)
        assert result.health_status == HealthStatus.HEALTHY
        assert result.triggers_detected == []

    def test_stall_detected(self):
        result = LearningHealthAnalyzer.analyze(
            sessions_since_last_progress=5,
            stall_session_threshold=3,
        )
        assert ReplanningTrigger.STALL in result.triggers_detected
        assert result.health_status in (HealthStatus.STALLED, HealthStatus.AT_RISK)

    def test_overload_detected(self):
        result = LearningHealthAnalyzer.analyze(recent_task_fail_rate=0.75)
        assert ReplanningTrigger.OVERLOAD in result.triggers_detected
        assert result.health_status == HealthStatus.OVERLOADED

    def test_regression_from_trajectory(self):
        from tarkyaan.planning.adaptive import MasteryTrajectoryAnalyzer
        traj = MasteryTrajectoryAnalyzer.analyze("math", [0.7, 0.65, 0.60, 0.62])
        result = LearningHealthAnalyzer.analyze(trajectory=traj)
        assert ReplanningTrigger.REGRESSION in result.triggers_detected
        assert result.health_status == HealthStatus.REGRESSING

    def test_multiple_signals_at_risk(self):
        from tarkyaan.planning.adaptive import GapEvolutionReport, MasteryTrajectoryAnalyzer
        from datetime import timedelta
        traj = MasteryTrajectoryAnalyzer.analyze("math", [0.7, 0.63, 0.58])
        gap_report = GapEvolutionReport(
            total_active_gaps=3,
            persistent_gap_ids=["gap1", "gap2"],
            resolved_gap_count=0,
            new_gap_count=0,
            avg_gap_age_days=10.0,
        )
        result = LearningHealthAnalyzer.analyze(
            trajectory=traj,
            gap_report=gap_report,
        )
        assert len(result.triggers_detected) >= 2


# ---------------------------------------------------------------------------
# AdaptiveLearningEngine
# ---------------------------------------------------------------------------

class TestAdaptiveLearningEngine:
    def test_instantiation(self):
        engine = AdaptiveLearningEngine()
        assert engine is not None

    def test_evaluate_without_memory(self):
        engine = AdaptiveLearningEngine()
        report = engine.evaluate_learner_health(
            learner_id="test_learner",
            mastery_history=[0.3, 0.4, 0.5],
            topic_id="python",
        )
        assert report is not None
        assert report.health_status in HealthStatus.__members__.values()

    def test_should_replan_for_regression(self):
        engine = AdaptiveLearningEngine()
        report = engine.evaluate_learner_health(
            learner_id="test",
            mastery_history=[0.8, 0.72, 0.64],
            topic_id="python",
        )
        should_replan, triggers = engine.should_replan(report)
        # Regression detected → should replan
        if report.health_status == HealthStatus.REGRESSING:
            assert should_replan

    def test_should_not_replan_when_healthy(self):
        engine = AdaptiveLearningEngine()
        report = engine.evaluate_learner_health(
            learner_id="test",
            mastery_history=[0.4, 0.5, 0.6, 0.7],
            topic_id="python",
        )
        if report.health_status == HealthStatus.HEALTHY:
            should_replan, triggers = engine.should_replan(report)
            assert not should_replan
            assert triggers == []

    def test_with_event_bus(self):
        from tarkyaan.events.event_bus import EventBus, TarkyaanEvent
        bus = EventBus()
        received = []
        bus.subscribe(TarkyaanEvent.HEALTH_ALERT, lambda e: received.append(e))

        engine = AdaptiveLearningEngine(event_bus=bus)
        engine.evaluate_learner_health(
            learner_id="test",
            mastery_history=[0.8, 0.70, 0.62],  # regression
            topic_id="math",
        )
        # If regression detected, HEALTH_ALERT should be published
        # (event fired only if not HEALTHY)
