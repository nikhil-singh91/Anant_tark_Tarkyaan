"""
Progressive Hint Engine for Tarkyaan Phase 5.
Enforces the strict Anti-Answer-Dumping rule: hints are delivered incrementally
across 5 distinct pedagogical tiers before any full solution is revealed.
"""

from __future__ import annotations

from typing import Optional
from tarkyaan.models.enums import HintLevel
from tarkyaan.models.practice import HintRequest, HintResponse, PracticeQuestion


class HintEngine:
    """
    Pedagogical hint delivery controller.
    Ensures learners do active mental heavy lifting rather than passive solution copying.
    """

    HINT_TIER_DESCRIPTIONS = {
        HintLevel.NUDGE: "Gentle conceptual nudge",
        HintLevel.PRINCIPLE: "Governing algorithmic principle",
        HintLevel.DIRECTION: "Concrete strategic direction",
        HintLevel.STRONG_GUIDANCE: "Structural skeleton or near-solution guidance",
        HintLevel.NEAR_SOLUTION: "Penultimate step walkthrough",
        HintLevel.FULL_SOLUTION: "Complete solution explanation",
    }

    HINT_PENALTY_PER_TIER: float = 0.15

    @classmethod
    def get_hint(
        cls,
        question: PracticeQuestion,
        request: HintRequest,
        allow_solution: bool = False
    ) -> HintResponse:
        """
        Deliver the next calibrated hint based on request level.
        Enforces anti-answer-dumping by refusing immediate solution disclosure unless authorized.
        """
        requested_level = request.requested_level
        hints = question.hints or []

        # If learner explicitly asks for full solution
        if requested_level == HintLevel.FULL_SOLUTION:
            if allow_solution or request.attempt_count >= 2 or len(hints) <= 1:
                return HintResponse(
                    question_id=question.question_id,
                    hint_level=HintLevel.FULL_SOLUTION,
                    hint_text=question.solution_explanation or "Full solution details unavailable.",
                    remaining_hints=0,
                    is_final_hint=True,
                    pedagogical_nudge="Here is the full solution. Notice how each step connects to the underlying invariant."
                )
            else:
                # Anti-Answer-Dumping: guide them with highest available progressive hint first
                requested_level = HintLevel.STRONG_GUIDANCE

        # Map HintLevel to list index (1-based to 0-based)
        target_idx = min(len(hints) - 1, max(0, int(requested_level) - 1)) if hints else 0
        hint_str = hints[target_idx] if hints and target_idx < len(hints) else "Review the core invariant of this problem."

        remaining = max(0, len(hints) - (target_idx + 1))
        is_final = remaining == 0 or requested_level == HintLevel.NEAR_SOLUTION

        nudge = (
            "Take your time to reason through this hint."
            if not is_final
            else "This is the final progressive hint. Give it your best attempt!"
        )

        return HintResponse(
            question_id=question.question_id,
            hint_level=requested_level,
            hint_text=hint_str,
            remaining_hints=remaining,
            is_final_hint=is_final,
            pedagogical_nudge=nudge
        )

    @classmethod
    def calculate_hint_penalty(cls, hints_used_count: int) -> float:
        """
        Calculate evidence score penalty based on hint consumption.
        Each hint reduces raw score by 0.15 (clamped so max penalty is 0.60).
        """
        return min(0.60, max(0.0, float(hints_used_count) * cls.HINT_PENALTY_PER_TIER))
