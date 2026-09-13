"""
Unit tests for AnswerEvaluator and DiagnosticEvidence separation.
"""

import pytest

from tarkyaan.assessment.answer_evaluator import AnswerEvaluator
from tarkyaan.models.diagnostic import (
    DiagnosticDimension,
    DiagnosticQuestion,
    QuestionType,
)
from tarkyaan.models.enums import EpistemicStatus, MasteryTier


class TestAnswerEvaluator:
    @pytest.fixture
    def question(self):
        return DiagnosticQuestion(
            concept_id="binary_search",
            difficulty=3,
            diagnostic_dimension=DiagnosticDimension.UNDERSTANDING,
            question_type=QuestionType.CONCEPTUAL,
            prompt="Explain how Binary Search guarantees O(log n) time complexity.",
            expected_reasoning="Learner explains that dividing the sorted search space in half at each step yields logarithmic steps.",
            evaluation_rubric={
                "keywords": ["divide", "half", "sorted", "search space"],
                "expected_depth": "first_principles"
            }
        )

    def test_strong_reasoning_evaluation(self, question):
        response = (
            "Binary search requires a sorted array. At each iteration, it compares the target with the mid element "
            "and divides the search space in half, which guarantees that after k steps n / 2^k = 1, giving O(log n) complexity."
        )
        evidence = AnswerEvaluator.evaluate(
            learner_id="l_test",
            question=question,
            response_text=response
        )

        assert evidence.observation.epistemic_status == EpistemicStatus.FACT
        assert evidence.evaluation.epistemic_status == EpistemicStatus.INFERENCE
        assert evidence.evaluation.correctness >= 0.8
        assert evidence.evaluation.reasoning_quality >= 0.7
        assert evidence.evaluation.evaluated_tier in (MasteryTier.COMPETENT, MasteryTier.MASTERED)
        assert evidence.composite_score >= 0.75

    def test_trivial_answer_penalized(self, question):
        evidence = AnswerEvaluator.evaluate(
            learner_id="l_test",
            question=question,
            response_text="idk"
        )
        assert evidence.evaluation.correctness <= 0.2
        assert len(evidence.evaluation.detected_errors) > 0
        assert evidence.composite_score <= 0.2

    def test_false_assumption_error_detection(self, question):
        response = "Binary search works on any unsorted list by checking random midpoints."
        evidence = AnswerEvaluator.evaluate(
            learner_id="l_test",
            question=question,
            response_text=response
        )
        assert evidence.evaluation.correctness <= 0.3
        errors_str = " ".join(evidence.evaluation.detected_errors)
        assert "unsorted" in errors_str.lower()
        assert len(evidence.evaluation.candidate_misconceptions) > 0

    def test_submitted_code_evaluation(self, question):
        code = "int search(int arr[], int target) { int left = 0, right = 10; while(left <= right) { int mid = (left+right)/2; } return -1; }"
        response = "Implementation with while loop dividing space."
        evidence = AnswerEvaluator.evaluate(
            learner_id="l_test",
            question=question,
            response_text=response,
            submitted_code=code
        )
        assert evidence.observation.submitted_code == code
        assert evidence.evaluation.application_score >= 0.7
