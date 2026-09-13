# TARKYAAN — PHASE 2 SPECIFICATION & TECHNICAL ARCHITECTURE
## DIAGNOSTIC ASSESSMENT & KNOWLEDGE GAP ENGINE

**Tarkyaan (तर्कयान)** — *Your Autonomous Learning Companion*  
**Repository**: `https://github.com/nikhil-singh91/Anant_tark_Tarkyaan.git`  
**Phase**: Phase 2 Completed

---

## 1. Phase 2 Purpose

The core purpose of Phase 2 is to equip Tarkyaan with deep cognitive diagnostic intelligence capable of answering two fundamental questions:
1. *"What does this learner ACTUALLY know?"*
2. *"What exactly is preventing this learner from progressing?"*

Unlike generic quiz platforms that evaluate superficial multiple-choice questions and assign aggregate percentages, Tarkyaan operates as an epistemic diagnostic engine. It uses directed prerequisite graphs, cognitive depth tiers, Socratic probing, rubric-anchored answer evaluations, backward-chaining root-cause analysis, and calibrated misconception detectors to discover the deep conceptual impediments hindering learner mastery.

---

## 2. Diagnostic Architecture

The Phase 2 diagnostic loop implements a closed-loop epistemic cycle:

```
                  USER LEARNING GOAL
                          │
                          ▼
              RELEVANT CONCEPT DISCOVERY
                          │
                          ▼
            PREREQUISITE GRAPH (PrerequisiteDAG)
                          │
                          ▼
           CURRENT LEARNER STATE (Tarkyaan Memory)
                          │
                          ▼
           UNCERTAINTY / WEAKNESS ANALYSIS
                          │
                          ▼
               SOCRATIC PROBE SELECTION
              (QuestionGenerator / Tier targeting)
                          │
                          ▼
                DIAGNOSTIC QUESTION
                          │
                          ▼
                    LEARNER ANSWER
                          │
                          ▼
            EVIDENCE SEPARATION & EVALUATION
       (Observed Evidence [FACT] vs Inferred Evaluation [INFERENCE])
                          │
                          ▼
           DETERMINISTIC MASTERY & UNCERTAINTY UPDATE
                 (MasteryEngine Bayesian Updates)
                          │
                          ▼
             KNOWLEDGE GAP ENGINE (GapAnalyzer)
                          │
                          ▼
           MISCONCEPTION DETECTION & ROOT-CAUSE TRACE
                  (MisconceptionDetector)
                          │
                          ▼
            DIAGNOSTIC REPORT & TARKYAAN MEMORY
```

---

## 3. Prerequisite Knowledge Graph (`PrerequisiteDAG`)

Located at `tarkyaan/knowledge/prerequisite_graph.py`.

### Architectural Principles:
- **Strict Directed Acyclic Graph (DAG)**: All prerequisite connections are directional (`A -> B` where $A$ is prerequisite to $B$).
- **Zero Cycle Tolerance**: Every edge addition validates through Depth-First Search (`_causes_cycle`). Any direct, multi-hop, or self-referential loop raises `CyclicDependencyError`.
- **Multi-Domain Abstraction**: Built on domain-agnostic identifiers (`concept_id`, `subject_id`), decoupling the graph engine from any specific subject (DSA, Machine Learning, Physics, Mathematics).

### Key Capabilities:
- `add_concept(concept_id, name, subject_id, description)`
- `add_prerequisite(concept_id, prerequisite_id)`
- `get_prerequisites(concept_id)` / `get_dependents(concept_id)`
- `get_ancestors(concept_id)` / `get_descendants(concept_id)`
- `topological_sort()`: Validated topological ordering of curriculum topics.
- `get_roots()` / `get_leaves()`: Automatic discovery of foundational axioms vs terminal capstones.
- `get_depth(concept_id)`: Maximum distance from primitive roots.
- `find_blocking_prerequisites(concept_id, learner_mastery_map)`: Identifies unmastered upstream concepts blocking progress.

---

## 4. Diagnostic Session Lifecycle

Implemented via `DiagnosticSession` (`tarkyaan/models/diagnostic.py`) and orchestrated by `DiagnosticEngine` (`tarkyaan/assessment/diagnostic_engine.py`):

- **Statuses**: `CREATED` -> `IN_PROGRESS` -> `PAUSED` -> `COMPLETED` / `CANCELLED`.
- **Session State**: Maintains `target_concepts`, history of asked `questions`, submitted `responses`, structured `evidence_collected`, detected `discovered_gaps`, identified `discovered_misconceptions`, and `mastery_updates`.
- **Resumability**: Full session state and timestamps (`started_at`, `completed_at`) are maintained and resumable.

