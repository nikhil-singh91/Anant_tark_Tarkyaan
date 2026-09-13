# TARKYAAN (तर्कयान) — PHASE 5 SPECIFICATION & DOCUMENTATION
## Adaptive Teaching Engine + Practice Engine + Learning Session Engine + Advanced Voice Companion

---

## 1. Phase 5 Objective

Phase 5 elevates Tarkyaan from an autonomous roadmap and curriculum planner into a **living, real-time Autonomous AI Learning Companion**.

In Phases 1 through 4, Tarkyaan established:
- **Phase 1**: Independent persistent memory, cognitive learner model, epistemic knowledge states, and Bayesian mastery calculation.
- **Phase 2**: Socratic diagnostic assessment, prerequisite DAG analysis, and misconception taxonomy.
- **Phase 3**: Autonomous learning planner, curriculum roadmaps, phased task ordering, and workload scheduling.
- **Phase 4**: Autonomous research engine, multidimensional resource evaluation, capability registry, and OS safety boundaries.

Phase 5 moves Tarkyaan from *"Here is what you should learn"* to *"Let's actually learn it together"*. It implements real-time instruction, adaptive explanation, Socratic discovery, progressive practice, anti-answer-dumping hints, persistent session state machines, Bayesian evidence accumulation, and an advanced voice companion loop with barge-in interruption.

---

## 2. Teaching Architecture

The teaching subsystem (`tarkyaan/teaching/`) is structured into four specialized cognitive components coordinated by `TeachingEngine`:

```
                    [TeachingEngine] (Coordinator)
           ┌───────────────┼───────────────┬───────────────┐
           ▼               ▼               ▼               ▼
  [ExplanationEngine] [SocraticEngine] [Misconception] [Prerequisite]
     (Multi-Tier)       (Probing)        (Tutor)        (Tutor)
```

- **Input**: Learner profile, active goal, task, target concept, current mastery score, uncertainty, active knowledge gaps, recent misconceptions, and prerequisite graph.
- **Output**: Structured, pedagogically grounded interactions:
  - `ExplanationResponse`: Summary, sections with ASCII diagrams and code snippets, analogies, counterexamples, invariants, and verification check questions.
  - `SocraticProbe`: Inquiry prompts designed to elicit discovery without dumping facts.
  - `MisconceptionIntervention`: 5-step cognitive friction resolution.
  - `PrerequisiteRemediation`: Structured detour to remediate weak foundation before returning to target topic.

---

## 3. Adaptive Explanation Engine

Explanations dynamically adapt to the learner's actual cognitive tier rather than repeating a static text block:

| Tier / Style | Pedagogical Characteristics | Target Audience |
| :--- | :--- | :--- |
| **Beginner** (`SIMPLE_ANALOGY`) | Real-world metaphors (e.g. dictionary lookup, nesting dolls), zero unnecessary mathematical jargon, intuitive visual diagrams. | Unexplored / Introduced ($M < 0.40$) |
| **Intermediate** (`TECHNICAL`) | Algorithmic implementation, memory invariants, code snippets, boundary edge cases, time/space bounds. | Practicing ($0.40 \le M < 0.70$) |
| **Advanced** (`DEEP_FORMAL`) | Formal invariants, monotonic predicates, proofs, cache locality, SIMD branch prediction, Tail Call Optimization. | Competent / Mastered ($M \ge 0.70$) |

### Dynamic Style Overrides
The engine responds instantly to user requests such as:
- *"Explain this simply"* $\to$ switches immediately to `SIMPLE_ANALOGY`.
- *"Give me an analogy"* $\to$ extracts and emphasizes real-world mental models.
- *"Explain deeply"* $\to$ switches to `DEEP_FORMAL`.
- *"Show an example"* $\to$ delivers step-by-step trace.

---

## 4. Socratic Engine

The `SocraticEngine` prevents passive recitation by formulating purposeful questions that guide learners toward deduction from first principles:
- **Precondition Probing**: *"What fundamental property of the array allows us to safely discard an entire half after one comparison?"*
- **Complexity Deduction**: *"If you double the input size in naive recursive Fibonacci, what happens to the total number of calls?"*
- **Boundary Verification**: *"When arr[mid] < target, why do we advance low = mid + 1 rather than low = mid?"*

