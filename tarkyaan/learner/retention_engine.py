"""
Tarkyaan Retention & Forgetting Engine.
Calculates temporal Ebbinghaus memory decay and schedules spaced review triggers.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Optional


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RetentionEngine:
    """
    Computes temporal memory decay using the exponential Ebbinghaus curve:
    M_decayed(c) = M_baseline + (M(c) - M_baseline) * exp(-delta_t / S_c)
    """

    DEFAULT_BASELINE: float = 0.1
    DEFAULT_STABILITY_DAYS: float = 14.0
    REVIEW_THRESHOLD: float = 0.65

    @classmethod
    def calculate_decayed_mastery(
        cls,
        current_mastery: float,
        last_practiced: Optional[datetime],
        as_of: Optional[datetime] = None,
        stability_days: float = DEFAULT_STABILITY_DAYS,
        baseline: float = DEFAULT_BASELINE
    ) -> float:
        """
        Calculate decayed mastery over elapsed time.
        :param current_mastery: Prior mastery score M in [0.0, 1.0]
        :param last_practiced: UTC datetime of last practice or assessment
        :param as_of: Current time (defaults to utcnow)
        :param stability_days: Stability factor S_c in days (half-life multiplier)
        :param baseline: Floor baseline below which decay will not drop
        :return: Decayed mastery score clamped to [baseline, current_mastery]
        """
        m = max(0.0, min(1.0, float(current_mastery)))
        b = max(0.0, min(0.5, float(baseline)))

        # If mastery is already at or below baseline, or never practiced, return m
        if m <= b or last_practiced is None:
            return m

        now = as_of or _utc_now()
        # Ensure timezones match
        if last_practiced.tzinfo is None:
            last_practiced = last_practiced.replace(tzinfo=timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        elapsed_seconds = (now - last_practiced).total_seconds()
        if elapsed_seconds <= 0:
            return m

        delta_t_days = elapsed_seconds / 86400.0
        s = max(1.0, float(stability_days))

        decay_factor = math.exp(-delta_t_days / s)
        decayed = b + (m - b) * decay_factor

        # Round and clamp to [baseline, current_mastery]
        return round(max(b, min(m, decayed)), 4)

    @classmethod
    def calculate_reinforced_stability(
        cls,
        current_stability: float,
        recall_score: float
    ) -> float:
        """
        Reinforce concept stability S_c upon successful recall practice.
        Higher performance expands memory stability interval.
        """
        s = max(1.0, float(current_stability))
        score = max(0.0, min(1.0, float(recall_score)))

        if score >= 0.70:
            # Successful retrieval boosts stability by 50% to 100%
            multiplier = 1.0 + (score * 0.8)
        else:
            # Failed retrieval reduces stability slightly
            multiplier = max(0.7, score + 0.2)

        return round(s * multiplier, 2)

    @classmethod
    def needs_spaced_review(
        cls,
        current_mastery: float,
        last_practiced: Optional[datetime],
        as_of: Optional[datetime] = None,
        stability_days: float = DEFAULT_STABILITY_DAYS,
        threshold: float = REVIEW_THRESHOLD
    ) -> bool:
        """
        Check if decayed mastery has slipped below the retention threshold.
        """
        if current_mastery < threshold or last_practiced is None:
            return False
        decayed = cls.calculate_decayed_mastery(
            current_mastery=current_mastery,
            last_practiced=last_practiced,
            as_of=as_of,
            stability_days=stability_days
        )
        return decayed < threshold
