"""
Unit tests for QuestionGenerator.
Validates Socratic diagnostic question generation, tier targeting, and difficulty scaling.
"""

import pytest

from tarkyaan.assessment.question_generator import QuestionGenerator
from tarkyaan.knowledge.prerequisite_graph import PrerequisiteDAG
from tarkyaan.models.diagnostic import DiagnosticDimension, QuestionType
from tarkyaan.models.learner import LearnerProfile


class TestQuestionGenerator:
    @pytest.fixture
    def learner(self):
        return LearnerProfile(
            display_name="Aarav",
            primary_domain="Computer Science / DSA",
            preferred_language="Python"
        )

    def test_high_uncertainty_targets_understanding(self, learner):
        q = QuestionGenerator.generate_question(
            learner=learner,
            concept_id="recursion",
            concept_name="Recursion Fundamentals",
            current_mastery=0.1,
            uncertainty=0.9
        )
        assert q.diagnostic_dimension == DiagnosticDimension.UNDERSTANDING
        assert q.difficulty == 1
        assert "recursion fundamentals" in q.prompt.lower()
        assert q.question_type in (QuestionType.CONCEPTUAL, QuestionType.WHY, QuestionType.WHAT_IF)

    def test_competent_mastery_targets_application(self, learner):
        q = QuestionGenerator.generate_question(
            learner=learner,
            concept_id="binary_search",
            concept_name="Binary Search",
            current_mastery=0.72,
            uncertainty=0.25
        )
        assert q.diagnostic_dimension == DiagnosticDimension.APPLICATION
        assert q.difficulty >= 3
        assert q.question_type in (QuestionType.APPLICATION, QuestionType.DEBUGGING, QuestionType.CODE_WRITING)

    def test_prerequisite_awareness_in_prompt(self, learner):
        dag = PrerequisiteDAG()
        dag.add_prerequisite("trees", "recursion")

        q = QuestionGenerator.generate_question(
            learner=learner,
            concept_id="trees",
            concept_name="Binary Trees",
            current_mastery=0.3,
            uncertainty=0.5,
            dag=dag
        )
        assert "recursion" in q.prerequisite_concepts
        assert "recursion" in q.prompt.lower()

    def test_question_type_rotation(self, learner):
        # Generate question 1
        q1 = QuestionGenerator.generate_question(
            learner=learner,
            concept_id="graph_dfs",
            concept_name="Graph DFS",
            current_mastery=0.2,
            uncertainty=0.8,
            previous_questions=[]
        )

        # Generate question 2 for same concept
        q2 = QuestionGenerator.generate_question(
            learner=learner,
            concept_id="graph_dfs",
            concept_name="Graph DFS",
            current_mastery=0.2,
            uncertainty=0.8,
            previous_questions=[q1]
        )

        assert q1.question_type != q2.question_type
