"""
Unit tests for Tarkyaan MasteryEngine.
Validates deterministic Bayesian evidence updates, uncertainty decay, and tier classification.
"""

import pytest

from tarkyaan.learner.mastery_engine import MasteryEngine
from tarkyaan.models.enums import MasteryTier


class TestMasteryEngine:
    def test_tier_classification_thresholds(self):
        assert MasteryEngine.classify_tier(0.0, uncertainty=1.0) == MasteryTier.UNEXPLORED
        assert MasteryEngine.classify_tier(0.15) == MasteryTier.INTRODUCED
        assert MasteryEngine.classify_tier(0.39) == MasteryTier.INTRODUCED
        assert MasteryEngine.classify_tier(0.40) == MasteryTier.PRACTICING
        assert MasteryEngine.classify_tier(0.69) == MasteryTier.PRACTICING
        assert MasteryEngine.classify_tier(0.70) == MasteryTier.COMPETENT
        assert MasteryEngine.classify_tier(0.87) == MasteryTier.COMPETENT
        assert MasteryEngine.classify_tier(0.88) == MasteryTier.MASTERED
        assert MasteryEngine.classify_tier(1.0) == MasteryTier.MASTERED

    def test_initial_evidence_update(self):
        # M_t = 0.0, U_t = 1.0, Evidence E = 1.0 (perfect score)
        # alpha = 0.25
        # U_{t+1} = 1.0 * 0.75 = 0.75
        # confidence = 1.0 - 0.75 = 0.25
        # delta = 0.25 * (1.0 - 0.0) * 0.25 = 0.0625
        # M_{t+1} = 0.0 + 0.0625 = 0.0625
        res = MasteryEngine.calculate_update(
            current_mastery=0.0,
            current_uncertainty=1.0,
            evidence_score=1.0,
            alpha=0.25
        )
        assert res.prior_mastery == 0.0
        assert res.new_uncertainty == 0.75
        assert res.new_mastery == 0.0625
        assert res.delta_mastery == 0.0625
        assert res.new_tier == MasteryTier.INTRODUCED

    def test_repeated_successful_practice(self):
        # As student solves multiple problems successfully, mastery rises and uncertainty drops
        m = 0.0
        u = 1.0
        res = None
        for _ in range(10):
            res = MasteryEngine.calculate_update(
                current_mastery=m,
                current_uncertainty=u,
                evidence_score=1.0
            )
            assert res.new_mastery >= m
            assert res.new_uncertainty <= u
            m = res.new_mastery
            u = res.new_uncertainty

        assert m > 0.85
        assert u < 0.1
        assert res is not None
        assert res.new_tier in (MasteryTier.COMPETENT, MasteryTier.MASTERED)

    def test_failed_evidence_reduces_mastery(self):
        # Starting with competent mastery 0.75, student fails assessment (E = 0.0)
        res = MasteryEngine.calculate_update(
            current_mastery=0.75,
            current_uncertainty=0.2,
            evidence_score=0.0,
            alpha=0.25
        )
        assert res.new_mastery < 0.75
        assert res.delta_mastery < 0.0
        # Uncertainty also decays towards higher certainty of deficit
        assert res.new_uncertainty == round(0.2 * 0.75, 4)

    def test_boundary_clamping(self):
        # Testing extreme inputs
        res_high = MasteryEngine.calculate_update(
            current_mastery=1.0,
            current_uncertainty=0.0,
            evidence_score=1.0
        )
        assert res_high.new_mastery <= 1.0
        assert res_high.new_uncertainty >= 0.0

        res_low = MasteryEngine.calculate_update(
            current_mastery=0.0,
            current_uncertainty=0.5,
            evidence_score=0.0
        )
        assert res_low.new_mastery >= 0.0
        assert res_low.new_uncertainty <= 1.0