---

## 5. Question Generation (`QuestionGenerator`)

Located at `tarkyaan/assessment/question_generator.py`.

### Socratic Probing & Cognitive Dimensions:
Targets the five learning tiers defined in Tarkyaan:
1. **EXPOSURE / UNDERSTANDING**: Evaluates core invariants and mental models (`CONCEPTUAL`, `WHY`, `WHAT_IF`).
2. **RECALL**: Traces state evolution and memory transitions (`TRACE`, `RECALL`, `CODE_READING`).
3. **APPLICATION**: Solves constrained problems and boundary debugging (`APPLICATION`, `DEBUGGING`, `CODE_WRITING`).
4. **MASTERY**: Analyzes asymptotic trade-offs, edge cases, and cross-domain transfers (`EDGE_CASE`, `COMPARISON`, `TRANSFER`).

### Dynamic Adaptation:
- Prioritizes uncertain root prerequisites before interrogating advanced composite concepts.
- Rotates question types to prevent test fatigue and probe complementary cognitive faculties.
- Incorporates prerequisite awareness directly into generated prompts.

---

## 6. Answer Evaluation (`AnswerEvaluator`)

Located at `tarkyaan/assessment/answer_evaluator.py`.

- Evaluates learner responses across three orthogonal vectors:
  - `correctness`: $0.0 - 1.0$
  - `reasoning_quality`: $0.0 - 1.0$ (rewarding first-principles logic, Big-O analysis, and invariant verification)
  - `application_score`: $0.0 - 1.0$ (assessing code syntax, boundary handling, and operational precision)
- Maps composite evaluation scores into calibrated mastery tiers (`UNEXPLORED`, `INTRODUCED`, `PRACTICING`, `COMPETENT`, `MASTERED`).
- Triggers misconception detection only when genuine conceptual or algorithmic anomalies occur.

---

## 7. Epistemic Evidence Model (`ObservedEvidence` vs `InferredEvaluation`)

Located at `tarkyaan/assessment/evidence.py`.

A strict philosophical boundary separates facts from inferences:
- **ObservedEvidence (Epistemic Status: `FACT`)**:
  - Exact learner input string (`raw_response_text`)
  - Verbatim submitted code (`submitted_code`)
  - Concrete wall-clock duration (`time_taken_seconds`)
  - Timestamped observation record
- **InferredEvaluation (Epistemic Status: `INFERENCE`)**:
  - Algorithmic evaluation scores (`correctness`, `reasoning_quality`, `application_score`)
  - Confidence metric ($0.0 - 1.0$)
  - Candidate misconceptions and error classifications
  - Evaluated mastery tier

Observed evidence is never overwritten; inferences are calibrated and can be revised as new observations emerge.

---

## 8. Deterministic Mastery Integration (`MasteryEngine`)

- Diagnostic evidence updates topic mastery exclusively through Phase 1's `MasteryEngine`.
- Uses Bayesian evidence weighting where the update step size scales dynamically with current uncertainty $\sigma$:
  $$\mu_{t+1} = \text{clamp}(\mu_t + \eta \cdot \sigma_t \cdot (\text{score} - \mu_t), 0.0, 1.0)$$
  $$\sigma_{t+1} = \max(0.10, \sigma_t \cdot 0.82)$$
- Updates both persistent SQLite records in `topic_mastery` and volatile learner cache, maintaining full foreign-key referential integrity.

---

## 9. Knowledge Gap Engine & Root-Cause Traversal (`GapAnalyzer`)

Located at `tarkyaan/knowledge/gap_analyzer.py`.

### Gap Types & Severity:
- Identifies `MISSING_PREREQUISITE`, `WEAK_FOUNDATION`, `MISCONCEPTION`, `APPLICATION_GAP`, `RECALL_GAP`, and `CONCEPTUAL_GAP`.
- Computes severity dynamically:
  - `CRITICAL`: High-uncertainty prerequisite blocking multiple downstream concepts.
  - `HIGH`: Intermediate concept with low mastery blocking current target.
  - `MEDIUM` / `LOW`: Isolated application friction or minor recall deficit.

### Root-Cause Analysis:
When a learner fails a question on an advanced concept (e.g. *Binary Search Trees*), `GapAnalyzer` performs backward topological traversal over ancestor prerequisites (*Binary Trees* $\leftarrow$ *Recursion* $\leftarrow$ *Call Stack* $\leftarrow$ *Functions*). It pinpoints the exact foundational node where mastery first degraded, isolating the true root cause rather than diagnosing superficial symptoms.

---