### Insight Evaluation
Learner responses are evaluated against target concepts and expected keyword clusters while checking for negations (e.g. distinguishing *"without a base case"* from genuine understanding of base cases).

---

## 5. Misconception-Aware Teaching

When a learner repeatedly makes an error, Tarkyaan never responds with a blunt *"That is incorrect"*. Instead, `MisconceptionTutor` deploys a 5-step cognitive intervention:

1. **Identify the Misconception**: State the misconception without condescension.
2. **Acknowledge the Temptation**: Explain why human intuition naturally falls into this trap.
3. **Contrast Mental Models**: Present the flawed mental model vs. the valid mental model side-by-side.
4. **Concrete Counterexample**: Walk through a demonstrable scenario where the flawed model fails (e.g. searching for 9 in unsorted `[5, 9, 2, 1, 8]` where midpoint 2 erroneously discards 9).
5. **Corrective Check**: Prompt the learner to apply the corrected invariant.

---

## 6. Interactive Practice Engine

The practice subsystem (`tarkyaan/practice/`) generates exercises across difficulty levels 1 to 5 and diverse cognitive exercise types:

- **Recall & Definitions** (Level 1)
- **Conceptual Inquiries & Multiple Choice** (Level 1–2)
- **Application & Numerical Parameters** (Level 2)
- **Code Tracing & Stack Frame Simulation** (Level 3)
- **Debugging & Bug Fixing** (Level 4)
- **Transfer & Novel Problem Solving** (Level 5)

---

## 7. Question Generation & Anti-Answer-Dumping

Every generated `PracticeQuestion` contains:
- `question_id`, `concept_id`, `difficulty` (1–5), `question_type`
- `prompt`: Exercise statement (code snippet or problem description)
- `expected_reasoning`: Required internal logical steps
- `evaluation_criteria`: Atomic criteria evaluated for partial credit
- `hints`: Exactly 5 progressive hint strings
- `solution_explanation`: Full solution (strictly withheld from learner UI)

---

## 8. 5-Tier Progressive Hint Engine

Tarkyaan enforces a strict **Anti-Answer-Dumping** policy. Hints are disclosed progressively:

1. **Tier 1 (Nudge)**: Conceptual reminder (e.g. *"Think about what property allows you to discard half the elements"*).
2. **Tier 2 (Principle)**: Highlights the governing rule or invariant (e.g. *"The array must be strictly sorted"*).
3. **Tier 3 (Direction)**: Suggests the strategic path (e.g. *"Compute mid = low + (high - low) // 2"*).
4. **Tier 4 (Strong Guidance)**: Structural code skeleton or formula template.
5. **Tier 5 (Near-Solution)**: Penultimate step walkthrough.
6. **Tier 6 (Full Solution)**: Released **only** if the learner explicitly asks (*"show me the answer"*) or after multiple unsuccessful attempts with all hints exhausted.

### Evidence Penalty
Each hint consumed applies a calibrated $0.15$ deduction to the empirical evidence score, reflecting that assisted performance indicates lower autonomous mastery.

---

## 9. Multidimensional Answer Evaluation

`AnswerEvaluator` assesses learner answers across multiple dimensions rather than a binary boolean:

- **Correctness**: Validates numerical, logical, or code outputs.
- **Reasoning Quality**: Inspects the presence of sound causal and conceptual explanations.
- **Partial Credit**: Distinguishes between sound reasoning with a minor off-by-one or calculation slip ($0.65$ score) versus total misunderstanding ($0.10$ score).
- **Misconception Detection**: Flags cognitive anti-patterns (e.g. searching unsorted arrays, omitting recursive base cases) and recommends immediate concept revision.

---

## 10. Persistent Learning Session Engine

