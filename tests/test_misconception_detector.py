"""
Unit tests for MisconceptionDetector.
Validates categorization (conceptual, algorithmic, syntax, fatigue) and anti-hallucination rules.
"""

import pytest

from tarkyaan.knowledge.misconception_detector import MisconceptionDetector
from tarkyaan.models.enums import MisconceptionCategory
from tarkyaan.models.gaps import MisconceptionRecord


class TestMisconceptionDetector:
    def test_algorithmic_logic_detection(self):
        cands = MisconceptionDetector.evaluate_error(
            learner_id="l1",
            topic_id="binary_search",
            error_tags=["off_by_one: missing boundary check in loop"],
            reasoning_excerpt="left < right instead of left <= right",
            code_snippet="while(left < right)"
        )
        assert len(cands) >= 1
        assert cands[0].category == MisconceptionCategory.ALGORITHMIC_LOGIC
        assert "boundary" in cands[0].description.lower()

    def test_syntax_friction_detection(self):
        cands = MisconceptionDetector.evaluate_error(
            learner_id="l1",
            topic_id="cpp_templates",
            error_tags=["syntax: undefined_identifier"],
            reasoning_excerpt="Forgot typename in template definition",
            code_snippet="template<class T> T::iterator it;"
        )
        assert len(cands) >= 1
        assert cands[0].category == MisconceptionCategory.SYNTAX_IDIOM

    def test_single_wrong_answer_never_flags_fatigue(self):
        """
        CRITICAL RULE: Never diagnose cognitive fatigue purely from one wrong answer!
        """
        cands = MisconceptionDetector.evaluate_error(
            learner_id="l1",
            topic_id="arrays",
            error_tags=["wrong_answer"],
            reasoning_excerpt="Forgot to return length",
            session_duration_minutes=20.0,
            prior_mastery=0.2
        )
        # Fatigue MUST NOT be in candidates
        categories = {c.category for c in cands}
        assert MisconceptionCategory.COGNITIVE_FATIGUE not in categories

    def test_fatigue_detection_requires_sustained_duration_and_drop(self):
        cands = MisconceptionDetector.evaluate_error(
            learner_id="l1",
            topic_id="dp",
            error_tags=["trivial_error"],
            reasoning_excerpt="I am making silly typos",
            session_duration_minutes=90.0,  # > 75 min
            prior_mastery=0.85,             # Had prior competence
            recent_scores=[0.9, 0.85, 0.88, 0.15]  # Sudden plunge
        )
        categories = {c.category for c in cands}
        assert MisconceptionCategory.COGNITIVE_FATIGUE in categories

    def test_cumulative_confidence_on_repeated_errors(self):
        # First error
        cands1 = MisconceptionDetector.evaluate_error(
            learner_id="l1",
            topic_id="recursion",
            error_tags=["false_assumption"],
            prior_misconceptions=[]
        )
        conf1 = cands1[0].confidence

        # Second identical error with previous record present
        prior_rec = MisconceptionRecord(
            learner_id="l1",
            topic_id="recursion",
            category=MisconceptionCategory.CONCEPTUAL,
            description="Flawed recursion tree model"
        )
        cands2 = MisconceptionDetector.evaluate_error(
            learner_id="l1",
            topic_id="recursion",
            error_tags=["false_assumption"],
            prior_misconceptions=[prior_rec]
        )
        conf2 = cands2[0].confidence

        assert conf2 > conf1
