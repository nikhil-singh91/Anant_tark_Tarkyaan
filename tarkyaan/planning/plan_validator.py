"""
Plan Validator for Tarkyaan Planning Brain.
Performs deterministic, rule-based integrity verification on generated learning plans.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set

from tarkyaan.knowledge.prerequisite_graph import PrerequisiteDAG
from tarkyaan.models.enums import PlanValidationStatus
from tarkyaan.models.planning import LearningPlan, PlanValidationResult


class PlanValidator:
    """
    Validates learning plan integrity, prerequisite constraints, task uniqueness,
    and workload consistency.
    """

    @classmethod
    def validate(
        cls,
        plan: LearningPlan,
        dag: Optional[PrerequisiteDAG] = None
    ) -> PlanValidationResult:
        """
        Execute deterministic validation suite on a proposed or active plan.
        """
        errors: List[str] = []
        warnings: List[str] = []

        # 1. Identity & Reference Checks
        if not plan.learner_id or not plan.learner_id.strip():
            errors.append("Plan must reference a valid non-empty learner_id.")
        if not plan.goal_id or not plan.goal_id.strip():
            errors.append("Plan must reference a valid non-empty goal_id.")
        if not plan.title or len(plan.title.strip()) < 2:
            errors.append("Plan title must be at least 2 characters long.")

        # 2. Duplicate ID Checks
        task_ids: List[str] = [t.task_id for t in plan.tasks]
        if len(task_ids) != len(set(task_ids)):
            errors.append("Plan contains duplicate task IDs.")

        phase_ids: List[str] = [p.phase_id for p in plan.phases]
        if len(phase_ids) != len(set(phase_ids)):
            errors.append("Plan contains duplicate phase IDs.")

        milestone_ids: List[str] = [m.milestone_id for m in plan.milestones]
        if len(milestone_ids) != len(set(milestone_ids)):
            errors.append("Plan contains duplicate milestone IDs.")

        task_id_set: Set[str] = set(task_ids)
        task_order_map: Dict[str, int] = {t.task_id: idx for idx, t in enumerate(plan.tasks)}

        # 3. Phase & Task Reference Integrity
        for phase in plan.phases:
            for tid in phase.task_ids:
                if tid not in task_id_set:
                    errors.append(f"Phase '{phase.title}' references nonexistent task ID '{tid}'.")

        # 4. Milestone Reference Integrity
        for ms in plan.milestones:
            for tid in ms.required_task_ids:
                if tid not in task_id_set:
                    warnings.append(f"Milestone '{ms.title}' references unassigned task ID '{tid}'.")

        # 5. Prerequisite Task Ordering Integrity
        for task in plan.tasks:
            curr_pos = task_order_map[task.task_id]
            for prereq_tid in task.prerequisite_task_ids:
                if prereq_tid in task_order_map:
                    prereq_pos = task_order_map[prereq_tid]
                    if prereq_pos >= curr_pos:
                        errors.append(
                            f"Task '{task.title}' (order {curr_pos}) is scheduled before its prerequisite task "
                            f"'{prereq_tid}' (order {prereq_pos}). Prerequisite ordering violated."
                        )

        # 6. Prerequisite DAG Integrity
        if dag:
            concept_first_seen: Dict[str, int] = {}
            for idx, task in enumerate(plan.tasks):
                cid = task.concept_id or task.topic_id
                if cid and cid not in concept_first_seen:
                    concept_first_seen[cid] = idx

            for cid, pos in concept_first_seen.items():
                if dag.has_concept(cid):
                    direct_prereqs = dag.get_prerequisites(cid)
                    for p in direct_prereqs:
                        if p in concept_first_seen and concept_first_seen[p] > pos:
                            errors.append(
                                f"Concept '{cid}' is scheduled at task position {pos} before its DAG prerequisite "
                                f"'{p}' which appears at position {concept_first_seen[p]}."
                            )

        # 7. Workload Consistency
        calculated_minutes = sum(t.estimated_minutes for t in plan.tasks)
        if calculated_minutes == 0 and len(plan.tasks) > 0:
            warnings.append("Plan tasks have 0 total estimated minutes.")
        if any(t.estimated_minutes < 5 for t in plan.tasks):
            warnings.append("Some tasks have unrealistic estimated durations (< 5 minutes).")

        # Evaluate final status
        is_valid = (len(errors) == 0)
        status = PlanValidationStatus.VALID if is_valid else PlanValidationStatus.INVALID
        if is_valid and warnings:
            status = PlanValidationStatus.WARNING

        return PlanValidationResult(
            is_valid=is_valid,
            status=status,
            errors=errors,
            warnings=warnings
        )
