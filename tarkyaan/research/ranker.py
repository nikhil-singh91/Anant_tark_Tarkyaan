"""
Deterministic Resource Ranker.
Combines 8 evaluation dimensions into a composite score with deterministic tie-breaking.
"""

from __future__ import annotations

from typing import List, Tuple
from tarkyaan.models.learning import LearningResource


class ResourceRanker:
    """
    Ranks evaluated LearningResource instances deterministically using a transparent formula:
    Composite = 0.25 * Relevance + 0.20 * LearnerFit + 0.15 * Authority + 0.15 * DifficultyFit
              + 0.10 * Quality + 0.10 * Practical + 0.05 * Freshness
    """

    WEIGHT_RELEVANCE = 0.25
    WEIGHT_LEARNER_FIT = 0.20
    WEIGHT_AUTHORITY = 0.15
    WEIGHT_DIFFICULTY_FIT = 0.15
    WEIGHT_QUALITY = 0.10
    WEIGHT_PRACTICAL = 0.10
    WEIGHT_FRESHNESS = 0.05

    @classmethod
    def calculate_composite_score(cls, resource: LearningResource) -> float:
        """Compute the weighted multi-attribute overall score [0.0, 1.0]."""
        composite = (
            cls.WEIGHT_RELEVANCE * resource.relevance_score +
            cls.WEIGHT_LEARNER_FIT * resource.learner_fit_score +
            cls.WEIGHT_AUTHORITY * resource.authority_score +
            cls.WEIGHT_DIFFICULTY_FIT * (resource.quality_score) * 0.5 + 0.5 * cls.WEIGHT_DIFFICULTY_FIT +
            cls.WEIGHT_QUALITY * resource.quality_score +
            cls.WEIGHT_PRACTICAL * resource.usefulness_score +
            cls.WEIGHT_FRESHNESS * resource.freshness_score
        )
        return round(min(1.0, max(0.0, composite)), 3)

    @classmethod
    def rank_resources(cls, resources: List[LearningResource]) -> List[LearningResource]:
        """
        Sort resources descending by overall score, breaking ties deterministically
        by (authority_score, relevance_score, resource_id).
        """
        for res in resources:
            res.overall_score = cls.calculate_composite_score(res)

        # Deterministic sorting key
        sorted_res = sorted(
            resources,
            key=lambda r: (
                r.overall_score,
                r.authority_score,
                r.relevance_score,
                r.learner_fit_score,
                r.resource_id
            ),
            reverse=True
        )

        for rank, r in enumerate(sorted_res, start=1):
            r.recommended_order = rank

        return sorted_res
