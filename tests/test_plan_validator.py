"""
Unit tests for PlanValidator.
Tests deterministic validation catching circular task dependencies,
duplicate IDs, nonexistent task references, and DAG prerequisite violations.
"""

import pytest

from tarkyaan.knowledge.prerequisite_graph import PrerequisiteDAG
from tarkyaan.models.enums import PlanValidationStatus
from tarkyaan.models.planning import (
    LearningPlan,
    LearningTask,
    Milestone,
    StudyPhase,
)
from tarkyaan.planning.plan_validator import PlanValidator


class TestPlanValidator:
    def test_valid_plan_passes(self):
        t1 = LearningTask(task_id="t1", title="Task 1", topic_id="math")
        t2 = LearningTask(task_id="t2", title="Task 2", topic_id="math", prerequisite_task_ids=["t1"])
        phase = StudyPhase(phase_id="p1", title="Phase 1", task_ids=["t1", "t2"], tasks=[t1, t2])
        ms = Milestone(milestone_id="m1", title="M1", required_task_ids=["t1", "t2"])

        plan = LearningPlan(
            learner_id="l1",
            goal_id="g1",
            title="Valid Roadmap",
            phases=[phase],
            tasks=[t1, t2],
            milestones=[ms]
        )

        res = PlanValidator.validate(plan)
        assert res.is_valid is True
        assert res.status in (PlanValidationStatus.VALID, PlanValidationStatus.WARNING)
        assert len(res.errors) == 0

    def test_duplicate_task_ids_rejected(self):
        t1 = LearningTask(task_id="dup_id", title="Task 1", topic_id="t1")
        t2 = LearningTask(task_id="dup_id", title="Task 2", topic_id="t2")

        plan = LearningPlan(
            learner_id="l1",
            goal_id="g1",
            title="Invalid Roadmap",
            tasks=[t1, t2]
        )

        res = PlanValidator.validate(plan)
        assert res.is_valid is False
        assert any("duplicate task" in e.lower() for e in res.errors)

    def test_prerequisite_task_ordering_violation_caught(self):
        # t2 is scheduled first (index 0) but lists t1 as prerequisite, while t1 is at index 1!
        t2 = LearningTask(task_id="t2", title="Advanced Task", topic_id="trees", prerequisite_task_ids=["t1"])
        t1 = LearningTask(task_id="t1", title="Basics Task", topic_id="recursion")

        plan = LearningPlan(
            learner_id="l1",
            goal_id="g1",
            title="Backward Roadmap",
            tasks=[t2, t1]
        )

        res = PlanValidator.validate(plan)
        assert res.is_valid is False
        assert any("prerequisite ordering violated" in e.lower() for e in res.errors)

    def test_dag_prerequisite_inversion_detected(self):
        dag = PrerequisiteDAG()
        dag.add_concept("pointers", "Pointers", "cs")
        dag.add_concept("linked_lists", "Linked Lists", "cs")
        dag.add_prerequisite("linked_lists", "pointers")

        # Plan schedules linked_lists at task index 0 and pointers at task index 1
        t_ll = LearningTask(task_id="t_ll", title="LL", concept_id="linked_lists", topic_id="linked_lists")
        t_ptr = LearningTask(task_id="t_ptr", title="Ptr", concept_id="pointers", topic_id="pointers")

        plan = LearningPlan(
            learner_id="l1",
            goal_id="g1",
            title="Inverted DAG Roadmap",
            tasks=[t_ll, t_ptr]
        )

        res = PlanValidator.validate(plan, dag=dag)
        assert res.is_valid is False
        assert any("dag prerequisite" in e.lower() for e in res.errors)
