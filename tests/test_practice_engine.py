"""
Unit and Integration Tests for Tarkyaan Interactive Practice Engine (Phase 5).
Verifies question generation across Levels 1-5, strict progressive 5-tier hints,
anti-answer-dumping enforcement, reasoning evaluation, and dynamic difficulty pacing.
"""

import pytest
from tarkyaan.models.enums import HintLevel, PracticeQuestionType
from tarkyaan.models.practice import HintRequest
from tarkyaan.practice.answer_evaluator import AnswerEvaluator
from tarkyaan.practice.hint_engine import HintEngine
from tarkyaan.practice.practice_engine import PracticeEngine
from tarkyaan.practice.question_generator import PracticeQuestionGenerator


class TestQuestionGenerator:
    def test_generates_questions_across_all_difficulty_levels(self):
        for diff in range(1, 6):
            q = PracticeQuestionGenerator.generate_question("binary_search", difficulty=diff)
            assert q.concept_id == "binary_search"
            assert q.difficulty == diff
            assert len(q.prompt) > 10
            assert len(q.hints) == 5  # Exactly 5 progressive hint strings
            assert len(q.evaluation_criteria) >= 1
            assert len(q.solution_explanation) > 10

    def test_generates_mcq_with_options(self):
        q = PracticeQuestionGenerator.generate_question(
            "binary_search", difficulty=1, question_type=PracticeQuestionType.MULTIPLE_CHOICE
        )
        # Check that options or prompt contain choices
        assert q.options or ("A)" in q.prompt and "B)" in q.prompt)

    def test_generates_recursion_exercises(self):
        q_trace = PracticeQuestionGenerator.generate_question("recursion", difficulty=3)
        assert q_trace.question_type == PracticeQuestionType.CODE_TRACE
        assert "factorial" in q_trace.prompt.lower() or "call stack" in q_trace.prompt.lower()

        q_debug = PracticeQuestionGenerator.generate_question("recursion", difficulty=4)
        assert q_debug.question_type == PracticeQuestionType.DEBUGGING
        assert "recursionerror" in q_debug.prompt.lower() or "bug" in q_debug.prompt.lower()


class TestHintEngineAndAntiAnswerDumping:
    def test_progressive_hint_delivery_5_tiers(self):
        q = PracticeQuestionGenerator.generate_question("binary_search", difficulty=2)

        # Tier 1: Nudge
        h1 = HintEngine.get_hint(q, HintRequest(question_id=q.question_id, requested_level=HintLevel.NUDGE))
        assert h1.hint_level == HintLevel.NUDGE
        assert h1.remaining_hints >= 3
        assert h1.is_final_hint is False

        # Tier 2: Principle
        h2 = HintEngine.get_hint(q, HintRequest(question_id=q.question_id, requested_level=HintLevel.PRINCIPLE))
        assert h2.hint_level == HintLevel.PRINCIPLE

        # Tier 5: Near Solution
        h5 = HintEngine.get_hint(q, HintRequest(question_id=q.question_id, requested_level=HintLevel.NEAR_SOLUTION))
        assert h5.hint_level == HintLevel.NEAR_SOLUTION
        assert h5.is_final_hint is True

    def test_anti_answer_dumping_prevents_immediate_solution_leak(self):
        q = PracticeQuestionGenerator.generate_question("binary_search", difficulty=2)

        # First attempt requesting full solution without authorization
        req = HintRequest(question_id=q.question_id, requested_level=HintLevel.FULL_SOLUTION, attempt_count=0)
        h_blocked = HintEngine.get_hint(q, req, allow_solution=False)

        # Must NOT be full solution; downgraded to strong guidance
        assert h_blocked.hint_level != HintLevel.FULL_SOLUTION
        assert h_blocked.hint_level == HintLevel.STRONG_GUIDANCE

        # With explicit authorization or repeated attempts, solution is released
        h_allowed = HintEngine.get_hint(q, req, allow_solution=True)
        assert h_allowed.hint_level == HintLevel.FULL_SOLUTION
        assert h_allowed.is_final_hint is True
        assert len(h_allowed.hint_text) > 10

    def test_hint_penalty_calculation(self):
        assert HintEngine.calculate_hint_penalty(0) == 0.0
        assert HintEngine.calculate_hint_penalty(1) == 0.15
        assert HintEngine.calculate_hint_penalty(2) == 0.30
        assert HintEngine.calculate_hint_penalty(10) == 0.60  # Clamped maximum


class TestAnswerEvaluator:
    def test_evaluates_correct_reasoning_and_application(self):
        evaluator = AnswerEvaluator()
        q = PracticeQuestionGenerator.generate_question("binary_search", difficulty=2)
        # Expected: low=0, high=9, mid=4, arr[4]=16
        student_resp = "low is 0, high is 9, mid is 4, and arr[mid] is 16."

        res = evaluator.evaluate(q, student_resp)
        assert res.is_correct is True
        assert res.score >= 0.85
        assert res.reasoning_quality >= 0.70
        assert res.suggested_action in ("increase_difficulty", "continue")

    def test_evaluates_mcq_accurately(self):
        evaluator = AnswerEvaluator()
        q = PracticeQuestionGenerator.generate_question(
            "binary_search", difficulty=1, question_type=PracticeQuestionType.MULTIPLE_CHOICE
        )

        # Correct selection: B (O(log N))
        res_correct = evaluator.evaluate(q, "B) O(log N)")
        assert res_correct.is_correct is True
        assert res_correct.score == 1.0

        # Incorrect selection: C (O(N))
        res_incorrect = evaluator.evaluate(q, "C) O(N)")
        assert res_incorrect.is_correct is False
        assert res_incorrect.score <= 0.20

    def test_detects_misconceptions_and_suggests_revision(self):
        evaluator = AnswerEvaluator()
        q = PracticeQuestionGenerator.generate_question("binary_search", difficulty=1)

        student_resp = "Binary search works on any unsorted array because you can always check the middle."
        res = evaluator.evaluate(q, student_resp)

        assert res.is_correct is False
        assert len(res.detected_misconceptions) >= 1
        assert "unsorted" in res.detected_misconceptions[0].lower()
        assert res.suggested_action == "revise_concept"

    def test_awards_partial_credit_for_sound_intuition_with_minor_slips(self):
        evaluator = AnswerEvaluator()
        q = PracticeQuestionGenerator.generate_question("binary_search", difficulty=2)

        # Partially correct: mentions low, high, mid but misses checking value
        student_resp = "We set low to 0 and high to 9, so the middle index is 4."
        res = evaluator.evaluate(q, student_resp)

        assert res.partial_credit is True
        assert res.score >= 0.50
        assert res.score < 1.0


class TestPracticeEnginePacing:
    def test_dynamic_difficulty_escalation(self):
        engine = PracticeEngine()
        q = engine.generate_practice("binary_search", difficulty=2)

        # Two consecutive correct answers
        engine.evaluate_response(q, "low is 0, high is 9, mid is 4, and arr[mid] is 16.")
        engine.evaluate_response(q, "low is 0, high is 9, mid is 4, and arr[mid] is 16.")

        next_diff = engine.recommend_next_difficulty(2)
        assert next_diff == 3

    def test_dynamic_difficulty_deescalation(self):
        engine = PracticeEngine()
        q = engine.generate_practice("binary_search", difficulty=3)

        # Two consecutive incorrect answers
        engine.evaluate_response(q, "wrong guess")
        engine.evaluate_response(q, "another incorrect guess")

        next_diff = engine.recommend_next_difficulty(3)
        assert next_diff == 2
