"""
Unit tests for WorkloadEngine.
Tests duration summation, daily/weekly pacing, and overload warning detection.
"""

from datetime import datetime, timedelta, timezone
import pytest

from tarkyaan.models.learner import LearnerProfile
from tarkyaan.models.planning import LearningTask
from tarkyaan.planning.workload_engine import WorkloadEngine


class TestWorkloadEngine:
    @pytest.fixture
    def tasks(self):
        return [
            LearningTask(title="Task 1", topic_id="t1", estimated_minutes=30),
            LearningTask(title="Task 2", topic_id="t2", estimated_minutes=45),
            LearningTask(title="Task 3", topic_id="t3", estimated_minutes=45),
            LearningTask(title="Task 4", topic_id="t4", estimated_minutes=60),
        ]

    def test_workload_summation_and_sessions(self, tasks):
        estimate = WorkloadEngine.estimate(tasks=tasks)
        # 30 + 45 + 45 + 60 = 180 min = 3.0 hours
        assert estimate.total_minutes == 180
        assert estimate.total_hours == 3.0
        assert estimate.estimated_sessions >= 3

    def test_overload_warning_triggered_when_deadline_insufficient(self):
        learner = LearnerProfile(
            display_name="Rohan",
            daily_time_budget_minutes=30  # Only 30 min/day
        )
        # 10 heavy tasks = 600 minutes (10 hours)
        heavy_tasks = [
            LearningTask(title=f"Heavy Task {i}", topic_id=f"t{i}", estimated_minutes=60)
            for i in range(10)
        ]
        # Deadline is in 3 days: 3 * 30 min = 90 min capacity < 600 min needed!
        now = datetime.now(timezone.utc)
        deadline = now + timedelta(days=3)

        estimate = WorkloadEngine.estimate(
            tasks=heavy_tasks,
            learner=learner,
            deadline=deadline
        )

        assert estimate.is_overloaded is True
        assert estimate.overload_reason is not None
        assert "capacity" in estimate.overload_reason.lower() or "requires" in estimate.overload_reason.lower()

    def test_realistic_pacing_without_overload(self, tasks):
        learner = LearnerProfile(
            display_name="Meera",
            daily_time_budget_minutes=60
        )
        now = datetime.now(timezone.utc)
        deadline = now + timedelta(days=10)  # 10 days * 60 min = 600 min capacity > 180 min needed

        estimate = WorkloadEngine.estimate(
            tasks=tasks,
            learner=learner,
            deadline=deadline
        )
        assert estimate.is_overloaded is False
        assert estimate.daily_minutes <= 60.0
