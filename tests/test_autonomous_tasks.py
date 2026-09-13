"""Tests for Tarkyaan Autonomous Task Execution, Bounded Steps, and Safety Gates."""

import pytest

from tarkyaan.capabilities.registry import (
    CapabilityCategory,
    CapabilityDefinition,
    CapabilityRegistry,
    CapabilityStatus,
)
from tarkyaan.events.event_bus import EventEnvelope, TarkyaanEvent, event_bus
from tarkyaan.safety.permissions import PermissionCategory, PermissionManager, PermissionStatus
from tarkyaan.safety.policies import RiskLevel
from tarkyaan.tasks.executor import AutonomousTaskExecutor
from tarkyaan.tasks.models import (
    AutonomousTask,
    TaskExecutionStatus,
    TaskStep,
)


def test_autonomous_task_success_execution():
    """Verify autonomous task executes all valid steps and records audit trail."""
    reg = CapabilityRegistry()
    reg.register(
        CapabilityDefinition(
            name="research.web_search",
            category=CapabilityCategory.RESEARCH,
            description="Search provider query",
            status=CapabilityStatus.AVAILABLE,
            risk_level=RiskLevel.LOW,
            required_permissions=[PermissionCategory.NETWORK],
        )
    )

    executor = AutonomousTaskExecutor(registry=reg)

    task = AutonomousTask(
        task_id="task_exec_101",
        learner_id="learner_001",
        title="Find AsyncIO Tutorials",
        goal="Discover authoritative async documentation",
        steps=[
            TaskStep(
                step_order=1,
                capability_name="research.web_search",
                description="Query Python docs",
                parameters={"query": "python asyncio tutorial"},
            ),
        ],
    )

    result = executor.execute_task(task)

    assert result.status == TaskExecutionStatus.COMPLETED
    assert result.steps[0].status == TaskExecutionStatus.COMPLETED
    assert len(result.audit_trail) == 1
    assert result.audit_trail[0]["capability"] == "research.web_search"


def test_autonomous_task_permission_gate():
    """Verify task step fails when required permission is not granted."""
    reg = CapabilityRegistry()
    reg.register(
        CapabilityDefinition(
            name="computer.capture_screen",
            category=CapabilityCategory.COMPUTER_CONTROL,
            description="Screen capture",
            status=CapabilityStatus.REQUIRES_PERMISSION,
            risk_level=RiskLevel.HIGH,
            required_permissions=[PermissionCategory.SCREEN_RECORDING],
        )
    )

    executor = AutonomousTaskExecutor(registry=reg)

    task = AutonomousTask(
        task_id="task_perm_gate",
        learner_id="learner_001",
        title="Inspect Screen Context",
        goal="Capture screen context",
        steps=[
            TaskStep(
                step_order=1,
                capability_name="computer.capture_screen",
                description="Capture current active window",
            ),
        ],
    )

    result = executor.execute_task(task)

    assert result.status == TaskExecutionStatus.FAILED
    assert result.steps[0].status == TaskExecutionStatus.FAILED
    assert result.steps[0].error_message is not None
    assert "required but not granted" in result.steps[0].error_message


def test_autonomous_task_cancellation():
    """Verify cancellation aborts execution before subsequent steps run."""
    reg = CapabilityRegistry()
    reg.register(
        CapabilityDefinition(
            name="step1",
            category=CapabilityCategory.RESEARCH,
            description="Step 1",
            status=CapabilityStatus.AVAILABLE,
            risk_level=RiskLevel.LOW,
        )
    )
    reg.register(
        CapabilityDefinition(
            name="step2",
            category=CapabilityCategory.RESEARCH,
            description="Step 2",
            status=CapabilityStatus.AVAILABLE,
            risk_level=RiskLevel.LOW,
        )
    )

    executor = AutonomousTaskExecutor(registry=reg)

    task = AutonomousTask(
        task_id="task_cancel_demo",
        learner_id="learner_001",
        title="Multi-step Workflow",
        goal="Execute multiple steps",
        steps=[
            TaskStep(step_order=1, capability_name="step1", description="First step"),
            TaskStep(step_order=2, capability_name="step2", description="Second step"),
        ],
    )

    # Cancel task using executor API
    executor.cancel_task(task.task_id)

    result = executor.execute_task(task)
    assert result.status == TaskExecutionStatus.CANCELLED


def test_autonomous_task_timeout():
    """Verify task aborts when total runtime exceeds configured timeout."""
    import time
    reg = CapabilityRegistry()
    reg.register(
        CapabilityDefinition(
            name="slow_step",
            category=CapabilityCategory.RESEARCH,
            description="Slow operation",
            status=CapabilityStatus.AVAILABLE,
            risk_level=RiskLevel.LOW,
            handler=lambda params: time.sleep(1.05),
        )
    )

    executor = AutonomousTaskExecutor(registry=reg)

    task = AutonomousTask(
        task_id="task_timeout_demo",
        learner_id="learner_001",
        title="Fast Timeout Task",
        goal="Test timeout enforcement",
        timeout_seconds=1,  # 1 second timeout triggers on step 2
        steps=[
            TaskStep(step_order=1, capability_name="slow_step", description="Slow 1"),
            TaskStep(step_order=2, capability_name="slow_step", description="Slow 2"),
        ],
    )

    result = executor.execute_task(task)
    assert result.status == TaskExecutionStatus.TIMED_OUT

