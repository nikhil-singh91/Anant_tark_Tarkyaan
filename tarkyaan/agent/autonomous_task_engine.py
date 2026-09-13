"""
Autonomous Task Engine.
Coordinates the Observe -> Plan -> Act -> Verify multi-step autonomous cycle.
Enforces step budgets, timeout constraints, safety boundaries, and instantaneous cancellation.
"""

from __future__ import annotations

import re
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from tarkyaan.agent.observability import AgentObservabilityRecorder
from tarkyaan.agent.task_executor import TaskExecutor
from tarkyaan.agent.task_models import AgentStep, AutonomousTask
from tarkyaan.agent.task_planner import TaskPlanner
from tarkyaan.context.multimodal_context import MultimodalContext
from tarkyaan.events.event_bus import EventBus, TarkyaanEvent
from tarkyaan.memory.memory_manager import TarkyaanMemoryManager
from tarkyaan.models.enums import AgentStepStatus, AgentTaskStatus


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AutonomousTaskEngine:
    """
    Central orchestration engine for autonomous multi-step tasks.
    Enforces Observe -> Plan -> Act -> Verify with hard limits on steps and time.
    """

    CANCELLATION_KEYWORDS = {
        "stop", "cancel", "never mind", "abort", "halt",
        "ruko", "रुको", "rahne do", "रहने दो", "bas", "बस"
    }

    def __init__(
        self,
        planner: Optional[TaskPlanner] = None,
        executor: Optional[TaskExecutor] = None,
        memory_mgr: Optional[TarkyaanMemoryManager] = None,
        observability: Optional[AgentObservabilityRecorder] = None,
        event_bus: Optional[EventBus] = None,
    ) -> None:
        self.planner = planner or TaskPlanner()
        self.executor = executor or TaskExecutor(event_bus=event_bus)
        self.memory_mgr = memory_mgr
        self.observability = observability or AgentObservabilityRecorder()
        self.event_bus = event_bus
        self._active_tasks: Dict[str, AutonomousTask] = {}
        self._lock = threading.RLock()

    def is_cancellation_intent(self, text: str) -> bool:
        """Detect if learner requested cancellation in English or Hindi."""
        t = text.lower().strip()
        # Direct word match
        for kw in self.CANCELLATION_KEYWORDS:
            if kw == t or re.search(rf"\b{re.escape(kw)}\b", t):
                return True
        return False

    def cancel_active_task(self, task_id: str, reason: str = "User requested cancellation") -> bool:
        """Immediately cancel an active autonomous task."""
        with self._lock:
            task = self._active_tasks.get(task_id)
            if not task:
                return False
            task.is_cancelled = True
            task.cancellation_reason = reason
            task.status = AgentTaskStatus.CANCELLED
            task.completed_at = _utc_now()

            if self.event_bus:
                self.event_bus.publish(
                    TarkyaanEvent.AGENT_TASK_CANCELLED,
                    {"task_id": task.task_id, "reason": reason},
                )

            if self.memory_mgr:
                self.memory_mgr.update_autonomous_task(
                    task_id=task.task_id,
                    status=AgentTaskStatus.CANCELLED.value,
                    cancellation_reason=reason,
                    completed=True,
                )
            return True

    def cancel_all_active_tasks(self, reason: str = "Global stop signal") -> int:
        """Cancel all currently active autonomous tasks."""
        cancelled_count = 0
        with self._lock:
            for tid, task in list(self._active_tasks.items()):
                if task.status in [AgentTaskStatus.EXECUTING, AgentTaskStatus.PLANNING, AgentTaskStatus.OBSERVING]:
                    self.cancel_active_task(tid, reason=reason)
                    cancelled_count += 1
        return cancelled_count

    def run_task(
        self,
        learner_id: str,
        goal_text: str,
        context: Optional[MultimodalContext] = None,
        max_steps: int = 10,
        confirmed_by_user: bool = False,
    ) -> AutonomousTask:
        """
        Execute full Observe -> Plan -> Act -> Verify cycle for a goal.
        Bounded by max_steps and strictly cancellable.
        """
        # 1. Observe & Plan
        task = self.planner.plan_task(
            learner_id=learner_id,
            goal_text=goal_text,
            context=context,
            max_steps=min(max_steps, 20),  # Hard upper limit 20
        )

        with self._lock:
            self._active_tasks[task.task_id] = task

        if self.event_bus:
            self.event_bus.publish(
                TarkyaanEvent.AGENT_TASK_CREATED,
                {"task_id": task.task_id, "goal": goal_text, "steps_count": len(task.steps)},
            )
            self.event_bus.publish(
                TarkyaanEvent.AGENT_PLAN_CREATED,
                {"task_id": task.task_id, "steps": [s.description for s in task.steps]},
            )

        if self.memory_mgr:
            self.memory_mgr.record_autonomous_task(
                task_id=task.task_id,
                learner_id=learner_id,
                goal=goal_text,
                status=AgentTaskStatus.EXECUTING.value,
                risk_level=task.goal.risk_level.value,
                max_steps=task.max_steps,
            )

        task.status = AgentTaskStatus.EXECUTING

        # 2. Sequential Act & Verify Loop
        for idx, step in enumerate(task.steps):
            if task.is_cancelled:
                task.status = AgentTaskStatus.CANCELLED
                break

            if task.is_budget_exhausted():
                task.status = AgentTaskStatus.TIMEOUT
                task.result_summary = "Task stopped: Step budget limit reached."
                break

            task.current_step_index += 1

            # Execute Step
            executed_step = self.executor.execute_step(
                task,
                step,
                confirmed_by_user=confirmed_by_user,
            )

            # Check if paused waiting for confirmation
            if executed_step.requires_confirmation:
                task.status = AgentTaskStatus.WAITING_PERMISSION
                task.result_summary = f"Waiting for confirmation to execute high-risk step: {step.description}"
                break

            # Check if step failed after verification
            if executed_step.status == AgentStepStatus.FAILED:
                # Self-correction check: retry if within limits
                if executed_step.retry_count < executed_step.max_retries:
                    executed_step.retry_count += 1
                    # Bounded single retry
                    executed_step = self.executor.execute_step(
                        task,
                        executed_step,
                        confirmed_by_user=confirmed_by_user,
                    )

                if executed_step.status == AgentStepStatus.FAILED:
                    task.status = AgentTaskStatus.FAILED
                    task.result_summary = f"Step {idx + 1} failed: {executed_step.error}"
                    if self.event_bus:
                        self.event_bus.publish(
                            TarkyaanEvent.AGENT_TASK_FAILED,
                            {"task_id": task.task_id, "error": executed_step.error},
                        )
                    break

        # 3. Finalize Status
        if task.status == AgentTaskStatus.EXECUTING:
            task.status = AgentTaskStatus.COMPLETED
            task.completed_at = _utc_now()
            task.result_summary = f"Successfully completed all {len(task.steps)} steps with empirical verification."
            if self.event_bus:
                self.event_bus.publish(
                    TarkyaanEvent.AGENT_TASK_COMPLETED,
                    {"task_id": task.task_id, "summary": task.result_summary},
                )

        if self.memory_mgr:
            self.memory_mgr.update_autonomous_task(
                task_id=task.task_id,
                status=task.status.value,
                current_step=task.current_step_index,
                result_summary=task.result_summary,
                completed=task.status in [AgentTaskStatus.COMPLETED, AgentTaskStatus.FAILED, AgentTaskStatus.CANCELLED],
            )

        return task
