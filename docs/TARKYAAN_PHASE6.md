# TARKYAAN — PHASE 6
## AUTONOMOUS ADAPTIVE LEARNING + DYNAMIC REPLANNING + SPACED REVIEW + PROGRESS INTELLIGENCE + SECURE CODING SANDBOX

---

## Phase 6 Vision

Phase 6 transforms Tarkyaan from a system that **can teach adaptively** into a system that **continuously adapts the learning journey** based on actual learner evidence.

Tarkyaan Phase 6 is not just a scheduler or a report generator. It is a living, evidence-driven **autonomous learning intelligence** that:

- Monitors every learning session for evidence of stalls, regressions, and overload
- Makes explainable autonomous decisions grounded in learner data
- Replans the curriculum with minimal mutation, preserving completed progress
- Schedules spaced-repetition reviews using the proven SM-2 algorithm
- Generates rich progress reports with velocity, mastery, and resource effectiveness metrics
- Provides a strictly bounded Python execution sandbox for safe learner practice

---

## Architecture

```
LearningSessionEngine (Phase 5)
        │ emits MASTERY_UPDATED, LEARNING_SESSION_ENDED
        ▼
AdaptiveLearningEngine   [tarkyaan/planning/adaptive.py]
  ├── LearningHealthAnalyzer      — synthesizes health from all signals
  ├── MasteryTrajectoryAnalyzer   — velocity, trend, regression detection
  ├── GapEvolutionAnalyzer        — gap age, persistence, recurrence
  └── MisconceptionTrendAnalyzer  — repeated error pattern analysis
        │
        ▼
LearningDecisionEngine   [tarkyaan/planning/decision_engine.py]
        │ → LearningDecision (REPLAN / CONTINUE / SCHEDULE_REVIEW / ...)
        ▼
ReplanningEngine         [tarkyaan/planning/replanning.py]
  ├── ReplanningTriggerEngine     — priority-ordered trigger selection
  ├── CurriculumMutationEngine    — minimal diff + change summary
  └── TaskPriorityRecalculator    — re-weights pending tasks
        │ → calls LearningPlanner.replan() (existing Phase 3)
        │ → persists ReplanningRecord audit trail
        ▼
ReviewScheduler          [tarkyaan/planning/review_scheduler.py]
  ├── SpacedRepetitionScheduler   — SM-2 variant scheduling
  └── RetentionReviewEngine       — REVIEW LearningTask injection

ProgressReportEngine     [tarkyaan/planning/progress_report.py]
  ├── LearningVelocityAnalyzer    — topics/session, completion rate, trend
  └── ResourceEffectivenessAnalyzer — resource quality aggregation

SecureCodingSandbox      [tarkyaan/sandbox/secure_sandbox.py]
  └── CodeSafetyChecker           — AST-level import/builtin allowlist
```

---

## New Files

| File | Purpose |
|------|---------|
| `tarkyaan/planning/adaptive.py` | AdaptiveLearningEngine + all health analyzers |
| `tarkyaan/planning/replanning.py` | ReplanningEngine + trigger/mutation/priority |
| `tarkyaan/planning/review_scheduler.py` | SM-2 spaced repetition + review task injection |
| `tarkyaan/planning/progress_report.py` | Progress report engine + velocity/resource analyzers |
| `tarkyaan/planning/decision_engine.py` | Explainable autonomous decision engine |
| `tarkyaan/sandbox/__init__.py` | Sandbox package |
| `tarkyaan/sandbox/secure_sandbox.py` | AST-checked subprocess sandbox |

---

## Modified Files

| File | Change |
|------|--------|
| `tarkyaan/models/enums.py` | Added: `ReplanningTrigger`, `HealthStatus`, `ReviewUrgency`, `SandboxLanguage`, `SandboxStatus` |
| `tarkyaan/events/event_bus.py` | Added 12 Phase 6 events: `HEALTH_ALERT`, `REPLANNING_TRIGGERED`, `REPLANNING_COMPLETED`, `REVIEW_SCHEDULED`, etc. |
| `tarkyaan/memory/memory_store.py` | Added tables: `replanning_records`, `review_schedules` + indexes |
| `tarkyaan/memory/memory_manager.py` | Added: `save_replanning_record`, `get_replanning_records`, `save_review_schedule`, `get_due_reviews`, `get_all_review_schedules` |
| `tarkyaan/planning/__init__.py` | Exports all Phase 6 planning modules |
| `tarkyaan/capabilities/registry.py` | Added 5 Phase 6 capabilities (adaptive_replanning, spaced_review, progress_report, decision_engine, sandbox.execute_python) |
| `tarkyaan/__main__.py` | Added 6 Phase 6 health checks (subsystems 13-18) |

