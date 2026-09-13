"""
Unit tests for GoalDecomposer.
Tests goal breakdown across multi-domain subjects (DSA, ML, Physics, Math).
"""

import pytest

from tarkyaan.knowledge.prerequisite_graph import PrerequisiteDAG
from tarkyaan.models.goals import LearningGoal
from tarkyaan.models.learner import LearnerProfile
from tarkyaan.planning.goal_decomposer import GoalDecomposer


class TestGoalDecomposer:
    @pytest.fixture
    def learner(self):
        return LearnerProfile(
            display_name="Ishan",
            primary_domain="Computer Science / DSA",
            preferred_language="Python"
        )

    def test_dsa_goal_decomposition(self, learner):
        goal = LearningGoal(
            learner_id=learner.learner_id,
            title="Master Dynamic Programming",
            target_outcome="Solve medium and hard dynamic programming problems in interviews"
        )
        decomposed = GoalDecomposer.decompose(goal=goal, learner=learner)

        assert decomposed.domain == "dsa"
        assert len(decomposed.target_concepts) > 0
        assert len(decomposed.required_competencies) > 0
        assert len(decomposed.practice_requirements) > 0

    def test_multi_domain_machine_learning_decomposition(self):
        ml_learner = LearnerProfile(
            display_name="Pooja",
            primary_domain="Machine Learning",
            preferred_language="Python"
        )
        goal = LearningGoal(
            learner_id=ml_learner.learner_id,
            title="Understand Deep Neural Networks",
            target_outcome="Implement backpropagation and train multi-layer perceptrons"
        )
        decomposed = GoalDecomposer.decompose(goal=goal, learner=ml_learner)

        assert decomposed.domain == "machine learning"
        assert any("gradient" in c or "neural" in c or "regression" in c for c in decomposed.target_concepts)

    def test_dag_aware_concept_discovery(self, learner):
        dag = PrerequisiteDAG()
        dag.add_concept("functions", "Functions", "cs")
        dag.add_concept("stack_memory", "Stack Memory", "cs")
        dag.add_concept("recursion", "Recursion", "cs")
        dag.add_concept("trees", "Binary Trees", "cs")
        dag.add_prerequisite("recursion", "functions")
        dag.add_prerequisite("recursion", "stack_memory")
        dag.add_prerequisite("trees", "recursion")

        goal = LearningGoal(
            learner_id=learner.learner_id,
            title="Learn Binary Trees",
            target_outcome="Traverse and manipulate binary trees"
        )
        decomposed = GoalDecomposer.decompose(goal=goal, learner=learner, dag=dag)

        assert "trees" in decomposed.target_concepts
        # Ancestor prerequisites should be discovered
        assert "recursion" in decomposed.prerequisite_concepts or "functions" in decomposed.prerequisite_concepts

    def test_milestone_token_incorporation(self, learner):
        goal = LearningGoal(
            learner_id=learner.learner_id,
            title="Prepare for coding interviews",
            target_outcome="Solve leetcode problems",
            milestones=["two_pointers", "sliding_window", "binary_search"]
        )
        decomposed = GoalDecomposer.decompose(goal=goal, learner=learner)

        assert "two_pointers" in decomposed.target_concepts
        assert "sliding_window" in decomposed.target_concepts
