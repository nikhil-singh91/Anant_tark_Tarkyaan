"""
Unit tests for PlanBuilder.
Tests end-to-end plan assembly, structured explanation generation,
phase construction, task generation, and milestone synthesis.
"""

import pytest

from tarkyaan.knowledge.prerequisite_graph import PrerequisiteDAG
from tarkyaan.models.enums import LearningStrategy, PlanValidationStatus, TaskType
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

    def test_nikhil_competitive_programming_acceptance_scenario(self):
        """
        Acceptance Test from Section 26:
        Learner: Nikhil
        Goal: 'Become strong at DSA for competitive programming'
        Knowledge: Arrays strong, Strings moderate, Hashing weak, Recursion weak, Trees unknown, Graphs unknown.
        Gaps: Hashing fundamentals, Recursion fundamentals, Tree foundations.
        Prerequisites: Recursion -> Trees -> Graphs; Hashing -> frequency patterns.
        """
        learner = LearnerProfile(
            display_name="Nikhil",
            primary_domain="Computer Science / DSA",
            preferred_language="C++",
            daily_time_budget_minutes=85  # ~10 hours/week
        )
        goal = LearningGoal(
            learner_id=learner.learner_id,
            title="Become strong at DSA for competitive programming",
            target_outcome="Solve medium and hard competitive programming problems in C++"
        )
        dag = PrerequisiteDAG()
        dag.add_concept("arrays", "Arrays", "dsa")
        dag.add_concept("strings", "Strings", "dsa")
        dag.add_concept("hashing", "Hashing", "dsa")
        dag.add_concept("recursion", "Recursion", "dsa")
        dag.add_concept("trees", "Trees", "dsa")
        dag.add_concept("graphs", "Graphs", "dsa")
        dag.add_prerequisite("hashing", "arrays")
        dag.add_prerequisite("trees", "recursion")
        dag.add_prerequisite("graphs", "trees")

        masteries = {
            "arrays": TopicMastery(learner_id=learner.learner_id, topic_id="arrays", mastery_score=0.92, uncertainty=0.15),
            "strings": TopicMastery(learner_id=learner.learner_id, topic_id="strings", mastery_score=0.60, uncertainty=0.30),
            "hashing": TopicMastery(learner_id=learner.learner_id, topic_id="hashing", mastery_score=0.30, uncertainty=0.50),
            "recursion": TopicMastery(learner_id=learner.learner_id, topic_id="recursion", mastery_score=0.25, uncertainty=0.60),
        }

        gaps = [
            KnowledgeGap(learner_id=learner.learner_id, concept_id="hashing", blocking_topic_id="frequency_patterns", severity="high", diagnostic_evidence="Hashing collision confusion"),
            KnowledgeGap(learner_id=learner.learner_id, concept_id="recursion", blocking_topic_id="trees", severity="high", diagnostic_evidence="Base case and recursive branching misunderstanding"),
            KnowledgeGap(learner_id=learner.learner_id, concept_id="trees", blocking_topic_id="graphs", severity="medium", diagnostic_evidence="Tree pointer manipulation gap"),
        ]

        plan = PlanBuilder.build(
            learner=learner,
            goal=goal,
            mastery_map=masteries,
            gaps=gaps,
            dag=dag
        )

        # 1. Verify structured plan existence
        assert plan.learner_id == learner.learner_id
        assert len(plan.phases) >= 2
        assert len(plan.tasks) >= 5
        assert len(plan.milestones) >= 2

        # 2. Verify topological order: recursion must precede trees
        task_concept_order = [t.concept_id for t in plan.tasks]
        assert "recursion" in task_concept_order
        assert "trees" in task_concept_order
        assert task_concept_order.index("recursion") < task_concept_order.index("trees")

        # 3. Verify Arrays (strong mastery) did not receive heavy instruction
        array_tasks = [t for t in plan.tasks if t.concept_id == "arrays"]
        for at in array_tasks:
            assert at.task_type != TaskType.LEARN

        # 4. Verify Milestones exist with clear criteria
        assert any("Competency" in m.title or "Capstone" in m.title for m in plan.milestones)

        # 5. Verify Structured Explanation rationale
        assert plan.explanation is not None
        exp_text = str(plan.explanation.model_dump()).lower()
        assert "recursion" in exp_text
        assert "hashing" in exp_text
        assert plan.validation_status in (PlanValidationStatus.VALID, PlanValidationStatus.WARNING)
