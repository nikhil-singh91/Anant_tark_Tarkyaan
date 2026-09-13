"""Tests for Tarkyaan ResearchEngine, Persistence, and Plan Integration."""

import pytest

from tarkyaan.events.event_bus import EventEnvelope, TarkyaanEvent, event_bus
from tarkyaan.memory.memory_manager import TarkyaanMemoryManager
from tarkyaan.memory.memory_store import TarkyaanMemoryStore
from tarkyaan.models.enums import TaskStatus, TaskType
from tarkyaan.models.learner import LearnerProfile
from tarkyaan.models.planning import LearningPlan, LearningTask, StudyPhase
from tarkyaan.research.providers.mock import MockSearchProvider
from tarkyaan.research.research_engine import ResearchEngine


@pytest.fixture
def test_env():
    """Create isolated in-memory store, memory manager, and research engine."""
    store = TarkyaanMemoryStore(":memory:")
    memory = TarkyaanMemoryManager(store=store)
    provider = MockSearchProvider()
    engine = ResearchEngine(memory_manager=memory, search_provider=provider)

    learner = LearnerProfile(
        learner_id="test_learner_42",
        display_name="Dev Learner",
        primary_domain="Software Engineering",
        preferred_language="Python",
    )
    memory.save_learner_profile(learner)

    return {"store": store, "memory": memory, "provider": provider, "engine": engine, "learner": learner}


def test_research_task_end_to_end(test_env):
    """Verify research_task discovers candidates, curates bundle, attaches to task, and persists."""
    engine = test_env["engine"]
    memory = test_env["memory"]
    learner = test_env["learner"]

    task = LearningTask(
        task_id="task_rec_01",
        plan_id="plan_test_01",
        phase_id="phase_01",
        concept_id="recursion",
        title="Understand Base Cases and Recursive Invariants",
        task_type=TaskType.LEARN,
        difficulty=2,
    )

    events_received = []

    def on_event(env: EventEnvelope) -> None:
        events_received.append(env.event)

    event_bus.subscribe_all(on_event)

    bundle = engine.research_task(task=task, learner=learner, max_resources=3)

    # 1. Bundle validation
    assert bundle.task_id == "task_rec_01"
    assert bundle.concept_id == "recursion"
    assert bundle.primary_resource_id is not None
    assert len(bundle.all_resource_ids) >= 2
    assert len(task.resource_ids) == len(bundle.all_resource_ids)

    # 2. Persistence validation
    saved_resources = memory.list_resources_for_task("task_rec_01")
    assert len(saved_resources) >= 2
    assert any(r.resource_id == bundle.primary_resource_id for r in saved_resources)

    # 3. History validation
    history = memory.get_research_history(learner.learner_id)
    assert len(history) >= 1
    assert history[0].task_id == "task_rec_01"
    assert history[0].concept_id == "recursion"

    # 4. Event validation
    assert TarkyaanEvent.RESEARCH_STARTED in events_received
    assert TarkyaanEvent.RESEARCH_COMPLETED in events_received


def test_research_task_resource_reuse(test_env):
    """Verify research engine reuses stored resources for same concept without re-searching."""
    engine = test_env["engine"]
    provider = test_env["provider"]
    learner = test_env["learner"]

    # First task on hashing
    task1 = LearningTask(
        task_id="task_hash_01",
        plan_id="plan_01",
        phase_id="phase_01",
        concept_id="hashing",
        title="Hash Map Bucket Array Mechanics",
        task_type=TaskType.LEARN,
        difficulty=3,
    )
    bundle1 = engine.research_task(task=task1, learner=learner, max_resources=3)
    first_call_count = len(provider.call_history)
    assert first_call_count > 0

    # Second task on same concept
    task2 = LearningTask(
        task_id="task_hash_02",
        plan_id="plan_01",
        phase_id="phase_01",
        concept_id="hashing",
        title="Collision Resolution Practice",
        task_type=TaskType.PRACTICE,
        difficulty=3,
    )
    bundle2 = engine.research_task(task=task2, learner=learner, max_resources=3, force_refresh=False)

    # Provider should NOT have been called again due to reuse
    assert len(provider.call_history) == first_call_count
    assert len(bundle2.all_resource_ids) >= 1
    assert task2.resource_ids == bundle2.all_resource_ids


def test_research_plan_orchestration(test_env):
    """Verify research_plan enriches eligible tasks across all phases."""
    engine = test_env["engine"]
    learner = test_env["learner"]
    memory = test_env["memory"]

    task_a = LearningTask(
        task_id="task_bs_learn",
        plan_id="plan_algo",
        phase_id="p1",
        concept_id="binary_search",
        title="Monotonic Property",
        task_type=TaskType.LEARN,
    )
    task_b = LearningTask(
        task_id="task_bs_quiz",
        plan_id="plan_algo",
        phase_id="p1",
        concept_id="binary_search",
        title="Check understanding",
        task_type=TaskType.ASSESSMENT,  # Assessments don't need external web resources
    )

    phase = StudyPhase(
        phase_id="p1",
        name="Phase 1: Binary Search",
        phase_order=1,
        tasks=[task_a, task_b],
    )

    plan = LearningPlan(
        plan_id="plan_algo",
        learner_id=learner.learner_id,
        goal_id="goal_algorithms",
        title="Algorithm Mastery",
        phases=[phase],
        tasks=[task_a, task_b],
    )

    researched_plan = engine.research_plan(plan=plan, learner=learner, max_resources_per_task=2)

    # Task A was eligible and got resources
    assert len(researched_plan.phases[0].tasks[0].resource_ids) >= 1
    # Task B was ASSESSMENT and skipped external web research
    assert len(researched_plan.phases[0].tasks[1].resource_ids) == 0


def test_research_task_failure_fallback(test_env):
    """Verify research_task gracefully handles search failure."""
    engine = test_env["engine"]
    provider = test_env["provider"]
    learner = test_env["learner"]

    provider.should_fail = True
    provider.failure_message = "Rate limit reached"

    task = LearningTask(
        task_id="task_fail_01",
        plan_id="plan_01",
        phase_id="phase_01",
        concept_id="quantum_computing",
        title="Quantum Gates",
        task_type=TaskType.LEARN,
    )

    bundle = engine.research_task(task=task, learner=learner)
    assert len(bundle.all_resource_ids) == 0
    assert len(task.resource_ids) == 0
