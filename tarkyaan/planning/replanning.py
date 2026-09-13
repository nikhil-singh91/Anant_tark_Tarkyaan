"""
Tarkyaan Replanning Engine — Phase 6.
Evidence-driven autonomous curriculum mutation with full audit trail.

Components:
- ReplanningTriggerEngine:    Evaluates evidence thresholds → trigger classification
- CurriculumMutationEngine:   Computes minimal plan diff and change summary
- TaskPriorityRecalculator:   Re-weights pending tasks by gap severity and mastery
- ReplanningEngine:           Top-level facade orchestrating the full replan cycle
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from tarkyaan.models.enums import ReplanningTrigger, TaskStatus
from tarkyaan.models.planning import LearningPlan, LearningTask


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# ReplanningRecord (Pydantic model returned to callers)
# ---------------------------------------------------------------------------

class ReplanningRecord(BaseModel):
    """Structured audit record describing a single autonomous replan decision."""
    record_id: str
    learner_id: str
    old_plan_id: str
    new_plan_id: str
    trigger_type: ReplanningTrigger
    trigger_evidence: Dict[str, Any] = Field(default_factory=dict)
    rationale: str = ""
    changes_summary: str = ""
    health_status: str = "healthy"
    created_at: datetime = Field(default_factory=_utc_now)


# ---------------------------------------------------------------------------
# ReplanningTriggerEngine
# ---------------------------------------------------------------------------

class ReplanningTriggerEngine:
    """
    Evaluates a LearningHealthReport and returns the primary replan trigger.
    Uses priority ordering: REGRESSION > OVERLOAD > STALL > GAP_PERSISTENCE >
    MISCONCEPTION_LOOP > PLATEAU > VELOCITY_DROP.
    """

    TRIGGER_PRIORITY: List[ReplanningTrigger] = [
        ReplanningTrigger.REGRESSION,
        ReplanningTrigger.OVERLOAD,
        ReplanningTrigger.STALL,
        ReplanningTrigger.GAP_PERSISTENCE,
        ReplanningTrigger.MISCONCEPTION_LOOP,
        ReplanningTrigger.PLATEAU,
        ReplanningTrigger.VELOCITY_DROP,
        ReplanningTrigger.MILESTONE_MISSED,
        ReplanningTrigger.PREREQUISITE_FAILURE,
    ]

    @classmethod
    def get_primary_trigger(
        cls,
        triggers: List[ReplanningTrigger],
    ) -> Optional[ReplanningTrigger]:
        """Return the highest-priority trigger from the given set."""
        for candidate in cls.TRIGGER_PRIORITY:
            if candidate in triggers:
                return candidate
        return None

    @classmethod
    def build_evidence_dict(
        cls,
        triggers: List[ReplanningTrigger],
        health_status: str,
        signals: List[str],
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Construct a structured evidence dict for audit logging."""
        ev: Dict[str, Any] = {
            "triggers": [t.value for t in triggers],
            "health_status": health_status,
            "signals": signals,
        }
        if extra:
            ev.update(extra)
        return ev


# ---------------------------------------------------------------------------
# CurriculumMutationEngine
# ---------------------------------------------------------------------------

class CurriculumMutationEngine:
    """
    Computes the minimal mutation between an old plan and proposed evidence.
    Produces a human-readable changes_summary for audit and explainability.
    Rule: Preserve completed tasks; only reconfigure PENDING/IN_PROGRESS tasks.
    """

    @classmethod
    def compute_changes_summary(
        cls,
        old_plan: LearningPlan,
        trigger: ReplanningTrigger,
        signals: List[str],
    ) -> str:
        """
        Generate a concise text summary of what changed and why.
        Used in plan_versions audit trail and replanning_records.
        """
        completed_count = sum(
            1 for t in old_plan.tasks
            if t.status == TaskStatus.COMPLETED
        )
        pending_count = sum(
            1 for t in old_plan.tasks
            if t.status == TaskStatus.PENDING
        )
        total = len(old_plan.tasks)

        reason_map = {
            ReplanningTrigger.STALL: "Learning stall detected",
            ReplanningTrigger.REGRESSION: "Mastery regression detected",
            ReplanningTrigger.OVERLOAD: "Task difficulty overload",
            ReplanningTrigger.GAP_PERSISTENCE: "Persistent unresolved knowledge gaps",
            ReplanningTrigger.PLATEAU: "Mastery plateau",
            ReplanningTrigger.MILESTONE_MISSED: "Milestone target date missed",
            ReplanningTrigger.MISCONCEPTION_LOOP: "Recurring misconception pattern",
            ReplanningTrigger.VELOCITY_DROP: "Learning velocity dropped below threshold",
            ReplanningTrigger.PREREQUISITE_FAILURE: "Prerequisite mastery insufficient",
            ReplanningTrigger.MANUAL: "Manual replan requested",
        }
        reason = reason_map.get(trigger, trigger.value)

        parts = [
            f"Trigger: {reason}.",
            f"Old plan v{old_plan.version}: {total} tasks ({completed_count} completed, "
            f"{pending_count} pending).",
            f"Completed tasks preserved; pending tasks reordered/replaced.",
        ]
        if signals:
            parts.append(f"Evidence: {signals[0]}")
        return " ".join(parts)

    @classmethod
    def preserved_completed_task_ids(cls, old_plan: LearningPlan) -> List[str]:
        """Return IDs of tasks that are completed and should be preserved."""
        return [
            t.task_id for t in old_plan.tasks
            if t.status == TaskStatus.COMPLETED
        ]


