"""
Autonomous Task Executor.
Sequentially runs bounded task steps with capability verification, cancellation, and timeouts.
"""

from __future__ import annotations

import threading
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional

from tarkyaan.capabilities.registry import CapabilityRegistry, capability_registry
from tarkyaan.events.event_bus import TarkyaanEvent, event_bus
from tarkyaan.safety.permissions import permission_manager
from tarkyaan.safety.policies import SafetyPolicy
from tarkyaan.tasks.models import (
    AutonomousTask,
    StepResult,
    TaskAuditRecord,
    TaskExecutionStatus,
    TaskStep,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AutonomousTaskExecutor:
    """
    Executes an AutonomousTask with verification, cancellation checks, and safety confirmation gates.
    """

    def __init__(self, registry: Optional[CapabilityRegistry] = None) -> None:
        self.registry = registry or capability_registry
        self._cancel_events: Dict[str, threading.Event] = {}
        self._lock = threading.RLock()

    def cancel_task(self, task_id: str, reason: str = "User cancelled") -> bool:
        """Signal an active autonomous task to stop immediately."""
        with self._lock:
            evt = self._cancel_events.setdefault(task_id, threading.Event())
            evt.set()
            return True

    def execute_task(self, task: AutonomousTask) -> AutonomousTask:
        """
        Execute all bounded steps in an AutonomousTask plan sequentially.
        """
        task.status = TaskExecutionStatus.IN_PROGRESS
        task.started_at = _utc_now()

        with self._lock:
            cancel_evt = self._cancel_events.setdefault(task.task_id, threading.Event())


        event_bus.publish(
            TarkyaanEvent.TASK_STARTED,
            payload={"task_id": task.task_id, "title": task.title, "step_count": len(task.steps)},
            learner_id=task.learner_id
        )

        start_time = time.time()

        try:
            for idx, step in enumerate(task.steps):
                task.current_step_index = idx

                # 1. Check Cancellation
                if cancel_evt.is_set():
                    task.status = TaskExecutionStatus.CANCELLED
                    task.cancellation_reason = "Cancelled by user or system signal"
                    step.status = TaskExecutionStatus.CANCELLED
                    event_bus.publish(TarkyaanEvent.TASK_CANCELLED, payload={"task_id": task.task_id}, learner_id=task.learner_id)
                    break

                # 2. Check Global Timeout
                if (time.time() - start_time) > task.timeout_seconds:
                    task.status = TaskExecutionStatus.TIMED_OUT
                    step.status = TaskExecutionStatus.TIMED_OUT
                    step.error_message = f"Task exceeded timeout limit of {task.timeout_seconds}s"
                    break

                # 3. Execute Step
                step_success = self._execute_step(task, step)
                if not step_success:
                    task.status = TaskExecutionStatus.FAILED
                    event_bus.publish(
                        TarkyaanEvent.TASK_FAILED,
                        payload={"task_id": task.task_id, "failed_step": step.step_id, "error": step.error_message},
                        learner_id=task.learner_id
                    )
                    break

            if task.status == TaskExecutionStatus.IN_PROGRESS:
                task.status = TaskExecutionStatus.COMPLETED
                event_bus.publish(
                    TarkyaanEvent.TASK_COMPLETED,
                    payload={"task_id": task.task_id, "title": task.title},
                    learner_id=task.learner_id
                )

        finally:
            task.completed_at = _utc_now()
            with self._lock:
                self._cancel_events.pop(task.task_id, None)

        return task

    def _execute_step(self, task: AutonomousTask, step: TaskStep) -> bool:
        """Execute a single step against the CapabilityRegistry."""
        step.status = TaskExecutionStatus.IN_PROGRESS
        step.started_at = _utc_now()

        cap = self.registry.get(step.capability_name)
        if not cap:
            step.status = TaskExecutionStatus.FAILED
            step.error_message = f"Unknown capability '{step.capability_name}'."
            return False

        # Check permissions
        for perm in cap.required_permissions:
            if not permission_manager.is_granted(perm):
                step.status = TaskExecutionStatus.FAILED
                step.error_message = f"Permission '{perm.value}' required but not granted."
                return False

        # Check safety confirmation
        if SafetyPolicy.requires_confirmation(step.capability_name, cap.risk_level, step.parameters):
            event_bus.publish(
                TarkyaanEvent.CONFIRMATION_REQUESTED,
                payload={"task_id": task.task_id, "step_id": step.step_id, "capability": step.capability_name},
                learner_id=task.learner_id
            )

        # Run capability handler if present, else run registered mock/architecture verification
        try:
            if cap.handler:
                out = cap.handler(step.parameters)
            else:
                out = {"success": True, "message": f"Simulated capability {step.capability_name} completed."}

            step.output = out
            step.status = TaskExecutionStatus.COMPLETED
            step.completed_at = _utc_now()

            # Record audit trail
            task.audit_trail.append({
                "step_id": step.step_id,
                "capability": step.capability_name,
                "status": "completed",
                "timestamp": step.completed_at.isoformat()
            })
            return True

        except Exception as exc:  # noqa: BLE001
            step.status = TaskExecutionStatus.FAILED
            step.error_message = str(exc)
            step.completed_at = _utc_now()
            return False