---

## Core Subsystems

### 1. Adaptive Learning Engine (`AdaptiveLearningEngine`)

The primary Phase 6 orchestrator. Accepts learner evidence (mastery history, gaps, misconceptions, session data) and produces a classified `LearningHealthReport`.

**HealthStatus values**: `HEALTHY`, `STALLED`, `REGRESSING`, `OVERLOADED`, `PLATEAUED`, `AT_RISK`, `RECOVERING`

```python
engine = AdaptiveLearningEngine(memory=memory, event_bus=event_bus)
report = engine.evaluate_learner_health(
    learner_id="learner_1",
    mastery_history=[0.3, 0.4, 0.5],
    topic_id="recursion",
    sessions_since_last_progress=0,
    recent_task_fail_rate=0.2,
)
# report.health_status → HealthStatus.HEALTHY
# report.triggers_detected → []
```

### 2. Mastery Trajectory Analyzer (`MasteryTrajectoryAnalyzer`)

Computes velocity, trend, regression, and plateau from a list of historical mastery scores.

- **Regression**: total delta < -0.05 over the window
- **Plateau**: same MasteryTier for ≥ 4 consecutive sessions
- **Velocity**: mastery delta per session

### 3. Gap Evolution Analyzer (`GapEvolutionAnalyzer`)

Tracks how long knowledge gaps persist. A gap is **persistent** if it has been unresolved for > 7 days. Two or more persistent gaps triggers the `GAP_PERSISTENCE` replan trigger.

### 4. Misconception Trend Analyzer (`MisconceptionTrendAnalyzer`)

Detects recurring misconceptions across sessions. If the same topic appears in multiple misconception records, it flags a `MISCONCEPTION_LOOP` trigger.

### 5. Learning Health Analyzer (`LearningHealthAnalyzer`)

Synthesizes all signals into a classified `LearningHealthReport`:

| Signal | Trigger | Health |
|--------|---------|--------|
| Sessions stalled (≥3 with no progress) | `STALL` | `STALLED` |
| Mastery delta < -5% | `REGRESSION` | `REGRESSING` |
| Task fail rate ≥ 60% | `OVERLOAD` | `OVERLOADED` |
| Mastery at same tier for ≥4 sessions | `PLATEAU` | `PLATEAUED` |
| ≥2 persistent gaps | `GAP_PERSISTENCE` | `AT_RISK` |
| ≥2 recurring misconception topics | `MISCONCEPTION_LOOP` | `AT_RISK` |
| Velocity < 0.5% per session | `VELOCITY_DROP` | `AT_RISK` |

---

### 6. Replanning Engine (`ReplanningEngine`)

Executes the full autonomous replan cycle:

1. Identifies the highest-priority trigger (`ReplanningTriggerEngine`)
2. Computes a human-readable change summary (`CurriculumMutationEngine`)
3. Delegates to existing `LearningPlanner.replan()` → new plan version
4. Re-prioritizes pending tasks (`TaskPriorityRecalculator`)
5. Persists an auditable `ReplanningRecord` to SQLite
6. Publishes `REPLANNING_TRIGGERED` + `REPLANNING_COMPLETED` events

**Minimal mutation rule**: Completed tasks are always preserved. Only `PENDING` tasks are re-ordered or replaced.

```python
engine = ReplanningEngine(memory=memory, planner=planner)
new_plan, record = engine.replan(
    plan_id="plan_abc",
    triggers=[ReplanningTrigger.STALL],
    health_status="stalled",
    signals=["No progress in 4 sessions"],
)
# new_plan.version == old_plan.version + 1
# record.trigger_type == ReplanningTrigger.STALL
```

**Trigger priority order** (highest → lowest):
`REGRESSION > OVERLOAD > STALL > GAP_PERSISTENCE > MISCONCEPTION_LOOP > PLATEAU > VELOCITY_DROP > MILESTONE_MISSED > PREREQUISITE_FAILURE`

---

### 7. Spaced Repetition Scheduler (`SpacedRepetitionScheduler`)

SM-2 variant adapted for mastery-based evidence:

```
quality = mastery_score × 5  (maps [0,1] → [0,5])
EF_new = EF + (0.1 - (5-q) × (0.08 + (5-q) × 0.02))
EF_min = 1.3

interval[1] = 1 day
interval[2] = 6 days
interval[n] = interval[n-1] × EF   (n ≥ 3)

If quality < 3.0 → reset (interval=1, repetitions=0)
```