The `LearningSessionEngine` (`tarkyaan/session/`) manages episodic study sessions. It binds:
- `session_id`, `learner_id`, `plan_id`, `task_id`, `concept_id`, `objective`
- `status`: `CREATED`, `ACTIVE`, `PAUSED`, `COMPLETED`, `CANCELLED`, `FAILED`
- `current_stage`: Current position in the session state machine
- `stage_history`: Audit trail of stage transitions with timestamps and reasons
- `interaction_history`: Turn-by-turn dialogue and event log
- `questions_asked`, `answers_received`, `hints_used`, `evidence_collected`
- `mastery_changes`: Prior and posterior scores per topic
- `summary`: Structured post-session educational synthesis

---

## 11. Session State Machine

The session lifecycle is governed by `SessionStateMachine` through an 8-stage sequence:

```
[INITIALIZE] ──→ [RECALL] ──→ [TEACH] ──→ [CHECK] ──→ [PRACTICE] ──→ [ASSESS] ──→ [REVIEW] ──→ [COMPLETE]
                     │            ▲          │            ▲          ▲
                     └────────────┴──────────┴────────────┼──────────┤
                                    (Remediation Loop)     (Retry)
```

### Allowed Transitions & Branching
- Forward progression: `INITIALIZE` $\to$ `RECALL` $\to$ `TEACH` $\to$ `CHECK` $\to$ `PRACTICE` $\to$ `ASSESS` $\to$ `REVIEW` $\to$ `COMPLETE`.
- Remediation branches:
  - `CHECK` $\to$ `TEACH` (check question failed; review concept first).
  - `PRACTICE` $\to$ `TEACH` (learner struggles on practice; revisit core invariant).
  - `ASSESS` $\to$ `PRACTICE` (assessment reveals partial gap; additional practice recommended).
- Illegal transitions (e.g. `INITIALIZE` $\to$ `REVIEW`) raise `InvalidStageTransitionError`.

---

## 12. Session Resumption & Persistence

All session state, stage transitions, interaction turns, and question/answer records are persisted to SQLite via `TarkyaanMemoryStore` and `TarkyaanMemoryManager`:
- A session can be paused (`pause_session`), written to SQLite, and resumed hours or days later (`resume_session`) with zero context loss.
- `session_interactions` stores turn-by-turn timestamps, speaker roles (`learner`, `companion`, `system`), and metadata.

---

## 13. Mastery Evidence Integration

Tarkyaan reuses the Phase 1 `MasteryEngine` and `LearnerModel.update_mastery_from_assessment(...)`:
- No secondary or duplicate mastery system is created.
- `MasteryEvidenceCollector` computes a calibrated composite evidence score $E \in [0.10, 1.0]$ based on answer accuracy, reasoning quality, recency weighting, and hint deductions.
- Directly updates `TopicMastery`:
  $$M_{t+1}(c) = M_t(c) + \alpha \cdot (E - M_t(c)) \cdot (1 - U_{t+1}(c))$$
  $$U_{t+1}(c) = U_t(c) \cdot 0.75$$
- Reinforces memory stability via `RetentionEngine` and stores an immutable `AssessmentResult` in SQLite.

---

## 14. Advanced Voice Companion Architecture

Tarkyaan’s voice companion architecture bridges speech audio, natural language intent, session management, and capability execution:

```
[Microphone / Audio In]
          ↓
[VoiceSTTProvider] (Whisper / Neural STT)
          ↓
[VoiceCommandRecognizer] (Fast Local Keyword & Intent Extraction)
          ↓
[VoiceContextResolver] (Anaphoric Entity Resolution: "it", "make it harder")
          ↓
[VoiceConversationController] ───→ [LearningSessionEngine] (Teach / Practice / Hint)
          ↓                         └──→ [CapabilityRegistry] (Web Search / Mac)
[VoiceTTSProvider] (EdgeTTS / SwaraNeural)
          ↓
[Speaker / Audio Out] ─── (Barge-in Interruption) ───← [Learner Spoken "Stop"]
          ↓
[EventBus] (VOICE_LISTENING_STARTED, VOICE_SPEAKING_STARTED, VOICE_INTERRUPTED)
```

---

## 15. Voice Activity & STT

