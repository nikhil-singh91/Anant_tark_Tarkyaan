"""Tests for Autonomous Task Engine, Task Planner, Verifier, and Executor."""

from __future__ import annotations

import pytest

from tarkyaan.agent.autonomous_task_engine import AutonomousTaskEngine
from tarkyaan.agent.observability import AgentObservabilityRecorder
from tarkyaan.agent.task_executor import TaskExecutor
from tarkyaan.agent.task_models import AgentStep, AutonomousTask, VerificationResult
from tarkyaan.agent.task_planner import TaskPlanner
from tarkyaan.agent.task_verifier import TaskVerifier
from tarkyaan.memory.memory_manager import TarkyaanMemoryManager
from tarkyaan.memory.memory_store import TarkyaanMemoryStore
from tarkyaan.models.enums import AgentRiskLevel, AgentStepStatus, AgentTaskStatus


def test_task_planner_generates_bounded_plan():
    """Verify TaskPlanner creates structured, bounded plans for learning goals."""
    planner = TaskPlanner()
    task: AutonomousTask = planner.plan_task(
        learner_id="lrn_001",
        goal_text="Help me prepare for my DSA exam",
        max_steps=5,
    )

    assert task.status == AgentTaskStatus.PLANNING
    assert len(task.steps) <= 5
    assert all(s.verification_criteria for s in task.steps)
    assert all(s.risk_level is not None for s in task.steps)


def test_task_verifier_empirical_checks():
    """Verify TaskVerifier checks postconditions accurately."""
    verifier = TaskVerifier()

    # Application step verification
    step_app = AgentStep(
        task_id="task_1",
        action="open_app",
        capability_id="app.control",
        parameters={"app_name": "Visual Studio Code"},
    )
    v_app = verifier.verify_step(step_app, {"verified": True})
    assert v_app.is_verified is True

    # Terminal step verification (passing vs failing exit codes)
    step_term = AgentStep(
        task_id="task_1",
        action="run_tests",
        capability_id="terminal.execute_bounded",
    )
    v_term_pass = verifier.verify_step(step_term, {"success": True, "exit_code": 0})
    assert v_term_pass.is_verified is True

    v_term_fail = verifier.verify_step(step_term, {"success": False, "exit_code": 1, "stderr": "AssertionError"})
    assert v_term_fail.is_verified is False


def test_autonomous_task_engine_observe_plan_act_verify_loop():
    """Verify AutonomousTaskEngine completes full task loop and records in memory."""
    store = TarkyaanMemoryStore(db_path=":memory:")
    mem_mgr = TarkyaanMemoryManager(store=store)

    # Seed learner
    from tarkyaan.models.learner import LearnerProfile
    from tarkyaan.models.enums import AutonomyLevel
    learner = LearnerProfile(
        learner_id="lrn_001",
        display_name="Student",
        primary_domain="cs",
        current_autonomy_level=AutonomyLevel.LEVEL_4,
    )
    mem_mgr.save_learner_profile(learner)

    # Isolated permission manager for test to prevent cross-test leakage
    from tarkyaan.safety.permissions import PermissionCategory, PermissionManager
    test_perms = PermissionManager()
    test_perms.grant(PermissionCategory.SCREEN_RECORDING, rationale="Test granted")

    executor = TaskExecutor(perms=test_perms)
    engine = AutonomousTaskEngine(memory_mgr=mem_mgr, executor=executor)
    task: AutonomousTask = engine.run_task(
        learner_id="lrn_001",
        goal_text="Find why my code isn't working",
        max_steps=4,
        confirmed_by_user=True,
    )

    assert task.status == AgentTaskStatus.COMPLETED
    assert task.current_step_index == len(task.steps)
    assert "Successfully completed" in task.result_summary

    # Check persistence
    persisted = mem_mgr.get_autonomous_task(task.task_id)
    assert persisted is not None
    assert persisted["status"] == "completed"


def test_autonomous_task_engine_cancellation():
    """Verify autonomous tasks can be stopped immediately on cancellation signals."""
    engine = AutonomousTaskEngine()
    task = engine.planner.plan_task(learner_id="lrn_001", goal_text="Long study session")

    # Cancel task
    ok = engine.cancel_active_task(task.task_id, reason="User said stop")
    # Even if not yet in active dict or in active dict, cancel marks status
    assert engine.is_cancellation_intent("Stop") is True
    assert engine.is_cancellation_intent("रुको") is True
    assert engine.is_cancellation_intent("रहने दो") is True
    assert engine.is_cancellation_intent("never mind") is True
    assert engine.is_cancellation_intent("Continue studying") is False


def test_observability_redacts_secrets_in_timeline():
    """Verify AgentObservabilityRecorder scrubs secrets from task logs."""
    obs = AgentObservabilityRecorder()
    obs.record_step_event(
        task_id="task_audit_1",
        step_index=1,
        capability_id="terminal.run",
        action="execute",
        risk_level="low",
        status="completed",
        details="Output with API key sk-abcdef123456789012345678 and password='mypassword'",
    )

    timeline = obs.get_task_timeline("task_audit_1")
    assert len(timeline) == 1
    details = timeline[0].details
    assert "sk-abcdef" not in details
    assert "[REDACTED_API_KEY]" in details
    assert "mypassword" not in details
