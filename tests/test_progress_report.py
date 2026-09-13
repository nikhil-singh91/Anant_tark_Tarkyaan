"""
Tests for Phase 6: Progress Report Engine
Covers: LearningVelocityAnalyzer, ResourceEffectivenessAnalyzer, ProgressReportEngine
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone

from tarkyaan.models.enums import HealthStatus
from tarkyaan.planning.progress_report import (
    LearningProgressReport,
    LearningVelocityAnalyzer,
    ProgressReportEngine,
    ResourceEffectivenessAnalyzer,
    VelocityReport,
)


def _utc_now():
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# LearningVelocityAnalyzer
# ---------------------------------------------------------------------------

class TestLearningVelocityAnalyzer:
    def test_empty_sessions(self):
        result = LearningVelocityAnalyzer.analyze([])
        assert result.topics_per_session == 0.0
        assert result.trend == "stable"

    def test_basic_velocity(self):
        sessions = [
            {"topics_covered": ["loops", "functions"]},
            {"topics_covered": ["classes"]},
        ]
        result = LearningVelocityAnalyzer.analyze(sessions)
        assert result.topics_per_session == 1.5
        assert result.sessions_analyzed == 2

    def test_json_string_topics(self):
        import json
        sessions = [
            {"topics_covered": json.dumps(["a", "b", "c"])},
        ]
        result = LearningVelocityAnalyzer.analyze(sessions)
        assert result.topics_per_session == 3.0

    def test_task_completion_rate(self):
        tasks = [
            {"status": "completed"},
            {"status": "completed"},
            {"status": "pending"},
            {"status": "pending"},
        ]
        sessions = [{"topics_covered": ["a"]}]  # Need at least 1 session
        result = LearningVelocityAnalyzer.analyze(sessions, tasks=tasks)
        assert result.task_completion_rate == 0.5
        assert result.tasks_completed == 2

    def test_improving_trend(self):
        # Second half has more topics than first half
        sessions = [
            {"topics_covered": ["a"]},
            {"topics_covered": ["b"]},
            {"topics_covered": ["c", "d", "e"]},
            {"topics_covered": ["f", "g", "h"]},
        ]
        result = LearningVelocityAnalyzer.analyze(sessions)
        assert result.trend == "improving"

    def test_declining_trend(self):
        sessions = [
            {"topics_covered": ["a", "b", "c"]},
            {"topics_covered": ["d", "e", "f"]},
            {"topics_covered": ["g"]},
            {"topics_covered": []},
        ]
        result = LearningVelocityAnalyzer.analyze(sessions)
        assert result.trend == "declining"

    def test_stable_trend(self):
        sessions = [
            {"topics_covered": ["a", "b"]},
            {"topics_covered": ["c", "d"]},
            {"topics_covered": ["e", "f"]},
            {"topics_covered": ["g", "h"]},
        ]
        result = LearningVelocityAnalyzer.analyze(sessions)
        assert result.trend == "stable"


# ---------------------------------------------------------------------------
# ResourceEffectivenessAnalyzer
# ---------------------------------------------------------------------------

class TestResourceEffectivenessAnalyzer:
    def test_empty_resources(self):
        result = ResourceEffectivenessAnalyzer.analyze([])
        assert result.resources_evaluated == 0
        assert result.avg_resource_score == 0.0

    def test_high_impact_resources(self):
        resources = [
            {"resource_id": "r1", "overall_score": 0.9},
            {"resource_id": "r2", "overall_score": 0.8},
        ]
        result = ResourceEffectivenessAnalyzer.analyze(resources)
        assert "r1" in result.high_impact_resource_ids
        assert "r2" in result.high_impact_resource_ids

    def test_low_impact_resources(self):
        resources = [
            {"resource_id": "r1", "overall_score": 0.2},
            {"resource_id": "r2", "overall_score": 0.35},
        ]
        result = ResourceEffectivenessAnalyzer.analyze(resources)
        assert "r1" in result.low_impact_resource_ids

    def test_average_score(self):
        resources = [
            {"resource_id": "r1", "overall_score": 0.6},
            {"resource_id": "r2", "overall_score": 0.8},
        ]
        result = ResourceEffectivenessAnalyzer.analyze(resources)
        assert abs(result.avg_resource_score - 0.7) < 0.01

    def test_mixed_impact(self):
        resources = [
            {"resource_id": "r1", "overall_score": 0.9},
            {"resource_id": "r2", "overall_score": 0.5},
            {"resource_id": "r3", "overall_score": 0.2},
        ]
        result = ResourceEffectivenessAnalyzer.analyze(resources)
        assert len(result.high_impact_resource_ids) == 1
        assert len(result.low_impact_resource_ids) == 1
        assert result.resources_evaluated == 3


# ---------------------------------------------------------------------------
# ProgressReportEngine (with in-memory store)
# ---------------------------------------------------------------------------

class TestProgressReportEngine:
    def _make_engine(self):
        from tarkyaan.memory.memory_store import TarkyaanMemoryStore
        from tarkyaan.memory.memory_manager import TarkyaanMemoryManager
        from tarkyaan.events.event_bus import EventBus
        store = TarkyaanMemoryStore(":memory:")
        memory = TarkyaanMemoryManager(store)
        bus = EventBus()
        return ProgressReportEngine(memory=memory, event_bus=bus), memory

    def _create_learner(self, memory):
        from tarkyaan.models.learner import LearnerProfile
        from tarkyaan.models.enums import AutonomyLevel
        profile = LearnerProfile(
            learner_id="learner_p",
            display_name="Progress Test",
            primary_domain="python",
            preferred_language="en",
            preferred_learning_style="visual",
            preferred_explanation_style="step_by_step",
            daily_time_budget_minutes=60,
            current_autonomy_level=AutonomyLevel.LEVEL_2,
        )
        return memory.create_learner(profile)

    def test_report_generation_empty_learner(self):
        engine, memory = self._make_engine()
        self._create_learner(memory)
        report = engine.generate_report("learner_p", HealthStatus.HEALTHY)
        assert isinstance(report, LearningProgressReport)
        assert report.learner_id == "learner_p"
        assert report.report_id.startswith("report_")
        assert report.health_status == HealthStatus.HEALTHY

    def test_headline_is_non_empty(self):
        engine, memory = self._make_engine()
        self._create_learner(memory)
        report = engine.generate_report("learner_p")
        assert len(report.headline) > 10

    def test_recommendations_always_present(self):
        engine, memory = self._make_engine()
        self._create_learner(memory)
        report = engine.generate_report("learner_p")
        assert len(report.recommendations) >= 1

    def test_stalled_report_has_recommendation(self):
        engine, memory = self._make_engine()
        self._create_learner(memory)
        report = engine.generate_report("learner_p", HealthStatus.STALLED)
        rec_text = " ".join(report.recommendations).lower()
        assert "session" in rec_text or "stall" in rec_text

    def test_overloaded_report_recommendation(self):
        engine, memory = self._make_engine()
        self._create_learner(memory)
        report = engine.generate_report("learner_p", HealthStatus.OVERLOADED)
        rec_text = " ".join(report.recommendations).lower()
        assert "difficulty" in rec_text or "foundation" in rec_text

    def test_report_with_mastery_data(self):
        engine, memory = self._make_engine()
        self._create_learner(memory)
        from tarkyaan.models.mastery import Subject, Topic, TopicMastery
        subject = Subject(subject_id="prog", name="Programming", domain="cs")
        memory.create_subject(subject)
        topic = Topic(topic_id="loops", subject_id="prog", name="Loops")
        memory.create_topic(topic)
        mastery = TopicMastery(
            learner_id="learner_p", topic_id="loops",
            subject_id="prog", name="Loops",
            mastery_score=0.75, uncertainty=0.1, tier="competent",
        )
        memory.update_topic_mastery(mastery)
        report = engine.generate_report("learner_p")
        assert report.mastery_summary.total_topics_tracked >= 1

    def test_event_published_on_report(self):
        from tarkyaan.events.event_bus import EventBus, TarkyaanEvent
        bus = EventBus()
        received = []
        bus.subscribe(TarkyaanEvent.PROGRESS_REPORT_GENERATED, lambda e: received.append(e))
        from tarkyaan.memory.memory_store import TarkyaanMemoryStore
        from tarkyaan.memory.memory_manager import TarkyaanMemoryManager
        memory = TarkyaanMemoryManager(TarkyaanMemoryStore(":memory:"))
        self._create_learner(memory)
        engine = ProgressReportEngine(memory=memory, event_bus=bus)
        engine.generate_report("learner_p")
        assert len(received) == 1

    def test_build_headline_static(self):
        from tarkyaan.planning.progress_report import MasteryProgressSummary
        summary = MasteryProgressSummary(
            total_topics_tracked=10,
            mastered_count=3,
            competent_count=4,
        )
        velocity = VelocityReport(task_completion_rate=0.8)
        headline = ProgressReportEngine._build_headline(HealthStatus.HEALTHY, summary, velocity)
        assert "7/10" in headline
        assert "80%" in headline
