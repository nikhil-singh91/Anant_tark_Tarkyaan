"""Tests for Tarkyaan EventBus and Event Taxonomy."""

import pytest
from tarkyaan.events.event_bus import (
    EventBus,
    EventEnvelope,
    TarkyaanEvent,
    event_bus,
)


def test_event_bus_publish_and_subscribe():
    """Verify handlers receive published events with typed envelopes."""
    bus = EventBus()
    received = []

    def on_research_started(env: EventEnvelope) -> None:
        received.append(env)

    bus.subscribe(TarkyaanEvent.RESEARCH_STARTED, on_research_started)

    env = bus.publish(
        event=TarkyaanEvent.RESEARCH_STARTED,
        payload={"query": "python asyncio", "depth": "standard"},
        learner_id="learner_123",
        source="research_engine",
    )

    assert len(received) == 1
    assert received[0].event == TarkyaanEvent.RESEARCH_STARTED
    assert received[0].payload["query"] == "python asyncio"
    assert received[0].learner_id == "learner_123"
    assert received[0].source == "research_engine"


def test_event_bus_global_subscriber():
    """Verify subscribe_all receives events from all domains."""
    bus = EventBus()
    events_log = []

    bus.subscribe_all(lambda env: events_log.append(env.event))

    bus.publish(TarkyaanEvent.VOICE_LISTENING_STARTED)
    bus.publish(TarkyaanEvent.DIAGNOSTIC_SESSION_STARTED)
    bus.publish(TarkyaanEvent.PLAN_ACTIVATED)

    assert events_log == [
        TarkyaanEvent.VOICE_LISTENING_STARTED,
        TarkyaanEvent.DIAGNOSTIC_SESSION_STARTED,
        TarkyaanEvent.PLAN_ACTIVATED,
    ]


def test_event_bus_unsubscribe():
    """Verify unregistering a listener prevents further notifications."""
    bus = EventBus()
    counter = {"count": 0}

    def handler(env: EventEnvelope) -> None:
        counter["count"] += 1

    bus.subscribe(TarkyaanEvent.MASTERY_UPDATED, handler)
    bus.publish(TarkyaanEvent.MASTERY_UPDATED)
    assert counter["count"] == 1

    unsubscribed = bus.unsubscribe(TarkyaanEvent.MASTERY_UPDATED, handler)
    assert unsubscribed is True

    bus.publish(TarkyaanEvent.MASTERY_UPDATED)
    assert counter["count"] == 1


def test_event_bus_error_resilience():
    """Verify exceptions in an event handler do not crash publisher or other handlers."""
    bus = EventBus()
    called = []

    def crashing_handler(env: EventEnvelope) -> None:
        raise RuntimeError("Simulated unhandled subscriber exception")

    def healthy_handler(env: EventEnvelope) -> None:
        called.append(env.event)

    bus.subscribe(TarkyaanEvent.TASK_COMPLETED, crashing_handler)
    bus.subscribe(TarkyaanEvent.TASK_COMPLETED, healthy_handler)

    # Should not raise
    bus.publish(TarkyaanEvent.TASK_COMPLETED, payload={"task_id": "task_1"})
    assert called == [TarkyaanEvent.TASK_COMPLETED]


def test_event_bus_history_and_filtering():
    """Verify event history maintains chronological order and supports filtering."""
    bus = EventBus()
    bus.publish(TarkyaanEvent.RESEARCH_STARTED, learner_id="learner_a")
    bus.publish(TarkyaanEvent.RESEARCH_COMPLETED, learner_id="learner_a")
    bus.publish(TarkyaanEvent.RESEARCH_STARTED, learner_id="learner_b")

    all_history = bus.get_history()
    assert len(all_history) == 3

    learner_a_history = bus.get_history(learner_id="learner_a")
    assert len(learner_a_history) == 2

    research_started_history = bus.get_history(event=TarkyaanEvent.RESEARCH_STARTED)
    assert len(research_started_history) == 2
