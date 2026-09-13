"""
Unit and Integration tests for LearningPlanner facade service.
Tests plan generation, database persistence, plan versioning (v1 -> v2),
version audit trails, and strict learner isolation.
"""

import pytest

from tarkyaan.knowledge.prerequisite_graph import PrerequisiteDAG
from tarkyaan.memory.memory_manager import TarkyaanMemoryManager
from tarkyaan.memory.memory_store import TarkyaanMemoryStore
from tarkyaan.models.enums import PlanStatus
from tarkyaan.models.gaps import KnowledgeGap
from tarkyaan.models.goals import LearningGoal
from tarkyaan.models.learner import LearnerProfile
from tarkyaan.models.mastery import TopicMastery
from tarkyaan.planning.planner import LearningPlanner


class TestLearningPlanner:
    @pytest.fixture
    def test_planner(self):
        store = TarkyaanMemoryStore(":memory:")
        memory = TarkyaanMemoryManager(store)
        dag = PrerequisiteDAG()
        dag.add_concept("variables", "Variables", "cs")
        dag.add_concept("control_flow", "Control Flow", "cs")
        dag.add_concept("functions", "Functions", "cs")
        dag.add_concept("recursion", "Recursion", "cs")
        dag.add_prerequisite("control_flow", "variables")
        dag.add_prerequisite("functions", "control_flow")
        dag.add_prerequisite("recursion", "functions")
        return LearningPlanner(memory=memory, dag=dag)

    def test_plan_goal_lifecycle_and_persistence(self, test_planner):
        # 1. Create learner and goal
        learner = test_planner.memory.create_learner(LearnerProfile(
            display_name="Devansh",
            primary_domain="Computer Science",
            preferred_language="C++"
        ))
        goal = test_planner.memory.create_goal(LearningGoal(
            learner_id=learner.learner_id,
            title="Master Recursion in C++",
            target_outcome="Solve medium recursive backtracking problems"
        ))

        # 2. Add knowledge gap
        test_planner.memory.create_knowledge_gap(KnowledgeGap(
            learner_id=learner.learner_id,
            concept_id="functions",
            blocking_topic_id="recursion",
            severity="high",
            diagnostic_evidence="Call stack frame confusion"
        ))

        # 3. Plan goal
        plan = test_planner.plan_goal(
            learner_id=learner.learner_id,
            goal_id=goal.goal_id,
            auto_activate=True
        )

        assert plan.plan_id is not None
        assert plan.version == 1
        assert plan.status == PlanStatus.ACTIVE
        assert len(plan.phases) >= 1
        assert len(plan.tasks) >= 2

        # 4. Fetch from database and verify persistence fidelity
        loaded_plan = test_planner.get_plan(plan.plan_id)
        assert loaded_plan is not None
        assert loaded_plan.plan_id == plan.plan_id
        assert loaded_plan.title == plan.title
        assert len(loaded_plan.tasks) == len(plan.tasks)
        assert len(loaded_plan.phases) == len(plan.phases)
        assert len(loaded_plan.milestones) == len(plan.milestones)

    def test_plan_versioning_and_replanning(self, test_planner):
        learner = test_planner.memory.create_learner(LearnerProfile(display_name="Kritika"))
        goal = test_planner.memory.create_goal(LearningGoal(
            learner_id=learner.learner_id,
            title="Algorithm Training",
            target_outcome="Solve problems"
        ))

        # Initial plan (v1)
        plan_v1 = test_planner.plan_goal(learner.learner_id, goal.goal_id)
        assert plan_v1.version == 1

        # Replan triggered by diagnostic update (v1 -> v2)
        plan_v2 = test_planner.replan(
            plan_id=plan_v1.plan_id,
            revision_reason="Learner demonstrated rapid mastery of functions; advancing directly to recursion.",
            changes_summary="Prerequisite phase consolidated"
        )

        assert plan_v2.version == 2
        assert plan_v2.parent_plan_id == plan_v1.plan_id
        assert plan_v2.status == PlanStatus.ACTIVE

        # Old plan should now be marked SUPERSEDED
        old_plan_reloaded = test_planner.get_plan(plan_v1.plan_id)
        assert old_plan_reloaded.status == PlanStatus.SUPERSEDED

        # Check version audit history
        history = test_planner.get_version_history(plan_v2.plan_id)
        assert len(history) >= 1
        assert history[-1]["version"] == 2

    def test_strict_learner_isolation_in_plans(self, test_planner):
        """
        CRITICAL TEST: Verify that Learner A's plan and tasks can NEVER
        be fetched or accessed in Learner B's plan queries.
        """
        learner_a = test_planner.memory.create_learner(LearnerProfile(display_name="Learner A"))
        goal_a = test_planner.memory.create_goal(LearningGoal(
            learner_id=learner_a.learner_id,
            title="Goal A",
            target_outcome="Master Domain A"
        ))
        plan_a = test_planner.plan_goal(learner_a.learner_id, goal_a.goal_id)

        learner_b = test_planner.memory.create_learner(LearnerProfile(display_name="Learner B"))
        goal_b = test_planner.memory.create_goal(LearningGoal(
            learner_id=learner_b.learner_id,
            title="Goal B",
            target_outcome="Master Domain B"
        ))
        plan_b = test_planner.plan_goal(learner_b.learner_id, goal_b.goal_id)

        # Learner B queries
        plans_b = test_planner.list_plans(learner_b.learner_id)
        plan_ids_b = [p.plan_id for p in plans_b]

        assert plan_a.plan_id not in plan_ids_b
        assert plan_b.plan_id in plan_ids_b

        # Active plan for B should be plan_b, never plan_a
        active_b = test_planner.get_active_plan(learner_b.learner_id)
        assert active_b.plan_id == plan_b.plan_id
        assert active_b.learner_id == learner_b.learner_id