# ---------------------------------------------------------------------------
# TaskPriorityRecalculator
# ---------------------------------------------------------------------------

class TaskPriorityRecalculator:
    """
    Re-weights pending tasks in a plan based on:
    - Gap severity (high-severity gap concepts get priority boost)
    - Mastery distance from competent tier (lower mastery = higher urgency)
    - Trigger type (e.g., OVERLOAD lowers difficulty, STALL boosts recall)
    """

    GAP_PRIORITY_BOOST: float = 1.5
    LOW_MASTERY_BOOST: float = 1.3
    COMPETENT_THRESHOLD: float = 0.70

    @classmethod
    def recalculate(
        cls,
        tasks: List[LearningTask],
        gap_topic_ids: Optional[List[str]] = None,
        mastery_map: Optional[Dict[str, float]] = None,
        trigger: Optional[ReplanningTrigger] = None,
    ) -> List[LearningTask]:
        """
        Return tasks with updated priority scores.
        Only modifies PENDING tasks; COMPLETED/IN_PROGRESS tasks are unchanged.
        """
        gap_set = set(gap_topic_ids or [])
        mastery_map = mastery_map or {}

        updated: List[LearningTask] = []
        for task in tasks:
            if task.status != TaskStatus.PENDING:
                updated.append(task)
                continue

            priority = task.priority

            # Boost priority for tasks in gap topics
            if task.topic_id in gap_set or task.concept_id in gap_set:
                priority *= cls.GAP_PRIORITY_BOOST

            # Boost priority for low-mastery topics
            mastery_score = mastery_map.get(task.topic_id, mastery_map.get(task.concept_id, 0.5))
            if mastery_score < cls.COMPETENT_THRESHOLD:
                priority *= cls.LOW_MASTERY_BOOST

            # Trigger-specific adjustments
            if trigger == ReplanningTrigger.OVERLOAD:
                # Reduce difficulty tasks' priority to ease the learner in
                if task.difficulty >= 4:
                    priority *= 0.6
            elif trigger == ReplanningTrigger.STALL:
                # Prefer recall/review tasks to break the stall
                from tarkyaan.models.enums import TaskType
                if task.task_type in (TaskType.RECALL, TaskType.REVIEW):
                    priority *= 1.4

            # Clamp to reasonable range
            task_copy = task.model_copy(update={"priority": round(min(priority, 10.0), 3)})
            updated.append(task_copy)

        return updated


# ---------------------------------------------------------------------------
# ReplanningEngine
# ---------------------------------------------------------------------------

