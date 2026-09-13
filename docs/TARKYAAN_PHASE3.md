# TARKYAAN — PHASE 3 SPECIFICATION & TECHNICAL ARCHITECTURE
## AUTONOMOUS LEARNING PLANNER & PERSONALIZED ROADMAP ENGINE

**Tarkyaan (तर्कयान)** — *Your Autonomous Learning Companion*  
**Repository**: `https://github.com/nikhil-singh91/Anant_tark_Tarkyaan.git`  
**Phase**: Phase 3 Completed

---

## 1. Phase 3 Objective

Phase 2 established Tarkyaan's cognitive diagnostic capability:
- What the learner knows vs what they do not know
- Epistemic evidence distinguishing verified observations (`FACT`) from evaluated deductions (`INFERENCE`)
- Prerequisite dependencies represented as a strict DAG (`PrerequisiteDAG`)
- Diagnosed root causes and classified misconceptions (`CONCEPTUAL`, `ALGORITHMIC_LOGIC`, `SYNTAX_IDIOM`, `COGNITIVE_FATIGUE`)

The objective of **Phase 3** is to transform that diagnostic intelligence into a **reasoned, prerequisite-aware, personalized, and explainable learning plan**.

Tarkyaan answers:
- *"What should this learner learn next?"*
- *"Why should they learn it now?"*
- *"What order should concepts be learned in?"*
- *"Which gaps are blocking downstream topics?"*
- *"How much study workload is required, and does it fit the learner's timeline?"*
- *"What does verifiable success look like?"*
- *"How does the roadmap adapt as new diagnostic evidence emerges?"*

---

## 2. Planning Brain Architecture

```
                       LEARNING GOAL & LEARNER PROFILE
                                      │
                                      ▼
                        GOAL DECOMPOSITION ENGINE
                 (Multi-domain candidate concept discovery)
                                      │
                                      ▼
                        PRIORITY RANKING ENGINE
                 (Multi-factor deterministic gap scoring)
                                      │
                                      ▼
                        PEDAGOGICAL STRATEGY ENGINE
                   (Diagnostic-driven strategy selection)
                                      │
                                      ▼
                        PREREQUISITE SCHEDULER
                 (DAG topological sort & mastery categorization)
                                      │
                                      ▼
                           PLAN BUILDER PIPELINE
             ┌────────────────────────┼────────────────────────┐
             │                        │                        │
             ▼                        ▼                        ▼
       STUDY PHASES             LEARNING TASKS            MILESTONES
   (Coherent Blocks)         (Actionable Units)      (Measurable Checkpoints)
             │                        │                        │
             └────────────────────────┼────────────────────────┘
                                      │
                                      ▼
                               WORKLOAD ENGINE
                 (Capacity pacing & deadline overload warning)
                                      │
                                      ▼
                               PLAN VALIDATOR
               (Deterministic DAG integrity & constraint checks)
                                      │
                                      ▼
                              PLAN EXPLANATION
                (Structured rationale: "Why this plan looks so")
                                      │
                                      ▼
                           TARKYAAN MEMORY STORE
                      (SQLite normalized persistence)
```

---

## 3. The Planner Pipeline

The end-to-end plan generation pipeline is orchestrated by `PlanBuilder` (`tarkyaan/planning/plan_builder.py`) and accessed via the `LearningPlanner` service facade (`tarkyaan/planning/planner.py`):

1. **Load Learner State**: Fetches learner profile, target learning goal, existing topic mastery probabilities, epistemic uncertainties, active knowledge gaps, and observed misconceptions from Tarkyaan's independent SQLite memory.
2. **Decompose Goal**: `GoalDecomposer` analyzes goal domain, target outcome, and candidate concepts.
3. **Prioritize Topics**: `PriorityEngine` calculates explainable numerical priority scores for all candidate topics.
4. **Select Strategy**: `StrategyEngine` selects from `PREREQUISITE_FIRST`, `GAP_FIRST`, `FOUNDATION_FIRST`, `PRACTICE_HEAVY`, `EXAM_FOCUSED`, or `BALANCED`.
5. **Schedule Dependencies**: `DependencyScheduler` uses `PrerequisiteDAG` to topologically sort concepts, categorizing each as `mastered`, `weak`, `missing`, or `uncertain`.
6. **Partition into Phases**: Groups scheduled concepts into coherent pedagogical blocks:
   - *Phase 1: Foundational Prerequisites*
   - *Phase 2: Core Concept Mastery*
   - *Phase 3: Applied Problem Solving & Synthesis*
7. **Generate Tasks**: Synthesizes atomic, actionable `LearningTask` objects tailored to the concept's diagnosed need (`UNDERSTAND`, `PRACTICE`, `REVIEW`, `APPLY`, `ASSESSMENT`).
8. **Estimate Workload**: `WorkloadEngine` calculates total minutes, daily pacing, and capacity overload alerts.
9. **Synthesize Milestones**: `MilestoneEngine` generates measurable checkpoints anchored to phase task completions.
10. **Explain Rationale**: `PlanExplanation` synthesizes structured reasoning for why every topic was prioritized, scheduled, or deferred.
11. **Validate Deterministically**: `PlanValidator` validates DAG ordering, uniqueness of IDs, workload consistency, and referential integrity.
12. **Persist and Version**: Saves normalized plan into Tarkyaan memory and archives version 1 in `plan_versions`.

