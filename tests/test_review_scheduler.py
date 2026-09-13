"""
Tests for Phase 6: Review Scheduler
Covers: SpacedRepetitionScheduler, RetentionReviewEngine, ReviewScheduler
"""
from __future__ import annotations

import pytest
from datetime import datetime, timedelta, timezone

from tarkyaan.models.enums import ReviewUrgency, TaskType
from tarkyaan.planning.review_scheduler import (
    RetentionReviewEngine,
    ReviewInterval,
    ReviewScheduler,
    SpacedRepetitionScheduler,
)


def _utc_now():
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# SpacedRepetitionScheduler
# ---------------------------------------------------------------------------

class TestSpacedRepetitionScheduler:
    def test_mastery_to_quality_mapping(self):
        assert SpacedRepetitionScheduler.mastery_to_quality(0.0) == 0.0
        assert SpacedRepetitionScheduler.mastery_to_quality(1.0) == 5.0
        assert SpacedRepetitionScheduler.mastery_to_quality(0.5) == 2.5

    def test_first_repetition_interval_one_day(self):
        result = SpacedRepetitionScheduler.compute_next_review(
            topic_id="loops",
            mastery_score=0.8,
            repetitions=0,
            current_interval_days=1.0,
        )
        assert result.repetitions == 1
        assert result.interval_days == 1.0

    def test_second_repetition_interval_six_days(self):
        result = SpacedRepetitionScheduler.compute_next_review(
            topic_id="loops",
            mastery_score=0.8,
            repetitions=1,
            current_interval_days=1.0,
        )
        assert result.repetitions == 2
        assert result.interval_days == 6.0

    def test_third_repetition_grows(self):
        result = SpacedRepetitionScheduler.compute_next_review(
            topic_id="loops",
            mastery_score=0.85,
            repetitions=2,
            current_interval_days=6.0,
        )
        assert result.repetitions == 3
        assert result.interval_days > 6.0

    def test_low_mastery_resets_interval(self):
        # mastery < 0.6 → quality < 3 → restart
        result = SpacedRepetitionScheduler.compute_next_review(
            topic_id="loops",
            mastery_score=0.3,  # quality = 1.5 < 3.0
            repetitions=5,
            current_interval_days=20.0,
        )
        assert result.repetitions == 0
        assert result.interval_days == 1.0

    def test_ease_factor_minimum_enforced(self):
        # Very low mastery → EF should not drop below MIN_EASE_FACTOR
        result = SpacedRepetitionScheduler.compute_next_review(
            topic_id="topic",
            mastery_score=0.0,
            ease_factor=1.4,
            repetitions=0,
            current_interval_days=1.0,
        )
        assert result.ease_factor >= SpacedRepetitionScheduler.MIN_EASE_FACTOR

    def test_next_review_at_is_future(self):
        now = _utc_now()
        result = SpacedRepetitionScheduler.compute_next_review(
            topic_id="lists",
            mastery_score=0.7,
        )
        assert result.next_review_at > now

    def test_urgency_low_for_future_review(self):
        result = SpacedRepetitionScheduler.compute_next_review(
            topic_id="recursion",
            mastery_score=0.9,
            repetitions=3,
            current_interval_days=6.0,
        )
        # High mastery, not yet overdue → interval grows, urgency LOW
        assert result.urgency in (ReviewUrgency.LOW, ReviewUrgency.NORMAL)

    def test_urgency_computation_from_due(self):
        # Severely overdue → CRITICAL
        overdue = _utc_now() - timedelta(days=10)
        urgency = SpacedRepetitionScheduler.compute_urgency_from_due(
            next_review_at=overdue,
            interval_days=2.0,
        )
        assert urgency == ReviewUrgency.CRITICAL


# ---------------------------------------------------------------------------
# RetentionReviewEngine
# ---------------------------------------------------------------------------

