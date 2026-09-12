# TARKYAAN — Engineering Roadmap & Milestone Blueprint
**Phase-by-Phase Development Plan, Hackathon Vision, and Validation Metrics**

---

## 1. Development Lifecycle Overview

The Tarkyaan engineering journey is divided into eight sequential, disciplined phases. Progression strictly follows an audit $\to$ contract $\to$ implementation $\to$ verification gate.

```
PHASE 0: Understand + Audit + Architect (Current Phase: COMPLETED)
   │
   ▼
PHASE 1: Core Learner Model & Memory Integration
   │
   ▼
PHASE 2: Diagnostic Assessment & Knowledge Gap Engine
   │
   ▼
PHASE 3: Autonomous Learning Planner & NOVA Capability Dispatch
   │
   ▼
PHASE 4: Autonomous Educational Research & Resource Evaluator
   │
   ▼
PHASE 5: Adaptive Teaching, Socratic Practice & Dynamic Replanner
   │
   ▼
PHASE 6: Learning-First Desktop Cockpit & Voice Integration
   │
   ▼
PHASE 7: Comprehensive Verification & Grand Hackathon Showcase
```

---

## 2. Phase-by-Phase Technical Breakdown

### Phase 0: Understand + Audit + Architect (CURRENT — COMPLETED)
- Deep audit of all 32 NOVA documentation files and real codebase (`NOVA_SETUP`).
- Verification of baseline tests (881 tests passed, 100% green).
- Architectural blueprint, ownership classification, data models, event catalog, and personality definitions.
- Git repository initialization and secret safety configuration.

### Phase 1: Core Learner Model & Memory Integration
- Implement `tarkyaan/learner/` models using Pydantic v2.
- Build `LearningMemoryAdapter` binding to NOVA `MemoryManager` (`MemoryCategory.EDUCATION`, `MemoryCategory.GOALS`).
- Implement Bayesian mastery calculation ($0.0 \le M \le 1.0$) and temporal Ebbinghaus retention decay.
- **Unit Tests**: Persistence round-trips, atomic JSON writing, corrupt store quarantine resilience.

### Phase 2: Diagnostic Assessment & Knowledge Gap Engine
- Build `tarkyaan/learning/gap_analyzer.py` with directed prerequisite graph traversal.
- Implement Socratic diagnostic probe generator that formulates non-trivial verification questions.
- Implement misconception classifier (Conceptual vs Algorithmic vs Syntax vs Fatigue).
- **Unit Tests**: Prerequisite deficit detection, root-cause backtracking tests.

### Phase 3: Autonomous Learning Planner & NOVA Capability Dispatch
- Implement `tarkyaan/planning/learning_planner.py` decomposing high-level goals into milestone roadmaps.
- Register Tarkyaan learning tools (`tarkyaan.scaffold_practice`, `tarkyaan.launch_ide_problem`) into NOVA's `CapabilityRegistry`.
- Wire `TaskExecutor` to run learning plans step-by-step with postcondition verifiers.
- **Unit Tests**: Plan decomposition, capability dispatch, timeout and cancellation handling.

### Phase 4: Autonomous Research & Resource Evaluator
- Integrate with NOVA `browser.planner.BrowserTaskPlanner` and `WebpageExtractor`.
- Implement `ResourceEvaluator` calculating composite quality scores (0–100) across clarity, credibility, and level alignment.
- Implement markdown study card generator from web articles.
- **Unit Tests**: Scraping resilience, score normalization, link validation.

### Phase 5: Adaptive Teaching, Practice & Dynamic Replanner
- Implement interactive Socratic teaching dialogue loop in `tarkyaan/learning/teaching.py`.
- Integrate screen perception (`NovaEyesManager`) to inspect active code in VS Code.
- Implement `DynamicReplanner` hooks that intercept learner struggles and rewrite future task chains.
- **Unit Tests**: Replanning triggers (velocity drop, gap detected, deadline shift).

### Phase 6: Learning-First UI & Voice Integration
- Build React 18 learning screens (`RoadmapScreen`, `TasksScreen`, `GapsScreen`, `FocusScreen`) in `ui/desktop/`.
- Extend WebSocket gateway in `ui/backend/` to stream `TarkyaanEvent` payloads.
- Connect Edge-TTS with `hi-IN-SwaraNeural` voice for conversational companion guidance.
- Integrate dynamic avatar orb states (Teaching, Evaluating, Gap Detected).
- **Verification**: End-to-end WebSocket telemetry, live voice dialogue tests.

### Phase 7: Comprehensive System Verification & Hackathon Showcase
- Run unified test suite covering both legacy NOVA (881 tests) and new Tarkyaan test modules.
- End-to-end rehearsal of the Grand Hackathon Showcase scenario.
- Final build packaging and documentation freeze.

---

## 3. The Grand Hackathon Demonstration Vision

The live demonstration will showcase what differentiates Tarkyaan from generic chatbots:

```
[LIVE DEMO TIMELINE: 5 MINUTES]

00:00 - 00:45 | THE GOAL
User speaks: "Tarkyaan, I have 30 days to prepare DSA for campus placements. 
I know basic C++ syntax, but recursion and dynamic programming terrify me. 
I can commit 2 hours a day."

00:45 - 01:30 | DIAGNOSTIC DISCOVERY (NOT A GENERIC ROADMAP)
Tarkyaan does not just dump a syllabus. She speaks naturally via SwaraNeural:
"Let's pinpoint exactly where recursion breaks down for you first."
She asks a targeted question on call stack frames. Learner gives an intuitive 
but incorrect answer. Tarkyaan highlights the exact misconception without judgment.

01:30 - 02:45 | AUTONOMOUS PLANNING & SYSTEM EXECUTION (LEVEL 4)
Tarkyaan synthesizes an adaptive 30-day roadmap prioritizing high-yield patterns.
She states: "I'm setting up today's workspace and opening your first challenge."
NOVA's FileSystemManager scaffolds a practice folder on Desktop with test harnesses.
NOVA's AppLauncher opens VS Code directly to the problem file.
Chrome opens to a verified visual recursion tree animation.

02:45 - 04:00 | REAL-TIME PERCEPTION & SOCRATIC HINTING
Learner writes an off-by-one error in VS Code.
Learner asks: "Why is this infinite looping?"
Tarkyaan inspects the active VS Code window via NovaEyes Quartz OCR:
"Look at line 14. Your base condition tests n == 0, but your recursive call 
subtracts 2. What happens on odd numbers?"
Learner fixes the bug; tests pass! Emerald avatar flashes.

04:00 - 05:00 | DYNAMIC REPLANNING & LONG-TERM CONTINUITY
Tarkyaan logs the milestone in MemoryManager.
Because the learner mastered recursion mechanics faster than projected, 
Tarkyaan automatically adapts tomorrow's roadmap:
"You grasped the call stack in 20 minutes. I've shifted memoization up by 
two days, freeing up an extra weekend for hard Graph problems."
The learner sees their living knowledge graph update in real-time.
```

---

## 4. Key Success Metrics & Verification Criteria

1. **Test Suite Integrity**: 100% green pass rate on all tests; zero regressions in NOVA's 881-test baseline.
2. **Pedagogical Precision**: 100% of diagnosed gaps link to concrete prerequisite DAG edges; zero ungrounded advice.
3. **Execution Safety**: Zero writes outside sandboxed workspace; 100% confirmation gate enforcement on destructive calls.
4. **Latency Budget**: Sub-10ms intent parsing on canonical commands; sub-1.5s voice response time using fast-mode routing.
5. **Zero Secret Leaks**: Strict git and log masking of all API tokens.
