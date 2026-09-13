"""
Workload Engine for Tarkyaan Planning Brain.
Estimates realistic study durations, session distributions, pacing against deadlines,
and overload warnings.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from tarkyaan.models.learner import LearnerProfile
from tarkyaan.models.planning import LearningTask, WorkloadEstimate


class WorkloadEngine:
    """
    Calculates study workload metrics and enforces realistic capacity limits.
    """

    DEFAULT_DAILY_BUDGET_MINUTES: int = 60
    DEFAULT_SESSION_MINUTES: int = 45

    @classmethod
    def estimate(
        cls,
        tasks: List[LearningTask],
        learner: Optional[LearnerProfile] = None,
        deadline: Optional[datetime] = None
    ) -> WorkloadEstimate:
        """
        Compute total time, session pacing, and capacity overload warnings.
        """
        total_minutes = sum(t.estimated_minutes for t in tasks)
        total_hours = round(total_minutes / 60.0, 2)

        daily_budget = (
            learner.daily_time_budget_minutes
            if learner and learner.daily_time_budget_minutes > 0
            else cls.DEFAULT_DAILY_BUDGET_MINUTES
        )

        estimated_sessions = max(1, round(total_minutes / cls.DEFAULT_SESSION_MINUTES))

        # Pacing against target deadline
        target_days = 14  # Default planning horizon in days
        is_overloaded = False
        overload_reason: Optional[str] = None

        if deadline:
            now = datetime.now(timezone.utc)
            d = deadline if deadline.tzinfo else deadline.replace(tzinfo=timezone.utc)
            delta_days = max(1, int((d - now).total_seconds() / 86400.0))
            target_days = delta_days

            available_minutes = target_days * daily_budget
            # Overload threshold: required study time exceeds available budget by > 15%
            if total_minutes > available_minutes * 1.15:
                is_overloaded = True
                available_hours = round(available_minutes / 60.0, 1)
                overload_reason = (
                    f"The planned curriculum requires approximately {total_hours:.1f} hours of study, "
                    f"while your available capacity before the deadline ({d.strftime('%Y-%m-%d')}) "
                    f"is approximately {available_hours:.1f} hours at {daily_budget} minutes/day."
                )

        daily_minutes = round(total_minutes / max(1, target_days), 1)
        weekly_hours = round((daily_minutes * 7.0) / 60.0, 2)

        return WorkloadEstimate(
            total_minutes=total_minutes,
            total_hours=total_hours,
            estimated_sessions=estimated_sessions,
            daily_minutes=daily_minutes,
            weekly_hours=weekly_hours,
            target_days=target_days,
            is_overloaded=is_overloaded,
            overload_reason=overload_reason
        )
