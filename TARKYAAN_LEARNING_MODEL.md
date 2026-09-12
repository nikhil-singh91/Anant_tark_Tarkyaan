# TARKYAAN — Learning & Pedagogical Model
**Educational Philosophy, Resource Evaluation, and Evidence-Based Verification**

---

## 1. Core Pedagogical Philosophy

Tarkyaan is built upon sound cognitive science and empirically validated educational psychology principles:

1. **Active Retrieval over Passive Consumption**: Reading an article or watching a 2-hour video provides the illusion of competence. Genuine learning occurs when the brain is forced to retrieve and apply schemas.
2. **Zone of Proximal Development (ZPD)**: Practice tasks must be situated just beyond the learner's current mastery—difficult enough to trigger cognitive effort, but supported enough to prevent helplessness.
3. **Cognitive Load Theory**: Working memory is strictly finite (4–7 chunks). Tarkyaan eliminates unnecessary friction by breaking complex concepts into progressive sub-goals and scaffolding boilerplate.
4. **Interleaving & Spacing**: Alternating between distinct problem types (e.g. tree traversals vs array partitioning) builds robust discrimination skills, while spaced retrieval counters Ebbinghaus memory decay.
5. **Socratic Inquiry**: Guided questions that provoke self-explanation produce significantly deeper conceptual neural pathways than simply handing over the final solution.

---

## 2. Evidence-Based Verification: The 5 Tiers of Mastery

A core tenet of Tarkyaan is: **Never confuse activity with learning.**

```
LEVEL 5: MASTERY (Can synthesize edge cases, optimize trade-offs, and teach others)
   ▲
LEVEL 4: APPLICATION (Can independently solve unassisted unseen problems)
   ▲
LEVEL 3: RECALL (Can reconstruct algorithms and explain mechanics from memory)
   ▲
LEVEL 2: UNDERSTANDING (Can explain the concept Socrates-style and trace small examples)
   ▲
LEVEL 1: EXPOSURE (Watched video, read docs, saw syntax; cannot yet apply independently)
```

| Depth Tier | Definition | Observed Activity | Validating Evidence Required |
| :--- | :--- | :--- | :--- |
| **1. Exposure** | Learner has encountered the material. | Watched a video, opened a documentation page. | None. Mastery score remains unchanged ($M=0.1$). |
| **2. Understanding** | Learner grasps the conceptual mechanism. | Learner answers conceptual "Why" and "What-if" questions. | Explains time complexity trade-offs or traces recursion states on paper. |
| **3. Recall** | Learner can retrieve core structures from memory without reference. | Learner reproduces template logic or definitions without looking up docs. | Writing algorithm skeleton without IDE autocompletion or browser tabs open. |
| **4. Application** | Learner solves novel, unassisted problems applying the concept. | Writes functional code that passes automated test suites on fresh problems. | Green tests on edge cases (empty input, negatives, overflow, duplicates). |
| **5. Mastery** | Learner can critically compare alternatives and debug subtle edge cases. | Analyzes space/time bottlenecks, refactors code, explains limitations. | Explaining why algorithm A beats algorithm B on specific hardware/data constraints. |

---

## 3. Autonomous Resource Discovery & Evaluation Engine

Not all educational resources are created equal. When Tarkyaan researches learning materials (via NOVA's `BrowserManager` and `WebpageExtractor`), it scores candidates across ten objective criteria before recommending them to the learner:

```
Resource Quality Score (0 to 100) = 
  0.20 × Relevance + 
  0.15 × Clarity + 
  0.15 × Credibility + 
  0.10 × LevelAlignment + 
  0.10 × Completeness + 
  0.10 × CodeExemplars + 
  0.05 × TimeEfficiency + 
  0.05 × VisualDiagrams + 
  0.05 × PrerequisiteHygiene + 
  0.05 × Recency
```

### Evaluation Criteria Matrix

| Criterion | High Score (8–10) | Low Score (0–4) |
| :--- | :--- | :--- |
| **Relevance** | Directly targets the diagnosed gap (e.g. recursion tree visualizer). | Generic overview mentioning topic as a footnote. |
| **Clarity** | Plain language, step-by-step state diagrams, zero jargon traps. | Dense, convoluted academic prose with unexplained notation. |
| **Credibility** | Recognized textbook, official language doc, vetted engineer blog. | SEO-farm article with unverified code snippets and spam ads. |
| **Level Alignment** | Matches learner's current mastery tier ($0.4 \le M < 0.7$). | Too elementary (elementary syntax) or too arcane (PhD research papers). |
| **Completeness** | Covers edge cases, invariants, and implementation pitfalls. | Truncated snippet with missing edge cases or hand-waving steps. |
| **Time Efficiency** | High signal-to-noise ratio; delivers core insight in 10 minutes. | 45-minute meandering video with 5 minutes of real substance. |

---

## 4. Socratic Guidance & The Feynman Technique

Tarkyaan employs structured teaching protocols designed to build autonomous problem-solvers:

### The 4-Stage Socratic Protocol
1. **Observation Prompt**: *"Take a look at line 12. What does `array[mid]` evaluate to when `mid` is calculated using integer division?"*
2. **Hypothesis Challenge**: *"If the target is smaller than `mid`, why does your code search the right subarray?"*
3. **Counter-Example Generation**: *"Consider the array `[2, 2, 2, 3, 2, 2]`. How does your pivot logic determine which half is sorted?"*
4. **Feynman Synthesis**: *"Before we write the solution, explain to me in one simple sentence as if to a freshman how sliding windows avoid $O(n^2)$ recomputations."*

---

## 5. Dynamic Replanning Triggers

Static study schedules fail because human learning is inherently non-linear. Tarkyaan actively monitors 7 dynamic replanning triggers:

1. **Velocity Acceleration**: Learner achieves mastery ($M \ge 0.88$) in half the allocated time $\to$ Fast-track prerequisites and unlock advanced modules early.
2. **Velocity Deceleration / Roadblock**: Learner fails 3 consecutive practice exercises $\to$ Pause forward syllabus, inject diagnostic sub-roadmap on missing prerequisite.
3. **Prerequisite Gap Detection**: Assessment reveals foundational deficit (e.g. pointer arithmetic confusion) $\to$ Insert remedial 45-minute unit before resuming current topic.
4. **Time Budget Shift**: Learner reports reduced study availability (e.g. from 2 hours/day down to 45 mins/day) $\to$ Automatically compress syllabus to Pareto high-yield topics.
5. **Deadline Contraction**: Placement interview moved up by 2 weeks $\to$ Recalculate critical path, convert deep theory modules to high-frequency problem patterns.
6. **Resource Invalidation**: Recommended link or site is inaccessible or outdated $\to$ Silently trigger NOVA browser research to fetch alternative verified source.
7. **Spaced Retrieval Alert**: Memory decay algorithm projects retention on Topic $X$ dropping below 60% $\to$ Interleave 10-minute warm-up review into today's session.
