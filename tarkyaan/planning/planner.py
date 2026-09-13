"""
Learning Planner Service Facade for Tarkyaan Planning Brain.
Orchestrates autonomous curriculum generation, plan persistence, and versioning.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from tarkyaan.knowledge.prerequisite_graph import PrerequisiteDAG
from tarkyaan.memory.memory_manager import TarkyaanMemoryManager
from tarkyaan.models.enums import PlanStatus
from tarkyaan.models.planning import LearningPlan
from tarkyaan.planning.plan_builder import PlanBuilder


class LearningPlanner:
    """
    High-level facade orchestrating personalized roadmap generation, persistence,
    and plan evolution across learning cycles.
    """

    def __init__(
        self,
        memory: Optional[TarkyaanMemoryManager] = None,
        dag: Optional[PrerequisiteDAG] = None
    ) -> None:
        self.memory = memory or TarkyaanMemoryManager()
        self.dag = dag

    def plan_goal(
        self,
        learner_id: str,
        goal_id: str,
        auto_activate: bool = False
    ) -> LearningPlan:
        """
        Synthesize a personalized, validated learning roadmap for a learner's goal.
        """
        # 1. Fetch learner and goal
        learner = self.memory.get_learner(learner_id)
        if not learner:
            raise ValueError(f"Learner '{learner_id}' does not exist in Tarkyaan memory.")

        goal = self.memory.get_goal(goal_id)
        if not goal:
            raise ValueError(f"Goal '{goal_id}' does not exist in Tarkyaan memory.")

        # 2. Fetch current learner state
        mastery_list = self.memory.get_all_topic_mastery(learner_id)
        mastery_map = {m.topic_id: m for m in mastery_list}

        gaps = self.memory.get_knowledge_gaps(learner_id, active_only=True)
        misconceptions = self.memory.get_misconceptions(learner_id)

        # 3. Build plan
        plan = PlanBuilder.build(
            learner=learner,
            goal=goal,
            mastery_map=mastery_map,
            gaps=gaps,
            misconceptions=misconceptions,
            dag=self.dag,
            version=1
        )

        if auto_activate:
            plan.status = PlanStatus.ACTIVE

        # 4. Persist in Tarkyaan memory
        saved_plan = self.memory.save_learning_plan(plan)
        self.memory.archive_plan_version(saved_plan, change_reason="Initial plan synthesis")

        return saved_plan

    def replan(
        self,
        plan_id: str,
        revision_reason: str,
        changes_summary: str = ""
    ) -> LearningPlan:
        """
        Replan an existing roadmap in response to diagnostic progress, mastery changes,
        or timeline adjustments. Creates an incremented plan version (v -> v+1) and
        supersedes the prior version.
        """
        old_plan = self.memory.get_learning_plan(plan_id)
        if not old_plan:
            raise ValueError(f"Plan '{plan_id}' does not exist.")

        # 1. Supersede previous plan
        self.memory.update_plan_status(plan_id, PlanStatus.SUPERSEDED)
        self.memory.archive_plan_version(
            old_plan,
            change_reason=f"Superseded by replanning: {revision_reason}"
        )

        # 2. Fetch fresh learner state
        learner = self.memory.get_learner(old_plan.learner_id)
        goal = self.memory.get_goal(old_plan.goal_id)
        if not learner or not goal:
            raise ValueError("Associated learner or goal missing during replan.")

        mastery_list = self.memory.get_all_topic_mastery(learner.learner_id)
        mastery_map = {m.topic_id: m for m in mastery_list}
        gaps = self.memory.get_knowledge_gaps(learner.learner_id, active_only=True)
        misconceptions = self.memory.get_misconceptions(learner.learner_id)

        # 3. Build incremented plan version
        new_plan = PlanBuilder.build(
            learner=learner,
            goal=goal,
            mastery_map=mastery_map,
            gaps=gaps,
            misconceptions=misconceptions,
            dag=self.dag,
            version=old_plan.version + 1,
            parent_plan_id=old_plan.plan_id,
            revision_reason=revision_reason
        )
        new_plan.status = PlanStatus.ACTIVE

        # 4. Save and archive
        saved_new_plan = self.memory.save_learning_plan(new_plan)
        reason_desc = f"{revision_reason}. {changes_summary}".strip()
        self.memory.archive_plan_version(saved_new_plan, change_reason=reason_desc)

        return saved_new_plan

    def get_plan(self, plan_id: str) -> Optional[LearningPlan]:
        """Retrieve a specific learning plan by ID."""
        return self.memory.get_learning_plan(plan_id)

    def get_active_plan(self, learner_id: str) -> Optional[LearningPlan]:
        """Fetch the active curriculum roadmap for a learner."""
        return self.memory.get_active_learning_plan(learner_id)

    def list_plans(self, learner_id: str) -> List[LearningPlan]:
        """List all plans associated with a learner."""
        return self.memory.list_learning_plans(learner_id)

    def get_version_history(self, plan_id: str) -> List[Dict[str, Any]]:
        """Retrieve full audit trail of plan revisions."""
        return self.memory.get_plan_version_history(plan_id)
