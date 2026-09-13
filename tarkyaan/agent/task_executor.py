"""
Task Executor Subsystem.
Sequentially dispatches steps to capabilities, checks cancellation tokens,
enforces permission/confirmation gates, and triggers postcondition verification.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional

from tarkyaan.agent.observability import AgentObservabilityRecorder
from tarkyaan.agent.task_models import AgentStep, AutonomousTask, VerificationResult
from tarkyaan.agent.task_verifier import TaskVerifier
from tarkyaan.capabilities.registry import CapabilityRegistry, capability_registry
from tarkyaan.events.event_bus import EventBus, TarkyaanEvent
from tarkyaan.models.enums import AgentRiskLevel, AgentStepStatus, AgentTaskStatus
from tarkyaan.safety.permissions import PermissionCategory, PermissionManager, permission_manager


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TaskExecutor:
    """
    Executes steps of an AutonomousTask with permission gating,
    cancellation monitoring, and verification enforcement.
    """

    def __init__(
        self,
        registry: Optional[CapabilityRegistry] = None,
        verifier: Optional[TaskVerifier] = None,
        observability: Optional[AgentObservabilityRecorder] = None,
        perms: Optional[PermissionManager] = None,
        event_bus: Optional[EventBus] = None,
    ) -> None:
        self.registry = registry or capability_registry
        self.verifier = verifier or TaskVerifier()
        self.observability = observability or AgentObservabilityRecorder()
        self.permission_mgr = perms or permission_manager
        self.event_bus = event_bus
        self._handlers: Dict[str, Callable[[AgentStep], Dict[str, Any]]] = {}

    def register_step_handler(self, capability_prefix: str, handler: Callable[[AgentStep], Dict[str, Any]]) -> None:
        """Register custom capability execution handler for agent dispatch."""
        self._handlers[capability_prefix] = handler

    def execute_step(
        self,
        task: AutonomousTask,
        step: AgentStep,
        confirmed_by_user: bool = False,
    ) -> AgentStep:
        """
        Execute an atomic agent step with strict safety and verification.
        """
        # 1. Check task-level cancellation
        if task.is_cancelled:
            step.status = AgentStepStatus.CANCELLED
            step.error = task.cancellation_reason or "Task cancelled by user."
            return step

        step.status = AgentStepStatus.RUNNING
        step.started_at = _utc_now()

        if self.event_bus:
            self.event_bus.publish(
                TarkyaanEvent.AGENT_STEP_STARTED,
                {"task_id": task.task_id, "step_index": step.step_index, "action": step.action},
            )

        self.observability.record_step_event(
            task_id=task.task_id,
            step_index=step.step_index,
            capability_id=step.capability_id,
            action=step.action,
            risk_level=step.risk_level.value,
            status="started",
            details=f"Executing {step.description}",
        )

        # 2. Risk & Confirmation Gate
        if step.risk_level in [AgentRiskLevel.HIGH, AgentRiskLevel.CRITICAL] and not confirmed_by_user:
            step.status = AgentStepStatus.PENDING
            step.requires_confirmation = True
            step.error = "Step paused: High-risk action requires explicit user confirmation."
            if self.event_bus:
                self.event_bus.publish(
                    TarkyaanEvent.AGENT_WAITING_PERMISSION,
                    {"task_id": task.task_id, "step_index": step.step_index, "action": step.action},
                )
            return step

        # 3. Permission Gate
        perm_error = self._check_required_permissions(step.capability_id)
        if perm_error:
            step.status = AgentStepStatus.FAILED
            step.error = perm_error
            self.observability.record_step_event(
                task_id=task.task_id,
                step_index=step.step_index,
                capability_id=step.capability_id,
                action=step.action,
                risk_level=step.risk_level.value,
                status="blocked",
                details=perm_error,
            )
            return step

        # 4. Capability Execution
        output = self._dispatch_action(step)
        step.result = output

        # 5. Verification Phase (Observe -> Verify)
        if self.event_bus:
            self.event_bus.publish(
                TarkyaanEvent.AGENT_VERIFICATION_STARTED,
                {"task_id": task.task_id, "step_index": step.step_index},
            )

        verif: VerificationResult = self.verifier.verify_step(step, output)
        step.verification_status = "verified" if verif.is_verified else "failed"
        step.verification_notes = verif.notes
        step.completed_at = _utc_now()

        if verif.is_verified:
            step.status = AgentStepStatus.COMPLETED
        else:
            step.status = AgentStepStatus.FAILED
            step.error = verif.error or "Verification postcondition check failed."

        if self.event_bus:
            self.event_bus.publish(
                TarkyaanEvent.AGENT_STEP_COMPLETED,
                {
                    "task_id": task.task_id,
                    "step_index": step.step_index,
                    "status": step.status.value,
                    "verified": verif.is_verified,
                },
            )

        self.observability.record_step_event(
            task_id=task.task_id,
            step_index=step.step_index,
            capability_id=step.capability_id,
            action=step.action,
            risk_level=step.risk_level.value,
            status=step.status.value,
            details=f"Completed. Verified: {verif.is_verified}. Notes: {verif.notes}",
            is_verified=verif.is_verified,
        )

        return step

    def _check_required_permissions(self, capability_id: str) -> Optional[str]:
        """Check if capability requires macOS permissions that are not granted."""
        cap_id = capability_id.lower()
        if "screen" in cap_id:
            if not self.permission_mgr.is_granted(PermissionCategory.SCREEN_RECORDING):
                return "Screen Recording permission is not granted."
        if "computer" in cap_id:
            if not self.permission_mgr.is_granted(PermissionCategory.ACCESSIBILITY):
                return "Accessibility permission is not granted for computer control."
        return None

    def _dispatch_action(self, step: AgentStep) -> Dict[str, Any]:
        """Dispatch action to registered handler or default simulated execution."""
        cap_prefix = step.capability_id.split(".")[0]
        if cap_prefix in self._handlers:
            return self._handlers[cap_prefix](step)

        # Default handler output
        return {
            "success": True,
            "exit_code": 0,
            "action": step.action,
            "capability": step.capability_id,
            "summary": f"Executed {step.action} successfully.",
            "verified": True,
        }