class TestRetentionReviewEngine:
    def test_creates_review_task(self):
        task = RetentionReviewEngine.create_review_task(
            topic_id="closures",
            learner_id="learner_1",
            plan_id="plan_1",
            urgency=ReviewUrgency.NORMAL,
            mastery_score=0.6,
        )
        assert task.task_type == TaskType.REVIEW
        assert "closures" in task.title
        assert task.topic_id == "closures"

    def test_critical_urgency_has_high_priority(self):
        critical = RetentionReviewEngine.create_review_task(
            topic_id="t", learner_id="l", plan_id="p",
            urgency=ReviewUrgency.CRITICAL,
        )
        low = RetentionReviewEngine.create_review_task(
            topic_id="t", learner_id="l", plan_id="p",
            urgency=ReviewUrgency.LOW,
        )
        assert critical.priority > low.priority

    def test_high_mastery_shorter_session(self):
        high = RetentionReviewEngine.create_review_task(
            topic_id="t", learner_id="l", plan_id="p",
            urgency=ReviewUrgency.NORMAL, mastery_score=0.85,
        )
        low = RetentionReviewEngine.create_review_task(
            topic_id="t", learner_id="l", plan_id="p",
            urgency=ReviewUrgency.NORMAL, mastery_score=0.3,
        )
        assert high.estimated_minutes <= low.estimated_minutes

    def test_review_task_has_rationale(self):
        task = RetentionReviewEngine.create_review_task(
            topic_id="graphs", learner_id="l", plan_id="p",
            urgency=ReviewUrgency.HIGH,
        )
        assert task.rationale != ""
        assert "review" in task.rationale.lower()


# ---------------------------------------------------------------------------
# ReviewScheduler (with in-memory store)
# ---------------------------------------------------------------------------

class TestReviewScheduler:
    def _make_scheduler(self):
        from tarkyaan.memory.memory_store import TarkyaanMemoryStore
        from tarkyaan.memory.memory_manager import TarkyaanMemoryManager
        from tarkyaan.events.event_bus import EventBus
        store = TarkyaanMemoryStore(":memory:")
        memory = TarkyaanMemoryManager(store)
        bus = EventBus()
        return ReviewScheduler(memory=memory, event_bus=bus), memory

    def _create_learner(self, memory):
        from tarkyaan.models.learner import LearnerProfile
        from tarkyaan.models.enums import AutonomyLevel
        profile = LearnerProfile(
            learner_id="learner_rs",
            display_name="RS Test",
            primary_domain="programming",
            preferred_language="en",
            preferred_learning_style="visual",
            preferred_explanation_style="step_by_step",
            daily_time_budget_minutes=60,
            current_autonomy_level=AutonomyLevel.LEVEL_2,
        )
        return memory.create_learner(profile)

    def test_schedule_review_persists(self):
        scheduler, memory = self._make_scheduler()
        self._create_learner(memory)
        interval = scheduler.schedule_review(
            learner_id="learner_rs",
            topic_id="recursion",
            mastery_score=0.7,
        )
        assert interval.interval_days >= 1.0
        schedules = memory.get_all_review_schedules("learner_rs")
        assert len(schedules) == 1
        assert schedules[0]["topic_id"] == "recursion"

    def test_get_due_review_tasks(self):
        scheduler, memory = self._make_scheduler()
        self._create_learner(memory)
        # Schedule a review in the past (overdue)
        past = _utc_now() - timedelta(days=1)
        memory.save_review_schedule(
            learner_id="learner_rs",
            topic_id="loops",
            next_review_at=past,
            urgency="high",
            last_mastery_score=0.6,
        )
        tasks = scheduler.get_due_review_tasks(
            learner_id="learner_rs", plan_id="plan_x"
        )
        assert len(tasks) == 1
        assert tasks[0].topic_id == "loops"

    def test_no_due_tasks_for_future_schedule(self):
        scheduler, memory = self._make_scheduler()
        self._create_learner(memory)
        future = _utc_now() + timedelta(days=5)
        memory.save_review_schedule(
            learner_id="learner_rs",
            topic_id="lists",
            next_review_at=future,
        )
        tasks = scheduler.get_due_review_tasks(
            learner_id="learner_rs", plan_id="plan_x"
        )
        assert len(tasks) == 0

    def test_mark_review_completed_updates_schedule(self):
        scheduler, memory = self._make_scheduler()
        self._create_learner(memory)
        # Initial schedule
        scheduler.schedule_review(
            learner_id="learner_rs",
            topic_id="closures",
            mastery_score=0.5,
        )
        # Mark completed with higher mastery
        new_interval = scheduler.mark_review_completed(
            learner_id="learner_rs",
            topic_id="closures",
            new_mastery_score=0.75,
        )
        assert new_interval.interval_days >= 1.0
        schedules = memory.get_all_review_schedules("learner_rs")
        assert len(schedules) == 1  # Upserted, not duplicated
