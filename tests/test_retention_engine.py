"""
Unit tests for Tarkyaan RetentionEngine.
Validates exponential Ebbinghaus decay, stability reinforcement, and spaced review flags.
"""

from datetime import datetime, timedelta, timezone
import pytest

from tarkyaan.learner.retention_engine import RetentionEngine


class TestRetentionEngine:
    def test_zero_elapsed_time_preserves_mastery(self):
        now = datetime.now(timezone.utc)
        decayed = RetentionEngine.calculate_decayed_mastery(
            current_mastery=0.85,
            last_practiced=now,
            as_of=now,
            stability_days=14.0,
            baseline=0.1
        )
        assert decayed == 0.85

    def test_short_and_long_elapsed_decay(self):
        t0 = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
        # 7 days later (half-life of 14 days)
        t_7d = t0 + timedelta(days=7)
        # 60 days later
        t_60d = t0 + timedelta(days=60)

        initial_m = 0.90
        decay_7d = RetentionEngine.calculate_decayed_mastery(
            current_mastery=initial_m,
            last_practiced=t0,
            as_of=t_7d,
            stability_days=14.0,
            baseline=0.1
        )
        decay_60d = RetentionEngine.calculate_decayed_mastery(
            current_mastery=initial_m,
            last_practiced=t0,
            as_of=t_60d,
            stability_days=14.0,
            baseline=0.1
        )

        assert 0.1 < decay_60d < decay_7d < initial_m
        # Over long time, decayed mastery should asymptotically approach baseline 0.1
        assert pytest.approx(decay_60d, abs=0.05) == 0.11

    def test_decay_never_drops_below_baseline(self):
        t0 = datetime(2020, 1, 1, tzinfo=timezone.utc)
        t_future = datetime(2026, 1, 1, tzinfo=timezone.utc)  # 6 years later

        decayed = RetentionEngine.calculate_decayed_mastery(
            current_mastery=0.8,
            last_practiced=t0,
            as_of=t_future,
            stability_days=14.0,
            baseline=0.1
        )
        assert decayed >= 0.1
        assert pytest.approx(decayed, abs=0.001) == 0.1

    def test_stability_factor_slows_decay(self):
        t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
        t_14d = t0 + timedelta(days=14)

        # High stability (30 days) vs Low stability (7 days)
        decay_high_s = RetentionEngine.calculate_decayed_mastery(
            current_mastery=0.85,
            last_practiced=t0,
            as_of=t_14d,
            stability_days=30.0,
            baseline=0.1
        )
        decay_low_s = RetentionEngine.calculate_decayed_mastery(
            current_mastery=0.85,
            last_practiced=t0,
            as_of=t_14d,
            stability_days=7.0,
            baseline=0.1
        )

        assert decay_high_s > decay_low_s

    def test_stability_reinforcement_on_recall(self):
        current_s = 14.0
        # Successful recall boosts stability
        s_boosted = RetentionEngine.calculate_reinforced_stability(current_s, recall_score=0.95)
        assert s_boosted > current_s

        # Failed recall decreases stability
        s_reduced = RetentionEngine.calculate_reinforced_stability(current_s, recall_score=0.2)
        assert s_reduced < current_s

    def test_spaced_review_trigger(self):
        t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
        # Freshly practiced -> no review needed
        assert not RetentionEngine.needs_spaced_review(
            current_mastery=0.85,
            last_practiced=t0,
            as_of=t0,
            threshold=0.65
        )

        # 30 days later -> decayed below 0.65 -> review needed
        t_30d = t0 + timedelta(days=30)
        assert RetentionEngine.needs_spaced_review(
            current_mastery=0.85,
            last_practiced=t0,
            as_of=t_30d,
            stability_days=14.0,
            threshold=0.65
        )
