"""
Plan Builder for Tarkyaan Planning Brain.
Orchestrates goal decomposition, priority ranking, strategy selection,
prerequisite scheduling, task generation, workload estimation, milestone synthesis,
validation, and structured explanation.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from tarkyaan.knowledge.prerequisite_graph import PrerequisiteDAG
from tarkyaan.models.enums import (
    LearningStrategy,
    MasteryTier,
    PlanStatus,
    PlanValidationStatus,
    TaskStatus,
    TaskType,
)
from tarkyaan.models.gaps import KnowledgeGap, MisconceptionRecord
from tarkyaan.models.goals import LearningGoal
from tarkyaan.models.learner import LearnerProfile
from tarkyaan.models.mastery import TopicMastery
from tarkyaan.models.planning import (
    LearningPlan,
    LearningTask,
    Milestone,
    PlanExplanation,
    StudyPhase,
)
from tarkyaan.planning.dependency_scheduler import DependencyScheduler, ScheduledConcept
from tarkyaan.planning.goal_decomposer import DecomposedGoal, GoalDecomposer
from tarkyaan.planning.milestone_engine import MilestoneEngine
from tarkyaan.planning.plan_validator import PlanValidator
from tarkyaan.planning.priority_engine import ConceptPriorityScore, PriorityEngine
from tarkyaan.planning.strategy_engine import StrategyDecision, StrategyEngine
from tarkyaan.planning.workload_engine import WorkloadEngine


class PlanBuilder:
    """
    End-to-end synthesizer transforming learner state, gaps, and prerequisites
    into a validated, actionable LearningPlan.
    """

    @classmethod
    def build(
        cls,
        learner: LearnerProfile,
        goal: LearningGoal,
        mastery_map: Optional[Dict[str, TopicMastery]] = None,
        gaps: Optional[List[KnowledgeGap]] = None,
        misconceptions: Optional[List[MisconceptionRecord]] = None,
        dag: Optional[PrerequisiteDAG] = None,
        plan_id: Optional[str] = None,
        version: int = 1,
        parent_plan_id: Optional[str] = None,
        revision_reason: Optional[str] = None
    ) -> LearningPlan:
        """
        Execute full deterministic plan building pipeline.
        """
        masteries = mastery_map or {}
        active_gaps = [g for g in (gaps or []) if not g.resolved]
        active_misc = misconceptions or []
        pid = plan_id or f"plan_{uuid.uuid4().hex[:8]}"

        # 1. Goal Decomposition
        decomposed: DecomposedGoal = GoalDecomposer.decompose(
            goal=goal,
            learner=learner,
            mastery_map=masteries,
            gaps=active_gaps,
            dag=dag
        )

        all_candidates = list(dict.fromkeys(
            decomposed.prerequisite_concepts
            + decomposed.target_concepts
            + decomposed.supporting_concepts
        ))

        # 2. Priority Ranking
        ranked_scores: List[ConceptPriorityScore] = PriorityEngine.rank_concepts(
            candidate_concept_ids=all_candidates,
            goal=goal,
            mastery_map=masteries,
            gaps=active_gaps,
            dag=dag,
            target_concept_ids=decomposed.target_concepts
        )
        ranked_map = {s.concept_id: s for s in ranked_scores}

        # 3. Strategy Selection
        strategy_decision: StrategyDecision = StrategyEngine.select_strategy(
            goal=goal,
            learner=learner,
            mastery_map=masteries,
            gaps=active_gaps,
            dag=dag,
            target_concept_ids=decomposed.target_concepts
        )

        # 4. Prerequisite-Aware Dependency Scheduling
        scheduled_concepts: List[ScheduledConcept] = DependencyScheduler.schedule(
            candidate_concept_ids=all_candidates,
            mastery_map=masteries,
            dag=dag,
            include_unmastered_ancestors=True
        )

        # 5. Partition into Coherent Study Phases
        # Phase 1: Prerequisite Foundations & Gaps
        # Phase 2: Core Concept Mastery
        # Phase 3: Applied Problem Solving & Capstone
        prereq_set = set(decomposed.prerequisite_concepts)
        target_set = set(decomposed.target_concepts)

        phase1_concepts: List[ScheduledConcept] = []
        phase2_concepts: List[ScheduledConcept] = []
        phase3_concepts: List[ScheduledConcept] = []

        for sc in scheduled_concepts:
            if sc.concept_id in prereq_set or sc.status_category in ("missing", "uncertain"):
                phase1_concepts.append(sc)
            elif sc.concept_id in target_set:
                phase2_concepts.append(sc)
            else:
                phase3_concepts.append(sc)

        # If a phase is completely empty, rebalance
        if not phase1_concepts and phase2_concepts:
            phase1_concepts.append(phase2_concepts.pop(0))
        if not phase3_concepts and len(phase2_concepts) > 2:
            phase3_concepts.append(phase2_concepts.pop(-1))

        phase_groups = [
            ("Phase 1: Foundational Prerequisites", "Strengthen foundational concepts and resolve prerequisite gaps.", phase1_concepts),
            ("Phase 2: Core Concept Mastery", "Acquire deep understanding and systematic mechanics of primary topics.", phase2_concepts),
            ("Phase 3: Applied Problem Solving & Synthesis", "Apply techniques to complex problems, edge cases, and algorithmic optimization.", phase3_concepts)
        ]

        # 6. Generate Atomic Tasks within Phases
        phases: List[StudyPhase] = []
        all_tasks: List[LearningTask] = []
        task_order_counter = 1

        for phase_idx, (p_title, p_obj, p_concept_list) in enumerate(phase_groups, start=1):
            phase_id = f"phase_{uuid.uuid4().hex[:8]}"
            phase_tasks: List[LearningTask] = []
            phase_concept_ids = [c.concept_id for c in p_concept_list]

            for sc in p_concept_list:
                cid = sc.concept_id
                c_name = cid.replace("_", " ").title()
                priority_info = ranked_map.get(cid)
                priority_val = priority_info.final_score if priority_info else 50.0
                prereq_task_ids = [t.task_id for t in all_tasks if t.concept_id in sc.prerequisites]

                if sc.skip_instruction:
                    # Demonstrated high mastery: brief verification or review task only
                    t_review = LearningTask(
                        plan_id=pid,
                        phase_id=phase_id,
                        learner_id=learner.learner_id,
                        goal_id=goal.goal_id,
                        concept_id=cid,
                        topic_id=cid,
                        title=f"{c_name}: Synthesis Review",
                        description=f"Quick trade-off comparison and application verification for {c_name}.",
                        task_type=TaskType.REVIEW,
                        objective=f"Verify retention and edge-case agility for {c_name}.",
                        difficulty=3,
                        estimated_minutes=25,
                        priority=priority_val,
                        prerequisite_task_ids=prereq_task_ids,
                        prerequisite_concept_ids=sc.prerequisites,
                        expected_evidence=f"Comparative reasoning or trace for {c_name}",
                        completion_criteria=["Correctly articulate key invariants and complexity bounds"],
                        mastery_target=0.80,
                        task_order=task_order_counter,
                        rationale=f"Mastery already demonstrated ({sc.mastery_score:.2f}); assigned brief review."
                    )
                    task_order_counter += 1
                    phase_tasks.append(t_review)
                    all_tasks.append(t_review)
                else:
                    # Task 1: Conceptual Understanding / First Principles
                    t_learn = LearningTask(
                        plan_id=pid,
                        phase_id=phase_id,
                        learner_id=learner.learner_id,
                        goal_id=goal.goal_id,
                        concept_id=cid,
                        topic_id=cid,
                        title=f"{c_name}: Foundations & Invariants",
                        description=f"Learn core mechanics, state invariants, and definitions of {c_name}.",
                        task_type=TaskType.UNDERSTAND if sc.status_category != "uncertain" else TaskType.ASSESSMENT,
                        objective=f"Understand theoretical underpinnings and mental model of {c_name}.",
                        difficulty=2 if phase_idx == 1 else 3,
                        estimated_minutes=35,
                        priority=priority_val,
                        prerequisite_task_ids=prereq_task_ids,
                        prerequisite_concept_ids=sc.prerequisites,
                        expected_evidence=f"Accurate Socratic conceptual explanation for {c_name}",
                        completion_criteria=["Explain core invariant without reading notes", "Trace simple execution"],
                        mastery_target=0.60,
                        task_order=task_order_counter,
                        rationale=f"Addresses baseline deficit in {c_name} (current mastery: {sc.mastery_score:.2f})."
                    )
                    task_order_counter += 1
                    phase_tasks.append(t_learn)
                    all_tasks.append(t_learn)

                    # Task 2: Deliberate Practice / Application
                    t_practice = LearningTask(
                        plan_id=pid,
                        phase_id=phase_id,
                        learner_id=learner.learner_id,
                        goal_id=goal.goal_id,
                        concept_id=cid,
                        topic_id=cid,
                        title=f"{c_name}: Implementation & Practice",
                        description=f"Solve representative problems applying {c_name} in {learner.preferred_language}.",
                        task_type=TaskType.PRACTICE,
                        objective=f"Implement algorithm and analyze Big-O runtime for {c_name}.",
                        difficulty=3 if phase_idx <= 2 else 4,
                        estimated_minutes=45,
                        priority=priority_val,
                        prerequisite_task_ids=[t_learn.task_id],
                        prerequisite_concept_ids=sc.prerequisites,
                        expected_evidence=f"Working implementation code and complexity analysis for {c_name}",
                        completion_criteria=["Pass sample test cases including boundary inputs", "State time/space complexity"],
                        mastery_target=0.75,
                        task_order=task_order_counter,
                        rationale=f"Reinforces applied competency in {c_name}."
                    )
                    task_order_counter += 1
                    phase_tasks.append(t_practice)
                    all_tasks.append(t_practice)

            phase_minutes = sum(t.estimated_minutes for t in phase_tasks)
            phases.append(StudyPhase(
                phase_id=phase_id,
                plan_id=pid,
                name=p_title,
                title=p_title,
                objective=p_obj,
                concepts=phase_concept_ids,
                prerequisite_phase_ids=[phases[-1].phase_id] if phases else [],
                task_ids=[t.task_id for t in phase_tasks],
                tasks=phase_tasks,
                estimated_minutes=phase_minutes,
                phase_order=phase_idx,
                completion_criteria=[f"Complete all {len(phase_tasks)} tasks in {p_title}"]
            ))

        # 7. Milestones
        milestones = MilestoneEngine.generate_milestones(plan_id=pid, phases=phases)

        # 8. Workload Estimation
        workload = WorkloadEngine.estimate(
            tasks=all_tasks,
            learner=learner,
            deadline=goal.deadline
        )

        # 9. Structured Plan Explanation Rationale
        strengths = [
            cid for cid, m in masteries.items()
            if m.mastery_score >= 0.70 and m.tier in (MasteryTier.COMPETENT, MasteryTier.MASTERED)
        ]
        deferred = [
            {"concept_id": cid, "reason": f"Sufficient existing competence ({m.mastery_score:.2f})"}
            for cid, m in masteries.items()
            if m.mastery_score >= 0.85 and cid not in target_set
        ]
        prioritized_gaps_summary = [
            {
                "concept_id": s.concept_id,
                "score": s.final_score,
                "rationale": s.rationale
            }
            for s in ranked_scores[:5]
        ]
        prereq_rationale_list = [
            f"'{sc.concept_id}' scheduled before dependents ({', '.join(sc.prerequisites) or 'foundational root'})"
            for sc in scheduled_concepts[:4]
        ]

        workload_note = (
            f"Estimated total study time: {workload.total_hours:.1f} hours across ~{workload.estimated_sessions} sessions "
            f"({workload.daily_minutes:.0f} min/day)."
        )
        if workload.is_overloaded:
            workload_note += f" [WARNING: {workload.overload_reason}]"

        explanation = PlanExplanation(
            summary=f"Personalized {strategy_decision.strategy.value.replace('_', ' ').title()} roadmap for '{goal.title}'.",
            goal_relevance=f"Curriculum systematically builds toward: '{goal.target_outcome}'.",
            strengths_acknowledged=strengths or ["No high-mastery topics recorded yet; starting from clean foundation"],
            prioritized_gaps=prioritized_gaps_summary,
            deferred_topics=deferred,
            prerequisite_rationale=prereq_rationale_list,
            strategy_rationale=strategy_decision.rationale,
            workload_rationale=workload_note
        )

        # 10. Assemble Plan
        plan = LearningPlan(
            plan_id=pid,
            learner_id=learner.learner_id,
            goal_id=goal.goal_id,
            title=f"{goal.title} — Personalized Roadmap",
            description=f"Personalized, prerequisite-aware study roadmap decomposing goal '{goal.title}'.",
            objective=goal.target_outcome,
            status=PlanStatus.PROPOSED,
            strategy=strategy_decision.strategy,
            version=version,
            parent_plan_id=parent_plan_id,
            revision_reason=revision_reason,
            phases=phases,
            milestones=milestones,
            tasks=all_tasks,
            dependencies={sc.concept_id: sc.prerequisites for sc in scheduled_concepts if sc.prerequisites},
            assumptions=[
                f"Learner daily study capacity is approximately {learner.daily_time_budget_minutes} min",
                f"Primary development language: {learner.preferred_language}"
            ],
            expected_outcomes=decomposed.required_competencies,
            validation_status=PlanValidationStatus.VALID,
            provenance={
                "builder": "TarkyaanPlanBuilder_v1",
                "strategy": strategy_decision.strategy.value,
                "strategy_factors": strategy_decision.primary_factors
            },
            explanation=explanation,
            total_estimated_hours=workload.total_hours,
            estimated_total_minutes=workload.total_minutes,
            priority=goal.priority,
            start_date=None,
            target_date=goal.deadline
        )

        # 11. Deterministic Validation
        val_result = PlanValidator.validate(plan, dag=dag)
        plan.validation_status = val_result.status

        return plan
