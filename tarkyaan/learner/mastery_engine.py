"""
Tarkyaan Mastery Engine.
Provides deterministic evidence-based Bayesian mastery updates
and epistemic tier classification.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from tarkyaan.models.enums import MasteryTier


@dataclass(frozen=True)
class MasteryUpdateResult:
    """Outcome of a deterministic mastery calculation."""
    prior_mastery: float
    new_mastery: float
    prior_uncertainty: float
    new_uncertainty: float
    delta_mastery: float
    prior_tier: MasteryTier
    new_tier: MasteryTier


class MasteryEngine:
    """
    Deterministic cognitive mastery calculation engine.
    Converts empirical task scores E into updated mastery M(c) and uncertainty U(c).
    """

    DEFAULT_ALPHA: float = 0.25
    UNCERTAINTY_DECAY: float = 0.75

    @classmethod
    def classify_tier(cls, mastery: float, uncertainty: float = 0.0) -> MasteryTier:
        """
        Classify concept mastery into canonical educational tiers.
        :param mastery: Score in [0.0, 1.0]
        :param uncertainty: Uncertainty in [0.0, 1.0]
        """
        clamped_m = max(0.0, min(1.0, float(mastery)))

        if clamped_m >= 0.88:
            return MasteryTier.MASTERED
        elif clamped_m >= 0.70:
            return MasteryTier.COMPETENT
        elif clamped_m >= 0.40:
            return MasteryTier.PRACTICING
        elif clamped_m > 0.0 or (clamped_m == 0.0 and uncertainty < 0.9):
            return MasteryTier.INTRODUCED
        else:
            return MasteryTier.UNEXPLORED

    @classmethod
    def calculate_update(
        cls,
        current_mastery: float,
        current_uncertainty: float,
        evidence_score: float,
        alpha: float = DEFAULT_ALPHA
    ) -> MasteryUpdateResult:
        """
        Compute deterministic Bayesian evidence update:
        M_{t+1}(c) = M_t(c) + alpha * (E - M_t(c)) * (1 - U(c))
        U_{t+1}(c) = U_t(c) * 0.75

        :param current_mastery: Prior mastery M_t in [0.0, 1.0]
        :param current_uncertainty: Prior uncertainty U_t in [0.0, 1.0]
        :param evidence_score: Empirical performance score E in [0.0, 1.0]
        :param alpha: Learning rate parameter (default 0.25)
        :return: MasteryUpdateResult with rounded, validated scores and tier changes.
        """
        # Validate and clamp inputs
        m_t = max(0.0, min(1.0, float(current_mastery)))
        u_t = max(0.0, min(1.0, float(current_uncertainty)))
        e = max(0.0, min(1.0, float(evidence_score)))
        a = max(0.01, min(1.0, float(alpha)))

        prior_tier = cls.classify_tier(m_t, u_t)

        # Update uncertainty first (evidence reduces ignorance)
        # When u_t == 1.0, decaying u_{t+1} to 0.75 gives initial confidence weight (1 - 0.75) = 0.25.
        new_u = round(u_t * cls.UNCERTAINTY_DECAY, 4)
        new_u = max(0.0, min(1.0, new_u))

        # Confidence factor: (1 - U)
        # We use the updated uncertainty so that the initial observation with U=1.0 has non-zero weight.
        confidence_factor = 1.0 - new_u

        # Compute mastery delta
        delta = a * (e - m_t) * confidence_factor
        new_m = round(m_t + delta, 4)
        new_m = max(0.0, min(1.0, new_m))

        new_tier = cls.classify_tier(new_m, new_u)

        return MasteryUpdateResult(
            prior_mastery=round(m_t, 4),
            new_mastery=new_m,
            prior_uncertainty=round(u_t, 4),
            new_uncertainty=new_u,
            delta_mastery=round(new_m - m_t, 4),
            prior_tier=prior_tier,
            new_tier=new_tier
        )