- `VoiceSTTProvider` abstracts neural speech recognition (Whisper / local models).
- Audio input is transcribed into normalized text.
- Fallback mock provider (`MockVoiceSTTProvider`) guarantees deterministic offline and CI test execution.

---

## 16. Neural TTS & Voice Personality

- `VoiceTTSProvider` abstracts neural speech synthesis (default voice: `hi-IN-SwaraNeural`).
- Output personality is warm, calm, patient, honest, and encouraging without false excitement or repetitive praise.

---

## 17. Barge-in & Voice Interruption

A true companion cannot force the learner to wait while lengthy audio plays:
- When the companion is in `VoiceState.SPEAKING` and speech activity or an interruption command is detected, `interrupt()` is called immediately.
- Audio synthesis/playback halts instantaneously.
- State transitions to `VoiceState.INTERRUPTED`, then `VoiceState.LISTENING`.
- Emits `TarkyaanEvent.VOICE_INTERRUPTED` on the `EventBus`.

---

## 18. Natural Voice Cancellation

Spoken commands are recognized via normalized keyword and regex matching:
- **Interruption/Cancellation**: *"stop"*, *"wait"*, *"hold on"*, *"cancel"*, *"never mind"*, *"that's enough"*, *"रुको"*, *"रुकिए"*, *"बस करो"*, *"रहने दो"*.
- **Pacing**: *"pause"*, *"resume"*, *"continue"*, *"make it harder"*, *"make it easier"*, *"skip this"*.
- **Inquiries**: *"give me a hint"*, *"show me the answer"*, *"explain simply"*, *"give me an analogy"*, *"test me"*.
- **Wake Word Stripping**: Strips *"Hey Tarkyaan"*, *"Tarkyaan"*, *"हे तर्कयान"*.

---

## 19. Voice Conversational Context

The `VoiceContextResolver` resolves anaphoric references:
- *"Explain it simply"* $\to$ resolves *"it"* to the active topic (`binary_search`).
- *"Give me another example"* $\to$ targets the current explanation context.
- *"Give me a hint"* $\to$ targets the currently presented practice exercise.
- *"Make it harder"* $\to$ steps up difficulty on the active topic.

---

## 20. Voice Driving Learning Sessions

Spoken turns directly operate the learning session:
1. Learner: *"Hey Tarkyaan, teach me binary search."* $\to$ starts session, explains concept.
2. Learner: *"Test me on this."* $\to$ presents practice exercise.
3. Learner: *"Give me a hint."* $\to$ delivers Tier 1 progressive hint.
4. Learner speaks answer $\to$ evaluates reasoning, provides grounded feedback.
5. Learner: *"Stop"* $\to$ halts audio playback immediately.
6. Learner: *"Resume"* $\to$ continues session.

---

## 21. Capability Routing via Voice

Voice commands requesting research or system actions route through Phase 4 `CapabilityRegistry`:
- *"Search for binary search tutorials"* $\to$ invokes `research.web_search` and speaks the outcome.
- Unsupported actions are never falsely claimed.

---

## 22. UI Synchronization & Event Bus

The voice companion publishes typed events on the thread-safe `EventBus`:
- `VOICE_LISTENING_STARTED`, `VOICE_LISTENING_FINISHED`
- `VOICE_SPEAKING_STARTED`, `VOICE_SPEAKING_FINISHED`
- `VOICE_INTERRUPTED`
- `SESSION_STAGE_CHANGED`, `QUESTION_PRESENTED`, `ANSWER_EVALUATED`, `HINT_PROVIDED`
- `MASTERY_UPDATED`

UI dashboards can subscribe to these events for real-time status indicators (Listening, Thinking, Speaking, Teaching, Evaluating).

---

## 23. Safety & Untrusted Data Boundary

- **Untrusted Student Input**: Student responses are sanitized and never passed directly into shell execution or arbitrary code interpreters.
- **Code Learning Safety**: Programming questions are evaluated via AST and lexical pattern matching; arbitrary untrusted host execution is strictly prohibited.
- **Secret Protection**: Provider API keys and credentials are never printed, logged, or exposed in event payloads.

