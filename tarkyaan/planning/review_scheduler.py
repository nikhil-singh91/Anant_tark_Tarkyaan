"""
Tarkyaan Review Scheduler — Phase 6.
Spaced-repetition scheduling and retention review task injection.

Components:
- SpacedRepetitionScheduler:  SM-2 variant computing next review intervals
- RetentionReviewEngine:      Creates REVIEW LearningTask objects for due topics
- ReviewScheduler:            Top-level facade for scheduling + review task creation
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from tarkyaan.models.enums import ReviewUrgency, TaskType
from tarkyaan.models.planning import LearningTask


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# SM-2 Spaced Repetition Computation
# ---------------------------------------------------------------------------

class ReviewInterval(BaseModel):
    """Computed spaced-repetition parameters for a single topic."""
    topic_id: str
    next_review_at: datetime
    interval_days: float
    ease_factor: float
    repetitions: int
    urgency: ReviewUrgency


class SpacedRepetitionScheduler:
    """
    SM-2 variant adapted for mastery-based Tarkyaan learning evidence.

    SM-2 algorithm (Wozniak, 1987):
    - interval[1] = 1 day
    - interval[2] = 6 days
    - interval[n] = interval[n-1] * EF  (n >= 3)
    - EF_new = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
      where q = quality [0-5]

    Tarkyaan adaptation:
    - quality is derived from mastery_score [0,1] mapped to [0,5]
    - minimum EF = 1.3 (prevents runaway short intervals)
    """

    MIN_EASE_FACTOR: float = 1.3
    INITIAL_EASE_FACTOR: float = 2.5

    @classmethod
    def mastery_to_quality(cls, mastery_score: float) -> float:
        """Map mastery score [0,1] → SM-2 quality score [0,5]."""
        return round(max(0.0, min(5.0, mastery_score * 5.0)), 2)

    @classmethod
    def compute_next_review(
        cls,
        topic_id: str,
        mastery_score: float,
        current_interval_days: float = 1.0,
        ease_factor: float = INITIAL_EASE_FACTOR,
        repetitions: int = 0,
        as_of: Optional[datetime] = None,
    ) -> ReviewInterval:
        """
        Compute the next review date using SM-2 variant.

        :param topic_id:               Topic being scheduled
        :param mastery_score:          Current mastery [0,1]
        :param current_interval_days:  Previous interval in days
        :param ease_factor:            Current EF (default 2.5)
        :param repetitions:            Number of successful repetitions so far
        :param as_of:                  Reference datetime (default: now)
        :return: ReviewInterval with next_review_at and updated parameters
        """
        now = as_of or _utc_now()
        q = cls.mastery_to_quality(mastery_score)

        # Update ease factor
        new_ef = ease_factor + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        new_ef = max(cls.MIN_EASE_FACTOR, round(new_ef, 4))

        # Compute new interval
        if q < 3.0:
            # Below threshold: restart from beginning
            new_interval = 1.0
            new_reps = 0
        else:
            new_reps = repetitions + 1
            if new_reps == 1:
                new_interval = 1.0
            elif new_reps == 2:
                new_interval = 6.0
            else:
                new_interval = round(current_interval_days * new_ef, 2)

        next_review_at = now + timedelta(days=new_interval)

        # Compute urgency (relative to previous interval)
        overdue_ratio = current_interval_days / max(new_interval, 1.0)
        if overdue_ratio >= 3.0:
            urgency = ReviewUrgency.CRITICAL
        elif overdue_ratio >= 1.5:
            urgency = ReviewUrgency.HIGH
        elif new_interval <= current_interval_days:
            urgency = ReviewUrgency.NORMAL
        else:
            urgency = ReviewUrgency.LOW

        return ReviewInterval(
            topic_id=topic_id,
            next_review_at=next_review_at,
            interval_days=new_interval,
            ease_factor=new_ef,
            repetitions=new_reps,
            urgency=urgency,
        )

    @classmethod
    def compute_urgency_from_due(
        cls,
        next_review_at: datetime,
        interval_days: float,
        as_of: Optional[datetime] = None,
    ) -> ReviewUrgency:
        """
        Given a scheduled next_review_at and original interval, compute current urgency.
        """
        now = as_of or _utc_now()
        if next_review_at.tzinfo is None:
            next_review_at = next_review_at.replace(tzinfo=timezone.utc)
        days_overdue = (now - next_review_at).total_seconds() / 86400.0

        if days_overdue >= 3 * interval_days:
            return ReviewUrgency.CRITICAL
        elif days_overdue >= 0:
            return ReviewUrgency.HIGH
        elif days_overdue >= -1:
            return ReviewUrgency.NORMAL
        else:
            return ReviewUrgency.LOW


# ---------------------------------------------------------------------------
# RetentionReviewEngine
# ---------------------------------------------------------------------------

class RetentionReviewEngine:
    """
    Creates REVIEW-type LearningTask objects for topics due for spaced review.
    These tasks are injected into the active plan by ReviewScheduler.
    """

    @classmethod
    def create_review_task(
        cls,
        topic_id: str,
        learner_id: str,
        plan_id: str,
        urgency: ReviewUrgency,
        mastery_score: float = 0.5,
        phase_id: Optional[str] = None,
    ) -> LearningTask:
        """
        Create a REVIEW LearningTask for a topic due for spaced repetition.

        :param topic_id:      Topic to review
        :param learner_id:    Learner who owns the task
        :param plan_id:       Plan to attach the task to
        :param urgency:       ReviewUrgency classification
        :param mastery_score: Current mastery (influences estimated_minutes)
        :param phase_id:      Optional phase to attach to
        """
        urgency_priority_map = {
            ReviewUrgency.CRITICAL: 4.0,
            ReviewUrgency.HIGH: 3.0,
            ReviewUrgency.NORMAL: 2.0,
            ReviewUrgency.LOW: 1.0,
            ReviewUrgency.OPTIONAL: 0.5,
        }
        priority = urgency_priority_map.get(urgency, 2.0)

        # Shorter review sessions for high-mastery topics
        estimated_minutes = 15 if mastery_score >= 0.70 else 25

        urgency_prefix_map = {
            ReviewUrgency.CRITICAL: "⚠ CRITICAL REVIEW",
            ReviewUrgency.HIGH: "↑ Priority Review",
            ReviewUrgency.NORMAL: "Review",
            ReviewUrgency.LOW: "Scheduled Review",
            ReviewUrgency.OPTIONAL: "Optional Review",
        }
        prefix = urgency_prefix_map.get(urgency, "Review")

        return LearningTask(
            plan_id=plan_id,
            phase_id=phase_id,
            learner_id=learner_id,
            topic_id=topic_id,
            concept_id=topic_id,
            title=f"{prefix}: {topic_id}",
            description=(
                f"Spaced-repetition review session for concept '{topic_id}'. "
                f"Urgency: {urgency.value}. Current mastery: {mastery_score:.0%}."
            ),
            task_type=TaskType.REVIEW,
            objective=f"Consolidate and verify retained mastery of '{topic_id}'.",
            difficulty=max(1, min(3, int(mastery_score * 5))),
            estimated_minutes=estimated_minutes,
            priority=priority,
            rationale=f"Spaced repetition: due for review (urgency={urgency.value}).",
        )


# ---------------------------------------------------------------------------
# ReviewScheduler (Top-Level Facade)
# ---------------------------------------------------------------------------

class ReviewScheduler:
    """
    Top-level facade integrating SpacedRepetitionScheduler and RetentionReviewEngine
    with Tarkyaan's MemoryManager.

    Responsibilities:
    - Schedule initial review after mastery is updated
    - Retrieve due reviews and inject REVIEW tasks into the active plan
    - Update schedules after review completion
    """

    def __init__(
        self,
        memory: Optional[Any] = None,
        event_bus: Optional[Any] = None,
    ) -> None:
        self._memory = memory
        self._event_bus = event_bus

    @property
    def memory(self) -> Any:
        if self._memory is None:
            from tarkyaan.memory.memory_manager import TarkyaanMemoryManager
            self._memory = TarkyaanMemoryManager()
        return self._memory

    @property
    def bus(self) -> Any:
        if self._event_bus is None:
            from tarkyaan.events import event_bus as _bus
            return _bus
        return self._event_bus

    def schedule_review(
        self,
        learner_id: str,
        topic_id: str,
        mastery_score: float,
        current_interval_days: float = 1.0,
        ease_factor: float = SpacedRepetitionScheduler.INITIAL_EASE_FACTOR,
        repetitions: int = 0,
    ) -> ReviewInterval:
        """
        Compute and persist the next spaced-repetition review for a topic.
        Returns the computed ReviewInterval.
        """
        interval = SpacedRepetitionScheduler.compute_next_review(
            topic_id=topic_id,
            mastery_score=mastery_score,
            current_interval_days=current_interval_days,
            ease_factor=ease_factor,
            repetitions=repetitions,
        )

        self.memory.save_review_schedule(
            learner_id=learner_id,
            topic_id=topic_id,
            next_review_at=interval.next_review_at,
            interval_days=interval.interval_days,
            ease_factor=interval.ease_factor,
            repetitions=interval.repetitions,
            urgency=interval.urgency.value,
            last_mastery_score=mastery_score,
        )

        # Publish event
        try:
            from tarkyaan.events.event_bus import TarkyaanEvent
            self.bus.publish(
                TarkyaanEvent.REVIEW_SCHEDULED,
                payload={
                    "topic_id": topic_id,
                    "next_review_at": interval.next_review_at.isoformat(),
                    "interval_days": interval.interval_days,
                    "urgency": interval.urgency.value,
                },
                learner_id=learner_id,
                source="review_scheduler",
            )
        except Exception:
            pass

        return interval

    def get_due_review_tasks(
        self,
        learner_id: str,
        plan_id: str,
        limit: int = 10,
    ) -> List[LearningTask]:
        """
        Return a list of REVIEW LearningTask objects for all due topics.
        These tasks can be injected into the active plan.
        """
        due = self.memory.get_due_reviews(learner_id=learner_id, limit=limit)
        tasks: List[LearningTask] = []
        for row in due:
            topic_id = row["topic_id"]
            mastery = float(row.get("last_mastery_score", 0.5))
            urgency_str = row.get("urgency", "normal")
            try:
                urgency = ReviewUrgency(urgency_str)
            except ValueError:
                urgency = ReviewUrgency.NORMAL

            task = RetentionReviewEngine.create_review_task(
                topic_id=topic_id,
                learner_id=learner_id,
                plan_id=plan_id,
                urgency=urgency,
                mastery_score=mastery,
            )
            tasks.append(task)
        return tasks

    def mark_review_completed(
        self,
        learner_id: str,
        topic_id: str,
        new_mastery_score: float,
    ) -> ReviewInterval:
        """
        After a review session, compute the next interval and update the schedule.
        """
        # Fetch current schedule
        schedules = self.memory.get_all_review_schedules(learner_id=learner_id, limit=100)
        current: Optional[Dict[str, Any]] = None
        for s in schedules:
            if s["topic_id"] == topic_id:
                current = s
                break

        interval_days = float(current["interval_days"]) if current else 1.0
        ease_factor = float(current["ease_factor"]) if current else SpacedRepetitionScheduler.INITIAL_EASE_FACTOR
        repetitions = int(current["repetitions"]) if current else 0

        return self.schedule_review(
            learner_id=learner_id,
            topic_id=topic_id,
            mastery_score=new_mastery_score,
            current_interval_days=interval_days,
            ease_factor=ease_factor,
            repetitions=repetitions,
        )
