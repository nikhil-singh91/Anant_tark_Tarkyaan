# TARKYAAN — Event Stream & Messaging Model
**Pub/Sub Event Catalog, Payload Contracts, and UI Synchronization**

---

## 1. Event Architecture Overview

Tarkyaan leverages NOVA's thread-safe, in-process publish/subscribe message backbone (`core.event_bus.EventBus`). All educational actions, state changes, telemetry updates, and diagnostic discoveries are modeled as immutable, structured events.

```
┌──────────────────────────────────────────────┐
│     TARKYAAN EDUCATIONAL SUBSYSTEMS          │
│  (GoalManager, Planner, Evaluator, Session)  │
└──────────────────────┬───────────────────────┘
                       │
                       │ event_bus.publish(TarkyaanEvent.XYZ, **payload)
                       ▼
┌──────────────────────────────────────────────┐
│           NOVA EVENTBUS (Thread-Safe)        │
└──────┬───────────────────────┬───────────────┘
       │                       │
       ▼                       ▼
┌──────────────────────┐ ┌──────────────────────────────────────────────┐
│  Internal Handlers   │ │ UI Event Bridge (`EventBridge`)              │
│  - Memory Sync       │ └──────────────────────┬───────────────────────┘
│  - Replanning Watcher│                        │ Translates to UIEvent
│  - Retention Decayer │                        ▼
└──────────────────────┘ ┌──────────────────────────────────────────────┐
                         │ WebSocket Stream (127.0.0.1:8765)            │
                         └──────────────────────┬───────────────────────┘
                                                │ Broadcasts JSON
                                                ▼
                         ┌──────────────────────────────────────────────┐
                         │ React 18 / Electron Desktop Interface        │
                         │ (Roadmap Cards, Knowledge Graph, Live Avatar)│
                         └──────────────────────────────────────────────┘
```

---

## 2. Complete Educational Event Catalog

Tarkyaan defines 17 first-class educational events extending the internal system stream:

| Event Identifier | Fired When | Typical Subsystem Publisher |
| :--- | :--- | :--- |
| `learning_goal_created` | Learner establishes a new objective | `goals.goal_manager` |
| `learning_goal_updated` | Goal deadline, title, or hour budget shifts | `goals.goal_manager` |
| `learning_plan_created` | Initial personalized curriculum roadmap generated | `planning.learning_planner` |
| `learning_plan_updated` | Roadmap milestone order or task list adjusted | `planning.learning_planner` |
| `plan_replanned` | Dynamic replanner alters syllabus due to evidence | `planning.replanner` |
| `learning_task_started` | Learner begins a scheduled study or practice unit | `planning.task_manager` |
| `learning_task_completed` | Learner finishes practice and verifier succeeds | `planning.task_manager` |
| `learning_task_failed` | Exercise attempts fail or time expires | `planning.task_manager` |
| `learning_session_started`| Dedicated focus study session commences | `learning.session` |
| `learning_session_completed`| Study session concludes with summary | `learning.session` |
| `assessment_started` | Diagnostic probe or milestone quiz initiated | `learning.assessment` |
| `assessment_completed` | Assessment evaluated and scored | `learning.assessment` |
| `knowledge_gap_detected` | Missing prerequisite or misconception uncovered | `learning.gap_analyzer` |
| `progress_updated` | Cumulative mastery delta or pace recalculated | `progress.progress_evaluator`|
| `learner_model_updated` | Bayesian mastery score updated for a concept | `learner.learner_model` |
| `resource_discovered` | Autonomous web research yields verified candidates | `research.research_engine` |
| `resource_selected` | Recommended tutorial or problem picked for task | `research.resource_evaluator`|

---

## 3. Structured Event Payload Contracts

Every event published to `EventBus` carries a standardized typed payload dictionary:

### 3.1 `knowledge_gap_detected`
```python
{
    "event": "knowledge_gap_detected",
    "timestamp": "2026-09-12T23:35:00.124Z",
    "gap_id": "gap_rec_091",
    "concept": "recursion_stack_growth",
    "blocking_topic": "divide_and_conquer",
    "severity": "critical",
    "diagnostic_evidence": "Learner assumed double recursion takes O(n) time and linear calls.",
    "suggested_remedy": "Interactive recursion tree tracing with n=4."
}
```

### 3.2 `plan_replanned`
```python
{
    "event": "plan_replanned",
    "timestamp": "2026-09-12T23:35:05.412Z",
    "plan_id": "plan_dsa_30d",
    "trigger_reason": "critical_prerequisite_gap",
    "topic_inserted": "recursion_fundamentals",
    "tasks_rescheduled_count": 4,
    "deadline_impact_days": 1,
    "summary": "Inserted 45-min recursion visualizer prior to Rotated Binary Search."
}
```

### 3.3 `assessment_completed`
```python
{
    "event": "assessment_completed",
    "timestamp": "2026-09-12T23:35:10.890Z",
    "assessment_id": "eval_bs_002",
    "topic_id": "binary_search_rotated_array",
    "score": 0.85,
    "prior_mastery": 0.62,
    "new_mastery": 0.81,
    "evaluated_tier": "competent",
    "feedback": "Boundary condition handles duplicates correctly. Minor edge case with 1-element arrays identified."
}
```

---

## 4. UI Synchronization & WebSocket Forwarding

NOVA's `EventBridge` (`ui.backend.event_bridge.EventBridge`) subscribes to all `TarkyaanEvent` types and serializes them into typed `UIEvent` objects broadcast across `ws://127.0.0.1:8765`:

```python
# EventBridge Forwarder Integration
class TarkyaanEventBridge:
    def __init__(self, event_bus, nova_ui_server):
        self._bus = event_bus
        self._server = nova_ui_server
        self._register_listeners()

    def _register_listeners(self):
        for event_name in TARKYAAN_EVENTS:
            self._bus.subscribe(event_name, self._forward_to_ui)

    def _forward_to_ui(self, event_name: str, payload: dict):
        ui_event = {
            "type": event_name,
            "avatar_state": self._map_to_avatar_state(event_name),
            "payload": payload,
            "timestamp": payload.get("timestamp")
        }
        self._server.broadcast(ui_event)
```

---

## 5. Telemetry, Retention Metrics & Cognitive Load Monitoring

The event stream powers continuous background telemetry:
1. **Pacing Velocity**: Measures topic completions per week against original deadline requirements.
2. **Cognitive Struggle Index (CSI)**: Calculated from the frequency of `learning_task_failed` and `knowledge_gap_detected` events within a rolling 60-minute window. If CSI exceeds threshold $0.7$, Tarkyaan proactively suggests a brief cognitive rest.
3. **Retention Projections**: Emits warnings when unpracticed topics approach their Ebbinghaus forgetting thresholds, automatically queuing review tasks.