**ReviewUrgency** classification:
- `CRITICAL`: overdue by > 3× expected interval
- `HIGH`: overdue by > 1.5× expected interval
- `NORMAL`: within expected interval
- `LOW`: not yet due

### 8. Review Scheduler (`ReviewScheduler`)

Top-level facade combining `SpacedRepetitionScheduler` + `RetentionReviewEngine`:

```python
scheduler = ReviewScheduler(memory=memory)
interval = scheduler.schedule_review(
    learner_id="l1", topic_id="closures", mastery_score=0.72
)
# Persists schedule; returns ReviewInterval with next_review_at

due_tasks = scheduler.get_due_review_tasks(learner_id="l1", plan_id="plan_1")
# Returns List[LearningTask] of type REVIEW for all overdue topics
```

---

### 9. Progress Report Engine (`ProgressReportEngine`)

Generates a `LearningProgressReport` pulling all data from `TarkyaanMemoryManager`:

```python
engine = ProgressReportEngine(memory=memory)
report = engine.generate_report("learner_1", health_status=HealthStatus.HEALTHY)
# report.headline → "Learning is on track. 5/10 topics at competent+ level (80% completion rate)."
# report.recommendations → [...]
# report.velocity.topics_per_session → 2.3
# report.mastery_summary.mastered_count → 3
```

**Report includes**:
- Mastery distribution (MASTERED / COMPETENT / PRACTICING / INTRODUCED / UNEXPLORED)
- Top 3 strong and weak topics
- Session velocity (topics/session, trend: improving/stable/declining)
- Task completion rate
- Active + resolved gap counts
- Active plan ID and version
- Resource effectiveness (high/low impact resources)
- Human-readable headline and actionable recommendations

---

### 10. Learning Decision Engine (`LearningDecisionEngine`)

Explainable autonomous decision engine with priority-chain logic:

```python
decision = LearningDecisionEngine.decide(
    learner_id="l1",
    health_status=HealthStatus.REGRESSING,
    triggers=[ReplanningTrigger.REGRESSION],
    signals=["Mastery dropped by 8% over 3 sessions"],
    plan_id="plan_abc",
)
# decision.decision_type → DecisionType.REPLAN
# decision.confidence → DecisionConfidence.MEDIUM
# decision.rationale → "Mastery regression detected (medium confidence)..."
```

**Decision types**: `CONTINUE`, `REPLAN`, `SCHEDULE_REVIEW`, `CHANGE_STRATEGY`, `ADJUST_DIFFICULTY`, `SUGGEST_BREAK`, `FLAG_FOR_ATTENTION`, `MILESTONE_REVIEW`

**Confidence levels** based on signal count:
- `HIGH`: ≥ 2 signals
- `MEDIUM`: 1 signal
- `LOW`: 0 signals

---

### 11. Secure Coding Sandbox (`SecureCodingSandbox`)

Strictly bounded Python execution for learner practice:

```python
sandbox = SecureCodingSandbox(SandboxConfig(timeout_seconds=5))
result = sandbox.execute("import math\nprint(math.sqrt(25))")
# result.status → SandboxStatus.SUCCESS
# result.stdout → "5.0\n"

result = sandbox.execute("import os\nos.system('rm -rf /')")
# result.status → SandboxStatus.BLOCKED
# result.blocked_reason → "Import 'os' is not permitted in the sandbox."
```

**Security layers** (defense in depth):
1. **AST analysis** — `CodeSafetyChecker` walks the AST before execution, blocking forbidden imports and dangerous builtins
2. **Subprocess isolation** — code runs in a fresh Python subprocess with no access to Tarkyaan internals
3. **Module poisoning** — `sys.modules` entries for `os`, `subprocess`, `socket`, `requests`, `urllib`, `http`, `shutil`, `pathlib` are set to `None`
4. **Builtin removal** — `exec`, `eval`, `compile`, `open`, `input`, `breakpoint` removed from builtins
5. **Timeout enforcement** — hard subprocess timeout (default 5s, max 10s)
6. **Import allowlist** — only approved stdlib modules permitted: `math`, `random`, `itertools`, `functools`, `collections`, `string`, `re`, `json`, `copy`, `typing`, `dataclasses`, `abc`, `enum`, `heapq`, `bisect`, `operator`, `decimal`, `fractions`, `statistics`, `time`, `datetime`, `pprint`, `textwrap`, `struct`, `array`

---

## Database Schema (Phase 6 Additions)