class ReplanningEngine:
    """
    Top-level Phase 6 replanning facade.

    Orchestrates the full replan cycle:
    1. Identify the primary trigger
    2. Compute change summary
    3. Delegate plan version increment to LearningPlanner.replan()
    4. Re-prioritize tasks
    5. Persist audit record via MemoryManager
    6. Publish REPLANNING_COMPLETED event

    Does NOT duplicate LearningPlanner logic — calls it directly.
    """

    def __init__(
        self,
        memory: Optional[Any] = None,        # TarkyaanMemoryManager
        planner: Optional[Any] = None,        # LearningPlanner
        event_bus: Optional[Any] = None,
    ) -> None:
        self._memory = memory
        self._planner = planner
        self._event_bus = event_bus

    @property
    def memory(self) -> Any:
        if self._memory is None:
            from tarkyaan.memory.memory_manager import TarkyaanMemoryManager
            self._memory = TarkyaanMemoryManager()
        return self._memory

    @property
    def planner(self) -> Any:
        if self._planner is None:
            from tarkyaan.planning.planner import LearningPlanner
            self._planner = LearningPlanner(memory=self.memory)
        return self._planner

    @property
    def bus(self) -> Any:
        if self._event_bus is None:
            from tarkyaan.events import event_bus as _bus
            return _bus
        return self._event_bus

    def replan(
        self,
        plan_id: str,
        triggers: List[ReplanningTrigger],
        health_status: str,
        signals: List[str],
        gap_topic_ids: Optional[List[str]] = None,
        mastery_map: Optional[Dict[str, float]] = None,
        extra_evidence: Optional[Dict[str, Any]] = None,
    ) -> Tuple[LearningPlan, ReplanningRecord]:
        """
        Execute a full autonomous replan cycle.

        :param plan_id:         Active plan to supersede
        :param triggers:        All fired ReplanningTriggers
        :param health_status:   HealthStatus string classification
        :param signals:         Human-readable evidence signals
        :param gap_topic_ids:   Topic IDs with active knowledge gaps
        :param mastery_map:     Topic → mastery score (for priority recalc)
        :param extra_evidence:  Additional evidence to log in audit
        :return: (new_plan, replanning_record)
        """
        old_plan = self.planner.get_plan(plan_id)
        if not old_plan:
            raise ValueError(f"Plan '{plan_id}' not found — cannot replan.")

        # 1. Primary trigger
        primary = ReplanningTriggerEngine.get_primary_trigger(triggers)
        if primary is None:
            primary = ReplanningTrigger.MANUAL

        # 2. Change summary
        changes_summary = CurriculumMutationEngine.compute_changes_summary(
            old_plan=old_plan,
            trigger=primary,
            signals=signals,
        )

        # 3. Rationale sentence
        rationale = (
            f"Autonomous replan triggered by [{primary.value}]. "
            f"Health: {health_status}. {signals[0] if signals else ''}"
        ).strip()

        # 4. Delegate to LearningPlanner.replan() — increments version, supersedes old
        try:
            from tarkyaan.events.event_bus import TarkyaanEvent
            self.bus.publish(
                TarkyaanEvent.REPLANNING_TRIGGERED,
                payload={"plan_id": plan_id, "trigger": primary.value},
                learner_id=old_plan.learner_id,
                source="replanning_engine",
            )
        except Exception:
            pass

        new_plan = self.planner.replan(
            plan_id=plan_id,
            revision_reason=rationale,
            changes_summary=changes_summary,
        )

        # 5. Re-prioritize tasks
        if new_plan.tasks:
            new_plan.tasks = TaskPriorityRecalculator.recalculate(
                tasks=new_plan.tasks,
                gap_topic_ids=gap_topic_ids,
                mastery_map=mastery_map,
                trigger=primary,
            )

        # 6. Persist audit record
        evidence_dict = ReplanningTriggerEngine.build_evidence_dict(
            triggers=triggers,
            health_status=health_status,
            signals=signals,
            extra=extra_evidence,
        )
        record_id = self.memory.save_replanning_record(
            learner_id=old_plan.learner_id,
            old_plan_id=old_plan.plan_id,
            new_plan_id=new_plan.plan_id,
            trigger_type=primary.value,
            trigger_evidence=evidence_dict,
            rationale=rationale,
            changes_summary=changes_summary,
            health_status=health_status,
        )

        record = ReplanningRecord(
            record_id=record_id,
            learner_id=old_plan.learner_id,
            old_plan_id=old_plan.plan_id,
            new_plan_id=new_plan.plan_id,
            trigger_type=primary,
            trigger_evidence=evidence_dict,
            rationale=rationale,
            changes_summary=changes_summary,
            health_status=health_status,
        )

        # 7. Publish completion event
        try:
            from tarkyaan.events.event_bus import TarkyaanEvent
            self.bus.publish(
                TarkyaanEvent.REPLANNING_COMPLETED,
                payload={
                    "old_plan_id": old_plan.plan_id,
                    "new_plan_id": new_plan.plan_id,
                    "trigger": primary.value,
                    "new_version": new_plan.version,
                },
                learner_id=old_plan.learner_id,
                source="replanning_engine",
            )
        except Exception:
            pass

        return new_plan, record
