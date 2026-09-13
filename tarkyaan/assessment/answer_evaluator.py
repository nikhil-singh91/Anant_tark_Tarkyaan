"""
Diagnostic Answer Evaluator.
Analyzes learner responses against rubric criteria and expected reasoning,
extracts errors, detects candidate misconceptions, and computes structured evidence.
"""

from __future__ import annotations

import re
import uuid
from typing import Any, Dict, List, Optional

from tarkyaan.assessment.evidence import (
    DiagnosticEvidence,
    InferredEvaluation,
    ObservedEvidence,
)
from tarkyaan.knowledge.misconception_detector import (
    CandidateMisconception,
    MisconceptionDetector,
)
from tarkyaan.models.diagnostic import DiagnosticQuestion, QuestionType
from tarkyaan.models.enums import EpistemicStatus, MasteryTier
from tarkyaan.models.gaps import MisconceptionRecord


class AnswerEvaluator:
    """
    Evaluates learner responses to diagnostic questions.
    Produces structured DiagnosticEvidence containing observed facts and model inferences.
    """

    @classmethod
    def evaluate(
        cls,
        learner_id: str,
        question: DiagnosticQuestion,
        response_text: str,
        submitted_code: Optional[str] = None,
        time_taken_seconds: float = 0.0,
        prior_mastery: float = 0.0,
        recent_scores: Optional[List[float]] = None,
        session_duration_minutes: float = 0.0,
        prior_misconceptions: Optional[List[MisconceptionRecord]] = None
    ) -> DiagnosticEvidence:
        """
        Evaluate a learner response deterministically against expected reasoning and rubrics.
        """
        text = response_text.strip()
        code = submitted_code.strip() if submitted_code else None

        # 1. Compute rubric matching scores
        rubric = question.evaluation_rubric or {}
        keywords = rubric.get("keywords", [])

        # Count keyword hits
        keyword_hits = sum(1 for kw in keywords if kw.lower() in text.lower()) if keywords else 1
        keyword_ratio = (keyword_hits / len(keywords)) if keywords else 0.8

        # Check for superficial / non-answers
        if len(text) < 10 and not code:
            correctness = 0.1
            reasoning_quality = 0.1
            application_score = 0.1
            detected_errors = ["Unresponsive or trivial answer"]
        else:
            # Analyze reasoning depth
            explanation_markers = [
                "because", "since", "so that", "therefore", "guarantees", "invariant",
                "ensures", "maintaining", "maintains", "order", "stack", "return",
                "allocates", "lifo", "base case", "terminates"
            ]
            has_explanation = any(w in text.lower() for w in explanation_markers)
            has_complexity = bool(re.search(r"o\([0-9nkm log\^]+\)", text, re.IGNORECASE))
            is_substantive = len(text) > 45

            # If no keywords matched and no explanation, the answer is irrelevant or incorrect
            if keyword_hits == 0 and not has_explanation and not code:
                correctness = 0.15
                reasoning_quality = 0.15
                application_score = 0.15
                detected_errors = [f"Irrelevant or incorrect response for {question.concept_id}"]
            else:
                base_c = 0.30 if keyword_hits > 0 else 0.15
                correctness = min(1.0, base_c + (keyword_ratio * 0.40) + (0.15 if is_substantive else 0.0) + (0.15 if has_explanation else 0.0))
                reasoning_quality = min(1.0, (0.65 if has_explanation else 0.35) + (0.25 if has_complexity else 0.10) + (0.10 if is_substantive else 0.0))
                application_score = 0.85 if code else (0.75 if has_explanation else 0.45)
                detected_errors = []

            # Check for error patterns
            if "unsorted" in text.lower() and ("binary search" in question.prompt.lower() or "binary search" in text.lower()):
                detected_errors.append("false_assumption: assumed binary search functions on unsorted arrays")
                correctness = 0.15
                reasoning_quality = 0.20
                application_score = 0.20
            if "o(n)" in text.lower() and "tree" in question.prompt.lower() and "branching" in question.expected_reasoning.lower():
                detected_errors.append("false_assumption: assumed branching recursion is linear O(n)")
                correctness = 0.25
                reasoning_quality = 0.30
                application_score = 0.30

            if code and ("while" in code or "for" in code) and ("<=" not in code and "<" not in code):
                detected_errors.append("off_by_one: missing boundary check in loop")
                application_score = 0.30

        # 2. Run Misconception Detector only if deficits/errors exist
        candidate_misconceptions = []
        if detected_errors or correctness < 0.60:
            candidate_misconceptions = MisconceptionDetector.evaluate_error(
                learner_id=learner_id,
                topic_id=question.concept_id,
                error_tags=detected_errors,
                reasoning_excerpt=text[:150],
                code_snippet=code,
                prior_mastery=prior_mastery,
                recent_scores=recent_scores,
                session_duration_minutes=session_duration_minutes,
                prior_misconceptions=prior_misconceptions
            )

        misc_strings = [c.description for c in candidate_misconceptions]

        # 3. Determine evaluated tier
        composite = 0.5 * correctness + 0.3 * reasoning_quality + 0.2 * application_score
        if composite >= 0.88:
            evaluated_tier = MasteryTier.MASTERED
        elif composite >= 0.70:
            evaluated_tier = MasteryTier.COMPETENT
        elif composite >= 0.40:
            evaluated_tier = MasteryTier.PRACTICING
        elif composite > 0.15:
            evaluated_tier = MasteryTier.INTRODUCED
        else:
            evaluated_tier = MasteryTier.UNEXPLORED

        # 4. Formulate Observation and Inference
        observation = ObservedEvidence(
            evidence_id=f"ev_{uuid.uuid4().hex[:8]}",
            question_id=question.question_id,
            concept_id=question.concept_id,
            raw_response_text=text,
            submitted_code=code,
            time_taken_seconds=time_taken_seconds,
            epistemic_status=EpistemicStatus.FACT
        )

        evaluation = InferredEvaluation(
            evaluation_id=f"eval_{uuid.uuid4().hex[:8]}",
            correctness=round(correctness, 4),
            reasoning_quality=round(reasoning_quality, 4),
            application_score=round(application_score, 4),
            confidence=0.85 if len(text) > 30 else 0.60,
            evaluated_tier=evaluated_tier,
            detected_errors=detected_errors,
            candidate_misconceptions=misc_strings,
            reasoning_critique=f"Evaluated against rubric for {question.question_type.value}: {keyword_hits} keyword hits.",
            epistemic_status=EpistemicStatus.INFERENCE
        )

        return DiagnosticEvidence(
            evidence_id=f"diag_ev_{uuid.uuid4().hex[:8]}",
            learner_id=learner_id,
            concept_id=question.concept_id,
            observation=observation,
            evaluation=evaluation
        )