---

## 24. API Configuration

Tarkyaan provider configuration is stored in `.env` (template in `.env.example`):
```bash
# AI Reasoning
GEMINI_API_KEY=
OPENROUTER_API_KEY=
GROQ_API_KEY=

# Search & Research
TAVILY_API_KEY=

# Speech & Voice (Phase 5)
ELEVENLABS_API_KEY=
TARKYAAN_VOICE_LANGUAGE=en
TARKYAAN_TTS_VOICE=hi-IN-SwaraNeural
TARKYAAN_STT_MODEL=whisper-1
```

---

## 25. Complete Verification Results

### Test Suite Execution
- Total Tests: **184 passed in 3.01s** (zero failures, zero skipped).
- Unit Tests: Teaching Engine (9), Practice Engine (12), Learning Session (7), Voice Companion (9), End-to-End Acceptance (2).
- Regression Tests: All Phase 1, Phase 2, Phase 3, and Phase 4 tests pass with 100% fidelity.

### Static Code Analysis
- `npx pyright`: **0 errors, 0 warnings, 0 informations**.

### Runtime Health & Capabilities
- `python3 -m tarkyaan --status`: All 12 operational checkpoints verified healthy.
- `python3 -m tarkyaan --capabilities`: Full capability inventory verified.

---

## 26. NOVA Parity Matrix & Integrity Check

### NOVA Zero-Modification Verification
- Working Tree: `git -C ../NOVA_SETUP status` $\to$ **Working tree clean, 0 modifications**.
- Git Diff: `git -C ../NOVA_SETUP diff` $\to$ **Zero lines changed**.

### Capability Parity Matrix

| Capability Area | NOVA Implementation | Tarkyaan Phase 5 Implementation | Status |
| :--- | :--- | :--- | :--- |
| **Voice Conversation** | `voice/manager.py`, `commands.py` | `tarkyaan/voice/conversation_controller.py` | **IMPLEMENTED** |
| **Barge-in Interruption** | Voice activity interrupt | `VoiceConversationController.interrupt()` | **IMPLEMENTED** |
| **STT Provider** | Groq Whisper / local Whisper | `VoiceSTTProvider` / `MockVoiceSTTProvider` | **IMPLEMENTED** |
| **TTS Provider** | EdgeTTS / ElevenLabs | `VoiceTTSProvider` / `MockVoiceTTSProvider` | **IMPLEMENTED** |
| **Adaptive Teaching** | N/A (General Assistant) | `tarkyaan/teaching/teaching_engine.py` | **IMPLEMENTED** |
| **Interactive Practice** | N/A (General Assistant) | `tarkyaan/practice/practice_engine.py` | **IMPLEMENTED** |
| **Progressive Hints** | N/A (General Assistant) | `tarkyaan/practice/hint_engine.py` | **IMPLEMENTED** |
| **Learning Sessions** | N/A (General Assistant) | `tarkyaan/session/session_engine.py` | **IMPLEMENTED** |
| **Mastery Evidence** | N/A (General Assistant) | `MasteryEvidenceCollector` $\to$ `MasteryEngine` | **IMPLEMENTED** |
| **Web Research** | Brave / Tavily search | `tarkyaan/research/research_engine.py` | **IMPLEMENTED** |
| **Mac Automation** | macOS AppleScript / Accessibility | `tarkyaan/mac/` | **PLANNED** |
| **Terminal Execution**| Bounded shell runner | `tarkyaan/terminal/` | **PLANNED** |

---

## 27. Phase 6 Extension Points

Phase 5 establishes the teaching, practice, and session evidence infrastructure. Phase 6 will consume:
- Session summaries and mastery deltas
- Misconception frequency and repeat failure rates
- Resource effectiveness metrics

Phase 6 will introduce:
- **Dynamic Curriculum Replanning**: Real-time DAG mutation when milestones stall.
- **Autonomous Review Scheduling**: Spaced repetition dispatch based on retention decay curves.
- **Deep Multimodal Coding Sandbox**: Secure containerized execution for advanced software engineering tasks.
