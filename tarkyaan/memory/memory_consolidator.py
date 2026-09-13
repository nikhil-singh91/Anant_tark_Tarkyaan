"""
Memory Consolidator for Tarkyaan.
Aggregates episodic learning sessions, assessment results, and mastery levels
into structured progress snapshots and learning velocity metrics.
"""

from __future__ import annotations

from datetime import datetime, timezone
import uuid
from typing import Optional

from tarkyaan.memory.memory_manager import TarkyaanMemoryManager
from tarkyaan.models.enums import MasteryTier
from tarkyaan.models.learning import ProgressSnapshot


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MemoryConsolidator:
    """
    Synthesizes episodic records into semantic progress snapshots.
    """

    def __init__(self, memory_manager: TarkyaanMemoryManager) -> None:
        self._mgr = memory_manager

    def consolidate_progress(self, learner_id: str) -> ProgressSnapshot:
        """
        Evaluate current state across all topics and gaps to create an immutable progress snapshot.
        """
        masteries = self._mgr.list_topic_mastery(learner_id)
        gaps = self._mgr.get_active_gaps(learner_id)

        mastered_count = sum(1 for m in masteries if m.tier == MasteryTier.MASTERED)
        practicing_count = sum(1 for m in masteries if m.tier in (MasteryTier.PRACTICING, MasteryTier.COMPETENT))
        active_gaps_count = len(gaps)

        avg_mastery = (
            sum(m.mastery_score for m in masteries) / len(masteries)
            if masteries else 0.0
        )

        # Estimate velocity (topics mastered or moved to competent per week)
        # For simplicity, calculate from total mastered over 4-week window
        velocity = round(mastered_count / 2.0, 1) if mastered_count > 0 else 0.0

        snapshot = ProgressSnapshot(
            snapshot_id=f"snap_{uuid.uuid4().hex[:8]}",
            learner_id=learner_id,
            timestamp=_utc_now(),
            topics_mastered_count=mastered_count,
            topics_practicing_count=practicing_count,
            active_gaps_count=active_gaps_count,
            average_mastery=round(avg_mastery, 3),
            velocity_topics_per_week=velocity
        )

        self._mgr.record_progress_snapshot(snapshot)
        return snapshot