### `replanning_records` (Phase 6 Audit Trail)
```sql
CREATE TABLE IF NOT EXISTS replanning_records (
    record_id     TEXT PRIMARY KEY,
    learner_id    TEXT NOT NULL REFERENCES learners(learner_id) ON DELETE CASCADE,
    old_plan_id   TEXT NOT NULL,
    new_plan_id   TEXT NOT NULL,
    trigger_type  TEXT NOT NULL,
    trigger_evidence TEXT NOT NULL DEFAULT '{}',
    rationale     TEXT NOT NULL DEFAULT '',
    changes_summary TEXT NOT NULL DEFAULT '',
    health_status TEXT NOT NULL DEFAULT 'healthy',
    created_at    TEXT NOT NULL
);
```

### `review_schedules` (Phase 6 Spaced Repetition)
```sql
CREATE TABLE IF NOT EXISTS review_schedules (
    schedule_id      TEXT PRIMARY KEY,
    learner_id       TEXT NOT NULL REFERENCES learners(learner_id) ON DELETE CASCADE,
    topic_id         TEXT NOT NULL,
    next_review_at   TEXT NOT NULL,
    interval_days    REAL NOT NULL DEFAULT 1.0,
    ease_factor      REAL NOT NULL DEFAULT 2.5,
    repetitions      INTEGER NOT NULL DEFAULT 0,
    urgency          TEXT NOT NULL DEFAULT 'normal',
    last_reviewed_at TEXT,
    last_mastery_score REAL NOT NULL DEFAULT 0.0,
    created_at       TEXT NOT NULL,
    updated_at       TEXT NOT NULL,
    UNIQUE(learner_id, topic_id)
);
```

---

## Phase 6 Events

| Event | Description |
|-------|-------------|
| `HEALTH_ALERT` | Learner health changed to non-healthy status |
| `REPLANNING_TRIGGERED` | Evidence threshold crossed; replan started |
| `REPLANNING_COMPLETED` | New plan version activated |
| `REVIEW_SCHEDULED` | Spaced review task injected |
| `REVIEW_COMPLETED` | Review session completed |
| `VELOCITY_DROPPED` | Learning velocity dropped below threshold |
| `MILESTONE_MISSED` | Milestone target date passed |
| `REGRESSION_DETECTED` | Mastery score significantly decreased |
| `PROGRESS_REPORT_GENERATED` | Progress report ready |
| `SANDBOX_EXECUTION_STARTED` | Code sandbox run started |
| `SANDBOX_EXECUTION_COMPLETED` | Code run finished |
| `SANDBOX_EXECUTION_BLOCKED` | Code run blocked by safety check |

---

## Phase 6 Capabilities (23 total)

| Capability | Status |
|-----------|--------|
| `learning.adaptive_replanning` | AVAILABLE |
| `learning.spaced_review` | AVAILABLE |
| `learning.progress_report` | AVAILABLE |
| `learning.decision_engine` | AVAILABLE |
| `sandbox.execute_python` | AVAILABLE |

---

## Test Coverage

| Test File | Tests Added | Coverage |
|-----------|-------------|---------|
| `test_adaptive_learning.py` | 20 | AdaptiveLearningEngine, all analyzers |
| `test_review_scheduler.py` | 20 | SpacedRepetitionScheduler, RetentionReviewEngine, ReviewScheduler |
| `test_progress_report.py` | 19 | ProgressReportEngine, VelocityAnalyzer, ResourceAnalyzer |
| `test_secure_sandbox.py` | 22 | CodeSafetyChecker, SecureCodingSandbox execution |
| `test_decision_engine.py` | 20 | LearningDecisionEngine, all decision types |

**Total: 299 tests passing (184 Phase 1-5 regression + 115 Phase 6 new)**

---

## Verification

```bash
# Run full test suite
/path/to/.venv/bin/python -m pytest tests/ -q
# → 299 passed in 4.56s

# Phase 1-6 health check
/path/to/.venv/bin/python -m tarkyaan --status
# → All 18 subsystems [+]
```

---

## Design Principles

1. **Zero duplication**: `ReplanningEngine` calls existing `LearningPlanner.replan()` — no new plan builder
2. **Minimal mutation**: Only `PENDING` tasks are re-ordered; `COMPLETED` tasks always preserved
3. **Audit-first**: Every autonomous decision → `ReplanningRecord` in SQLite
4. **Explainability**: Every `LearningDecision` carries its evidence signals, trigger list, rationale, and confidence level
5. **Defense in depth**: Sandbox security has 5 independent layers — AST, subprocess, module poisoning, builtin removal, timeout
6. **Event-driven**: All Phase 6 actions publish to `EventBus` for observability and future extensions
7. **Conservative**: Decision engine prefers `CONTINUE` over `REPLAN` whenever evidence is weak (LOW confidence)

---

*Phase 6 complete. Tarkyaan is now a living autonomous learning intelligence.*