---

## 4. Multi-Domain Goal Decomposition (`GoalDecomposer`)

Located at `tarkyaan/planning/goal_decomposer.py`.

The decomposer is domain-agnostic and explicitly decoupled from DSA:
- Supports **Computer Science, Mathematics, Physics, Machine Learning, Programming, Languages, and Professional Skills**.
- If a `PrerequisiteDAG` is supplied, it extracts graph concepts matching the goal and traverses transitive ancestors to unearth hidden prerequisite requirements.
- Incorporates explicit milestones defined in `LearningGoal.milestones`.
- Incorporates active unmastered gaps from `KnowledgeGap` records.

---

## 5. Explainable Priority Model (`PriorityEngine`)

Located at `tarkyaan/planning/priority_engine.py`.

Concepts and knowledge gaps are scored using a deterministic, transparent formula:

$$\text{Priority} = w_{\text{goal}} \cdot R_{\text{goal}} + w_{\text{prereq}} \cdot I_{\text{prereq}} + w_{\text{sev}} \cdot S_{\text{sev}} + w_{\text{weak}} \cdot W_{\text{weak}} + w_{\text{unc}} \cdot \sigma + w_{\text{dep}} \cdot D_{\text{dep}}$$

| Factor | Weight | Pedagogical Meaning |
|---|---|---|
| **Goal Relevance ($R_{\text{goal}}$)** | 25.0 | Direct alignment with target outcome vs peripheral background |
| **Prerequisite Impact ($I_{\text{prereq}}$)** | 25.0 | Whether this concept directly unblocks downstream target topics |
| **Gap Severity ($S_{\text{sev}}$)** | 20.0 | Critical (1.0), High (0.8), Medium (0.5), Low (0.2) |
| **Learner Weakness ($W_{\text{weak}}$)** | 15.0 | $1.0 - \text{MasteryScore}$ (higher score for lower mastery) |
| **Uncertainty ($\sigma$)** | 10.0 | Epistemic uncertainty $U(c)$ requiring diagnostic verification |
| **Downstream Dependents ($D_{\text{dep}}$)** | 5.0 | Number of immediate and transitive children in `PrerequisiteDAG` |

Every priority score produces a structured human explanation (e.g. *"'recursion' is prioritized (score: 87.5) because it has a critical-severity gap, blocks 3 downstream concepts, and is directly required for your goal."*).

---

## 6. Pedagogical Strategy Engine (`StrategyEngine`)

Located at `tarkyaan/planning/strategy_engine.py`.

Adapts curriculum strategy according to the learner's diagnostic profile:
- **`EXAM_FOCUSED`**: Activated when an explicit deadline is $\le 14$ days away; focuses strictly on high-yield, exam-critical topics and rapid practice.
- **`PREREQUISITE_FIRST`**: Activated when multiple foundational prerequisites are below competence ($< 0.60$); stabilizes root axioms before teaching complex composite structures.
- **`GAP_FIRST`**: Activated when foundational prerequisites are sound but target concepts exhibit high-severity gaps; attacks target deficits immediately.
- **`FOUNDATION_FIRST`**: Activated when baseline domain mastery is introductory ($< 0.25$); begins with first-principles conceptual exposure.
- **`PRACTICE_HEAVY`**: Activated when conceptual tiers are already competent ($\ge 0.65$); shifts weight to algorithmic implementation, edge-case debugging, and timed problem solving.
- **`BALANCED`**: Standard balanced progression blending understanding, structured recall, and incremental problem solving.

---

## 7. Prerequisite Scheduling & Mastery Categorization (`DependencyScheduler`)

Located at `tarkyaan/planning/dependency_scheduler.py`.

The scheduler respects `PrerequisiteDAG` as the ground-truth authority:
- Uses Kahn's topological sort to guarantee prerequisite ordering.
- Classifies each node into an epistemic status:
  - **`mastered`** ($\mu \ge 0.75, \sigma \le 0.35$): Sets `skip_instruction = True`. Emits only a lightweight synthesis review task ($\le 25\text{ min}$).
  - **`weak`** ($0.40 \le \mu < 0.75$): Emits deliberate `PRACTICE` and `APPLY` tasks.
  - **`missing`** ($\mu < 0.35$): Emits foundational `UNDERSTAND` and `PRACTICE` tasks.
  - **`uncertain`** ($\sigma \ge 0.70$ and unexplored): Emits diagnostic `ASSESSMENT` and `LEARN` tasks.

---

## 8. Workload Engine & Overload Detection (`WorkloadEngine`)

Located at `tarkyaan/planning/workload_engine.py`.

- Calculates total minutes, total hours, daily pacing, and estimated study sessions.
- **Overload Detection**: When a learner specifies a target deadline, available study minutes are computed ($D \times \text{daily\_budget}$). If required study time exceeds available capacity by $> 15\%$, `WorkloadEngine` flags `is_overloaded = True` and writes an explicit capacity warning into `overload_reason`.

