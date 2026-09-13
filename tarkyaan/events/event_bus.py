"""
Tarkyaan Event Bus and Educational Event Taxonomy.
Independent, thread-safe publish/subscribe subsystem.
"""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TarkyaanEvent(str, Enum):
    """Event catalog for educational intelligence, companion state, and capabilities."""

    # 1. Lifecycle & System
    APPLICATION_STARTED = "application_started"
    APPLICATION_SHUTDOWN = "application_shutdown"
    HEALTH_STATUS_CHANGED = "health_status_changed"

    # 2. Companion & Voice
    VOICE_LISTENING_STARTED = "voice_listening_started"
    VOICE_LISTENING_FINISHED = "voice_listening_finished"
    VOICE_SPEAKING_STARTED = "voice_speaking_started"
    VOICE_SPEAKING_FINISHED = "voice_speaking_finished"
    VOICE_INTERRUPTED = "voice_interrupted"
    USER_INPUT_RECEIVED = "user_input_received"
    INTENT_RESOLVED = "intent_resolved"

    # 3. Learning, Teaching, Practice & Sessions (Phase 5)
    LEARNING_SESSION_STARTED = "learning_session_started"
    LEARNING_SESSION_ENDED = "learning_session_ended"
    SESSION_STAGE_CHANGED = "session_stage_changed"
    SESSION_PAUSED = "session_paused"
    SESSION_RESUMED = "session_resumed"
    TEACHING_STARTED = "teaching_started"
    TEACHING_COMPLETED = "teaching_completed"
    PRACTICE_STARTED = "practice_started"
    PRACTICE_COMPLETED = "practice_completed"
    QUESTION_PRESENTED = "question_presented"
    ANSWER_RECEIVED = "answer_received"
    ANSWER_EVALUATED = "answer_evaluated"
    HINT_REQUESTED = "hint_requested"
    HINT_PROVIDED = "hint_provided"
    DIAGNOSTIC_SESSION_STARTED = "diagnostic_session_started"
    DIAGNOSTIC_ANSWER_EVALUATED = "diagnostic_answer_evaluated"
    DIAGNOSTIC_SESSION_COMPLETED = "diagnostic_session_completed"
    KNOWLEDGE_GAP_DETECTED = "knowledge_gap_detected"
    MISCONCEPTION_DETECTED = "misconception_detected"
    MASTERY_UPDATED = "mastery_updated"

    # 4. Planning & Tasks
    PLAN_PROPOSED = "plan_proposed"
    PLAN_ACTIVATED = "plan_activated"
    PLAN_REVISED = "plan_revised"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_CANCELLED = "task_cancelled"
    MILESTONE_ACHIEVED = "milestone_achieved"

    # 5. Research & Intelligence
    RESEARCH_STARTED = "research_started"
    RESEARCH_CANDIDATES_DISCOVERED = "research_candidates_discovered"
    RESOURCE_EVALUATED = "resource_evaluated"
    RESOURCE_CURATED = "resource_curated"
    RESEARCH_COMPLETED = "research_completed"
    RESEARCH_FAILED = "research_failed"

    # 6. Capabilities & Automation
    CAPABILITY_INVOKED = "capability_invoked"
    CAPABILITY_COMPLETED = "capability_completed"
    CAPABILITY_FAILED = "capability_failed"
    CONFIRMATION_REQUESTED = "confirmation_requested"
    CONFIRMATION_RESOLVED = "confirmation_resolved"
    SAFETY_VIOLATION_BLOCKED = "safety_violation_blocked"


class EventEnvelope(BaseModel):
    """Structured envelope wrapping an emitted event and typed payload."""
    event: TarkyaanEvent
    payload: Dict[str, Any] = Field(default_factory=dict)
    learner_id: Optional[str] = None
    source: str = Field(default="system")
    timestamp: datetime = Field(default_factory=_utc_now)


EventHandler = Callable[[EventEnvelope], None]


class EventBus:
    """Thread-safe, non-blocking in-memory publish/subscribe event bus."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._subscribers: Dict[TarkyaanEvent, List[EventHandler]] = {}
        self._global_subscribers: List[EventHandler] = []
        self._history: List[EventEnvelope] = []
        self._max_history = 500

    def subscribe(self, event: TarkyaanEvent, handler: EventHandler) -> None:
        """Subscribe a handler to a specific event type."""
        with self._lock:
            self._subscribers.setdefault(event, []).append(handler)

    def subscribe_all(self, handler: EventHandler) -> None:
        """Subscribe a handler to all events across the system."""
        with self._lock:
            self._global_subscribers.append(handler)

    def unsubscribe(self, event: TarkyaanEvent, handler: EventHandler) -> bool:
        """Unsubscribe a specific handler from an event."""
        with self._lock:
            if event in self._subscribers and handler in self._subscribers[event]:
                self._subscribers[event].remove(handler)
                return True
            return False

    def publish(
        self,
        event: TarkyaanEvent,
        payload: Optional[Dict[str, Any]] = None,
        learner_id: Optional[str] = None,
        source: str = "system"
    ) -> EventEnvelope:
        """
        Publish an event to all subscribed handlers synchronously and safely.
        Exceptions in handlers are captured to prevent crashing callers.
        """
        envelope = EventEnvelope(
            event=event,
            payload=payload or {},
            learner_id=learner_id,
            source=source
        )

        with self._lock:
            self._history.append(envelope)
            if len(self._history) > self._max_history:
                self._history.pop(0)

            # Copy lists to execute outside lock
            handlers = list(self._subscribers.get(event, []))
            global_handlers = list(self._global_subscribers)

        for h in handlers + global_handlers:
            try:
                h(envelope)
            except Exception as exc:  # noqa: BLE001
                # Log or track failure; do not interrupt publish loop
                pass

        return envelope

    def get_history(
        self,
        event: Optional[TarkyaanEvent] = None,
        learner_id: Optional[str] = None,
        limit: int = 50
    ) -> List[EventEnvelope]:
        """Retrieve recent event history with optional filtering."""
        with self._lock:
            res = list(self._history)

        if event:
            res = [e for e in res if e.event == event]
        if learner_id:
            res = [e for e in res if e.learner_id == learner_id]

        return res[-limit:]

    def clear(self) -> None:
        """Clear all subscribers and history (useful for test isolation)."""
        with self._lock:
            self._subscribers.clear()
            self._global_subscribers.clear()
            self._history.clear()


# Global event bus singleton for Tarkyaan
event_bus = EventBus()
