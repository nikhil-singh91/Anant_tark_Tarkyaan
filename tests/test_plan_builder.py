"""
Unit tests for PlanBuilder.
Tests end-to-end plan assembly, structured explanation generation,
phase construction, task generation, and milestone synthesis.
"""

import pytest

from tarkyaan.knowledge.prerequisite_graph import PrerequisiteDAG
from tarkyaan.models.enums import LearningStrategy, PlanValidationStatus
from tarkyaan.models.gaps import KnowledgeGap
from tarkyaan.models.goals import LearningGoal
from tarkyaan.models.learner import LearnerProfile
from tarkyaan.models.mastery import TopicMastery
from tarkyaan.planning.plan_builder import PlanBuilder


class TestPlanBuilder:
    @pytest.fixture
    def learner(self):
        return LearnerProfile(
            display_name="Divya",
            primary_domain="Computer Science",
            preferred_language="Python",
            daily_time_budget_minutes=60
        )

    @pytest.fixture
    def goal(self):
        return LearningGoal(
            learner_id="l_divya",
            title="Master Graph Traversal",
            target_outcome="Solve BFS and DFS problems in competitive programming"
        )

    @pytest.fixture
    def dag(self):
        dag = PrerequisiteDAG()
        dag.add_concept("arrays", "Arrays", "cs")
        dag.add_concept("queues", "Queues", "cs")
        dag.add_concept("recursion", "Recursion", "cs")
        dag.add_concept("graphs", "Graph Traversal", "cs")
        dag.add_prerequisite("queues", "arrays")
        dag.add_prerequisite("graphs", "queues")
        dag.add_prerequisite("graphs", "recursion")
        return dag

    def test_end_to_end_plan_synthesis(self, learner, goal, dag):
        masteries = {
            "arrays": TopicMastery(learner_id=learner.learner_id, topic_id="arrays", mastery_score=0.85, uncertainty=0.2),
            "queues": TopicMastery(learner_id=learner.learner_id, topic_id="queues", mastery_score=0.45, uncertainty=0.4),
            "recursion": TopicMastery(learner_id=learner.learner_id, topic_id="recursion", mastery_score=0.20, uncertainty=0.7),
            "graphs": TopicMastery(learner_id=learner.learner_id, topic_id="graphs", mastery_score=0.0, uncertainty=1.0),
        }
        gap = KnowledgeGap(
            learner_id=learner.learner_id,
            concept_id="recursion",
            blocking_topic_id="graphs",
            severity="critical",
            diagnostic_evidence="Failed recursive call trace"
        )

        plan = PlanBuilder.build(
            learner=learner,
            goal=goal,
            mastery_map=masteries,
            gaps=[gap],
            dag=dag
        )

        assert plan.learner_id == learner.learner_id
        assert plan.goal_id == goal.goal_id
        assert len(plan.phases) >= 2
        assert len(plan.tasks) >= 3
        assert len(plan.milestones) >= 2
        assert plan.validation_status in (PlanValidationStatus.VALID, PlanValidationStatus.WARNING)

        # Workload calculation
        assert plan.total_estimated_hours > 0.0
        assert plan.estimated_total_minutes > 0

        # Structured explanation verification
        assert plan.explanation is not None
        assert "recursion" in str(plan.explanation.prioritized_gaps).lower()
        assert len(plan.explanation.summary) > 10

    def test_mastered_concept_generates_review_only(self, learner, goal, dag):
        # 'arrays' is mastered (0.95), so it should not receive a heavy learn task
        masteries = {
            "arrays": TopicMastery(learner_id=learner.learner_id, topic_id="arrays", mastery_score=0.95, uncertainty=0.1),
            "graphs": TopicMastery(learner_id=learner.learner_id, topic_id="graphs", mastery_score=0.10, uncertainty=0.8),
        }
        plan = PlanBuilder.build(
            learner=learner,
            goal=goal,
            mastery_map=masteries,
            dag=dag
        )

        array_tasks = [t for t in plan.tasks if t.concept_id == "arrays"]
        if array_tasks:
            # All array tasks should be review / brief
            for t in array_tasks:
                assert t.estimated_minutes <= 30
