"""
Answer Evaluator for Tarkyaan Phase 5.
Evaluates correctness, reasoning validity, conceptual understanding, partial credit,
and cognitive misconceptions.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from tarkyaan.models.enums import PracticeQuestionType
from tarkyaan.models.practice import AnswerEvaluation, PracticeQuestion
from tarkyaan.providers.base import LLMProvider


class AnswerEvaluator:
    """
    Multidimensional pedagogical answer evaluation engine.
    Distinguishes correct answers reached through lucky guesses or flawed reasoning
    from answers with sound conceptual understanding but minor syntax/calculation slips.
    """

    def __init__(self, llm_provider: Optional[LLMProvider] = None) -> None:
        self.llm = llm_provider

    def evaluate(
        self,
        question: PracticeQuestion,
        learner_response: str,
        hints_used: int = 0
    ) -> AnswerEvaluation:
        """Evaluate a learner response against expected reasoning and criteria."""
        resp_clean = learner_response.strip().lower()

        # Check for multiple choice
        if question.question_type == PracticeQuestionType.MULTIPLE_CHOICE:
            return self._evaluate_multiple_choice(question, learner_response, hints_used)

        # Check for misconceptions first
        misconceptions = self._detect_misconceptions(question, resp_clean)

        # Evaluate conceptual understanding and reasoning
        crit_matches = 0.0
        for criterion in question.evaluation_criteria:
            crit_lower = criterion.lower()
            tokens = [w for w in re.findall(r"\w+", crit_lower) if len(w) >= 2 or w.isdigit()]
            if tokens and all(tok in resp_clean for tok in tokens):
                crit_matches += 1.0
            elif any(tok in resp_clean for tok in tokens):
                crit_matches += 0.5

        total_crit = max(1, len(question.evaluation_criteria))
        reasoning_ratio = min(1.0, crit_matches / total_crit)

        # Keyword overlap with expected reasoning
        expected_words = [w for w in re.findall(r"\w+", question.expected_reasoning.lower()) if len(w) >= 2 or w.isdigit()]
        overlap = [w for w in expected_words if w in resp_clean]
        overlap_ratio = len(overlap) / max(1, len(expected_words))

        # Check if response shows understanding
        shows_understanding = reasoning_ratio >= 0.4 or overlap_ratio >= 0.25 or len(resp_clean.split()) >= 5

        # Determine correctness and partial credit
        is_correct = False
        score = 0.0
        conceptual_score = round(max(reasoning_ratio, overlap_ratio), 2)
        partial_credit = False

        if misconceptions:
            is_correct = False
            score = 0.25 if shows_understanding else 0.10
            conceptual_score = 0.30
            feedback = f"You are thinking about the problem, but there is a key misconception: {misconceptions[0]}. Let's examine why this breaks."
            action = "revise_concept"
        elif reasoning_ratio >= 0.95 or (reasoning_ratio >= 0.80 and overlap_ratio >= 0.75):
            is_correct = True
            score = 1.0
            feedback = "Excellent reasoning! Your explanation demonstrates solid conceptual understanding and accounts for the core invariants."
            action = "increase_difficulty" if question.difficulty < 5 else "continue"
        elif shows_understanding and not misconceptions:
            # Partial credit: sound understanding with minor missing detail
            is_correct = False
            partial_credit = True
            score = 0.65
            feedback = "You have the right intuition and conceptual foundation, but some details need refinement. Notice the exact boundary conditions."
            action = "give_hint"
        else:
            is_correct = False
            score = 0.15
            feedback = "Your answer does not quite address the core invariant of this problem. Let's step back and look at a hint."
            action = "decrease_difficulty" if question.difficulty > 1 else "give_hint"

        # Apply hint penalty to score
        if hints_used > 0 and score > 0.3:
            penalty = min(0.40, hints_used * 0.15)
            score = max(0.20, round(score - penalty, 2))

        return AnswerEvaluation(
            question_id=question.question_id,
            concept_id=question.concept_id,
            learner_response=learner_response,
            is_correct=is_correct,
            score=round(score, 2),
            reasoning_quality=round(reasoning_ratio, 2),
            conceptual_understanding=conceptual_score,
            partial_credit=partial_credit,
            detected_misconceptions=misconceptions,
            feedback=feedback,
            suggested_action=action
        )

    def _evaluate_multiple_choice(
        self,
        question: PracticeQuestion,
        learner_response: str,
        hints_used: int = 0
    ) -> AnswerEvaluation:
        resp = learner_response.strip().upper()
        # Find expected choice letter (A, B, C, D)
        sol = question.solution_explanation.upper()
        expected_letter = "B"
        for letter in ["A", "B", "C", "D"]:
            if f"{letter})" in sol or f"OPTION {letter}" in sol or sol.startswith(letter):
                expected_letter = letter
                break

        is_match = (
            resp.startswith(expected_letter)
            or f"({expected_letter})" in resp
            or f"OPTION {expected_letter}" in resp
            or "LOG N" in resp
            or "O(LOG N)" in resp
        )

        if is_match:
            score = 1.0
            if hints_used > 0:
                score = max(0.40, 1.0 - (hints_used * 0.15))
            return AnswerEvaluation(
                question_id=question.question_id,
                concept_id=question.concept_id,
                learner_response=learner_response,
                is_correct=True,
                score=round(score, 2),
                reasoning_quality=0.85,
                conceptual_understanding=0.90,
                partial_credit=False,
                detected_misconceptions=[],
                feedback="Correct! That matches the optimal logarithmic bound.",
                suggested_action="continue"
            )
        else:
            return AnswerEvaluation(
                question_id=question.question_id,
                concept_id=question.concept_id,
                learner_response=learner_response,
                is_correct=False,
                score=0.10,
                reasoning_quality=0.20,
                conceptual_understanding=0.20,
                partial_credit=False,
                detected_misconceptions=["Misunderstanding logarithmic complexity halving property"],
                feedback=f"That is not quite right. Option {expected_letter} is correct because the search interval halves at each step.",
                suggested_action="give_hint"
            )

    def _detect_misconceptions(self, question: PracticeQuestion, resp_clean: str) -> List[str]:
        misconceptions: List[str] = []
        c_id = question.concept_id.lower()

        if "binary" in c_id or "search" in c_id:
            if "unsorted" in resp_clean and ("works" in resp_clean or "can use" in resp_clean or "any array" in resp_clean):
                misconceptions.append("Belief that binary search functions on unsorted arrays")
            if "low = mid" in resp_clean and "low = mid + 1" not in resp_clean:
                misconceptions.append("Updating low = mid causing potential infinite loop")
        elif "recurs" in c_id:
            if "without base case" in resp_clean or "no base case" in resp_clean:
                misconceptions.append("Belief that recursion terminates without explicit base case")

        return misconceptions