---

## 9. Actionable Tasks, Phases, and Milestones

- **`LearningTask`** (`tarkyaan/models/planning.py`): Represents atomic study units ($25 - 60$ minutes). Includes difficulty ($1 - 5$), pedagogical `TaskType` (`UNDERSTAND`, `PRACTICE`, `REVIEW`, `APPLY`, `ASSESSMENT`), expected evidence, completion criteria, and a clean extension point for future Phase 4 resources (`resource_ids: List[str]`).
- **`StudyPhase`**: Groups related tasks into coherent milestone phases with explicit prerequisite phase dependencies.
- **`Milestone`** (`MilestoneEngine`): Measurable checkpoints requiring completed task IDs and verified concept mastery benchmarks.

---

## 10. Deterministic Validation (`PlanValidator`)

Located at `tarkyaan/planning/plan_validator.py`.

Before any plan is saved or activated, it must pass deterministic validation:
- Validates non-empty learner and goal references.
- Asserts uniqueness of all task IDs, phase IDs, and milestone IDs.
- Validates phase and milestone task references.
- Validates prerequisite task ordering: no task may be scheduled before its prerequisite tasks.
- Validates DAG consistency: no concept may be scheduled before its upstream prerequisites.
- Verifies non-zero workload math.

---

## 11. Plan Versioning & Replanning Lifecycle

Located at `tarkyaan/planning/planner.py`.

Plans are fully versioned:
1. `plan_goal(...)`: Synthesizes initial plan (`version = 1`).
2. `replan(plan_id, revision_reason, changes_summary)`:
   - Marks previous plan version as `SUPERSEDED`.
   - Archives immutable snapshot in `plan_versions` SQLite table.
   - Synthesizes incremented plan (`version = v + 1`, `parent_plan_id = old_id`).
   - Saves new active plan and logs audit record.
3. `get_plan_version_history(plan_id)`: Returns full historical audit trail.

---

## 12. Tarkyaan Memory Integration

- **Zero NOVA Memory**: Uses only Tarkyaan's independent SQLite store (`TarkyaanMemoryStore` / `TarkyaanMemoryManager`).
- **Normalized Tables**:
  - `learning_plans`: Header metadata, strategy, status, workload, and JSON explanation.
  - `study_phases`: Normalized phase blocks with ordering and completion status.
  - `plan_milestones`: Checkpoints with required task and concept lists.
  - `learning_tasks`: Atomic task records with prerequisite task references.
  - `plan_versions`: Immutable audit snapshots.
- **Strict Learner Isolation**: All plan, phase, task, and version queries are strictly scoped by `learner_id`.

---

## 13. Test Verification Suite

All 93 unit and integration tests pass with 100% success rate (`pytest tests/ -v`):
- `tests/test_goal_decomposer.py`: 4 tests (DSA decomposition, ML multi-domain breakdown, DAG-aware concept discovery, milestone token extraction).
- `tests/test_priority_engine.py`: 3 tests (severity weighting, prerequisite centrality, transparent human rationale).
- `tests/test_strategy_engine.py`: 4 tests (exam-focused deadline urgency, prerequisite-first root blocking, gap-first prioritization, practice-heavy application).
- `tests/test_dependency_scheduler.py`: 3 tests (topological ordering guarantee, mastered skipping, weak practice reinforcement).
- `tests/test_workload_engine.py`: 3 tests (duration summation, overload warning on deadline crunch, realistic pacing).
- `tests/test_milestone_engine.py`: 1 test (phase anchoring and capstone synthesis).
- `tests/test_plan_validator.py`: 4 tests (valid plan pass, duplicate ID rejection, prerequisite ordering violation caught, DAG inversion detected).
- `tests/test_plan_builder.py`: 2 tests (end-to-end plan synthesis, review task sizing on mastered concepts).
- `tests/test_learning_planner.py`: 3 tests (plan lifecycle and persistence, plan versioning v1 -> v2, strict learner isolation).
- Existing Phase 1 & 2 regression tests: 66 tests (prerequisite DAG, question generator, answer evaluator, gap analyzer, misconception detector, diagnostic engine, learner model, retention engine, memory manager, memory retriever, memory store, models).

---

## 14. Known Limitations & Scope Boundaries

1. **No Autonomous Web Resource Scraping**: Phase 3 provides clean resource attachment slots (`resource_ids: List[str]`), but automated web research and resource evaluation belong to Phase 4.
2. **No Autonomous Execution Loops**: Phase 3 generates and validates the roadmap brain; autonomous desktop/voice teaching execution belongs to subsequent phases.
3. **No Dynamic Multi-Agent Replanners**: Live session-by-session replanning loops will be expanded in Phase 6.

---

## 15. Next Phase: Phase 4

**PHASE 4 — AUTONOMOUS RESEARCH & RESOURCE CURATION ENGINE**:
- Educational resource discovery and scraping.
- Multi-dimensional content evaluation (`relevance`, `clarity`, `credibility`, `level_alignment`, `time_efficiency`).
- Attaching curated learning resources directly to Phase 3 `LearningTask` units.