## 10. Misconception Detection (`MisconceptionDetector`)

Located at `tarkyaan/knowledge/misconception_detector.py`.

Categorizes learner errors into:
1. `CONCEPTUAL`: Flawed theoretical paradigm or invalid mental models.
2. `ALGORITHMIC_LOGIC`: Off-by-one errors, boundary omission, or infinite loop conditions.
3. `SYNTAX_IDIOM`: Compiler friction, type mismatches, or language syntax obstacles.
4. `COGNITIVE_FATIGUE`: Sustained session duration ($> 75$ minutes) combined with sudden performance collapse after demonstrated competence.

### Anti-Hallucination & Evidence Rules:
- **Strict Fatigue Rule**: NEVER flags cognitive fatigue on an isolated wrong answer; requires sustained session duration ($>75$m) plus a sudden drop after prior competence.
- **Evidence Confidence**: Initial candidate confidence scales upward ($0.70 \rightarrow 0.85 \rightarrow 0.95$) only upon observed error repetition across diagnostic probes.

---

## 11. Memory Persistence & Isolation

- **Zero NOVA Memory**: Tarkyaan uses its own SQLite store (`TarkyaanMemoryStore` / `TarkyaanMemoryManager`). Zero calls to `memory.memory_manager.MemoryManager` or `memory.vector_store.VectorStore`.
- **Strict Learner Isolation**: All diagnostic sessions, questions, responses, evidence records, gaps, and reports are partitioned strictly by `learner_id`. Learner A's data is mathematically inaccessible to Learner B.

---

## 12. Deterministic vs LLM Responsibilities

| Responsibility | Deterministic Tarkyaan Engine | LLM Assistance (Optional) |
|---|---|---|
| Learner Identity & State | **Sole Owner** | Forbidden |
| Prerequisite Graph Validity | **Sole Owner** (Strict DAG) | Forbidden |
| Mastery Math & Bayesian Updates | **Sole Owner** (`MasteryEngine`) | Forbidden |
| Evidence Ledger & Epistemics | **Sole Owner** (Fact vs Inference) | Forbidden |
| Knowledge Gap Records & Storage | **Sole Owner** | Forbidden |
| Session Status & Stopping Rules | **Sole Owner** | Forbidden |
| Prompt & Phrasing Generation | Supported templates & heuristics | Adaptive Socratic phrasing |
| Answer Interpretation & Rubrics | Deterministic regex / token analysis | Qualitative nuances |

---

## 13. Test Verification Suite

All 66 tests pass with 100% success rate (`pytest tests/ -v`):
- `tests/test_prerequisite_graph.py`: 8 tests (DAG construction, cycle prevention, multi-hop cycle rejection, topological sort, roots/leaves, depth, blocking prerequisites).
- `tests/test_question_generator.py`: 4 tests (Socratic targeting, high uncertainty probe, competent application probe, prerequisite awareness, question rotation).
- `tests/test_answer_evaluator.py`: 4 tests (epistemic separation, strong reasoning score, trivial answer penalty, false assumption detection, submitted code evaluation).
- `tests/test_gap_analyzer.py`: 3 tests (direct concept gap, root cause traversal chain, severity calculation).
- `tests/test_misconception_detector.py`: 5 tests (algorithmic logic, syntax friction, fatigue prevention on single wrong answer, fatigue detection on sustained sessions, repeated error confidence scaling).
- `tests/test_diagnostic_engine.py`: 3 tests (session lifecycle, Socratic diagnostic progression with mastery updates, strict learner isolation).
- Existing Phase 1 tests: 39 tests (all models, memory manager, memory retriever, memory store, mastery engine, retention engine, learner model).

---

## 14. Known Limitations & Scope Boundaries

1. **No Autonomous Curriculum Planning**: Phase 2 strictly diagnoses learner knowledge state and outputs actionable diagnostic reports; curriculum trajectory planning belongs to Phase 3.
2. **No Sandbox Code Execution**: Code submissions are statically and syntactically analyzed; containerized live execution will be integrated in subsequent phases.
3. **No Live OS / Desktop Side Effects**: Adheres strictly to cognitive diagnosis without modifying desktop environments or controlling external tools.

---

## 15. Next Phase: Phase 3

**Phase 3 — Autonomous Learning Planner + Tarkyaan/NOVA Capability Dispatch**:
- Dynamic curriculum generation based on Phase 2 diagnostic reports and detected root-cause gaps.
- Spaced repetition scheduling integrated with retention decay predictions.
- Tarkyaan capability dispatch utilizing read-only NOVA tools (browser, voice, terminal) with strict human-in-the-loop safety boundaries.
