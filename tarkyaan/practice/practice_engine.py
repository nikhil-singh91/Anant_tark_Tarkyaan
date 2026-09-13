"""
Practice Engine for Tarkyaan Phase 5.
Coordinates exercise generation, progressive hint delivery, answer evaluation,
and adaptive difficulty pacing.
"""

from __future__ import annotations

from typing import Dict, List, Optional
from tarkyaan.models.enums import HintLevel, PracticeQuestionType
from tarkyaan.models.practice import (
    AnswerEvaluation,
    HintRequest,
    HintResponse,
    PracticeQuestion,
)
from tarkyaan.practice.answer_evaluator import AnswerEvaluator
from tarkyaan.practice.hint_engine import HintEngine
from tarkyaan.practice.question_generator import PracticeQuestionGenerator
from tarkyaan.providers.base import LLMProvider


class PracticeEngine:
    """
    Pedagogical practice coordinator.
    Manages exercise difficulty pacing, hint distribution, and answer evaluation.
    """

    def __init__(self, llm_provider: Optional[LLMProvider] = None) -> None:
        self.question_generator = PracticeQuestionGenerator()
        self.hint_engine = HintEngine()
        self.evaluator = AnswerEvaluator(llm_provider=llm_provider)
        self._consecutive_correct: int = 0
        self._consecutive_incorrect: int = 0

    def generate_practice(
        self,
        concept_id: str,
        concept_name: Optional[str] = None,
        difficulty: int = 2,
        question_type: Optional[PracticeQuestionType] = None,
        session_id: Optional[str] = None,
        learner_id: str = ""
    ) -> PracticeQuestion:
        """Generate an exercise appropriate for the target concept and difficulty."""
        return self.question_generator.generate_question(
            concept_id=concept_id,
            concept_name=concept_name,
            difficulty=difficulty,
            question_type=question_type,
            session_id=session_id,
            learner_id=learner_id
        )

    def request_hint(
        self,
        question: PracticeQuestion,
        requested_level: HintLevel = HintLevel.NUDGE,
        attempt_count: int = 0,
        session_id: Optional[str] = None,
        allow_full_solution: bool = False
    ) -> HintResponse:
        """
        Deliver progressive hint while respecting the anti-answer-dumping rule.
        """
        req = HintRequest(
            question_id=question.question_id,
            session_id=session_id,
            requested_level=requested_level,
            attempt_count=attempt_count
        )
        return self.hint_engine.get_hint(
            question=question,
            request=req,
            allow_solution=allow_full_solution
        )

    def evaluate_response(
        self,
        question: PracticeQuestion,
        learner_response: str,
        hints_used: int = 0
    ) -> AnswerEvaluation:
        """
        Evaluate student response and update difficulty pacing metrics.
        """
        eval_result = self.evaluator.evaluate(
            question=question,
            learner_response=learner_response,
            hints_used=hints_used
        )

        if eval_result.is_correct or eval_result.score >= 0.70:
            self._consecutive_correct += 1
            self._consecutive_incorrect = 0
        else:
            self._consecutive_incorrect += 1
            self._consecutive_correct = 0

        return eval_result

    def recommend_next_difficulty(self, current_difficulty: int) -> int:
        """
        Adapt difficulty dynamically:
        Increase after 2 consecutive successes; decrease after 2 consecutive struggles.
        """
        if self._consecutive_correct >= 2:
            return min(5, current_difficulty + 1)
        elif self._consecutive_incorrect >= 2:
            return max(1, current_difficulty - 1)
        return current_difficulty
