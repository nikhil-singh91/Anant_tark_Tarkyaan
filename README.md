# TARKYAAN (तर्कयान)
### *Your Autonomous Learning Companion*

[![Architecture: Certified](https://img.shields.io/badge/Architecture-Certified-6366F1.svg)](./TARKYAAN_ARCHITECTURE.md)
[![Foundation: NOVA v3.5](https://img.shields.io/badge/Foundation-NOVA_v3.5-10B981.svg)](./TARKYAAN_NOVA_INTEGRATION.md)
[![Tests: 881 Passed](https://img.shields.io/badge/Tests-881_Passed-brightgreen.svg)](./TARKYAAN_AUDIT_REPORT.md)
[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-blue.svg)](#)

---

## ✦ What is Tarkyaan?

**Tarkyaan (तर्कयान)** is an AI-powered **Autonomous Learning Companion and Autonomous Learning Planner**.

The goal of Tarkyaan is **not** to build another superficial chatbot that generates static syllabi or recites trivia. The goal is to create a genuinely useful, empathetic, and autonomous educational intelligence that deeply understands the human learner, diagnoses their real knowledge state, uncovers hidden prerequisite gaps, researches authoritative resources, creates personalized roadmaps, breaks plans into daily actionable tasks, teaches Socratically, verifies understanding with rigorous evidence, and dynamically adapts the journey when obstacles arise.

---

## ✦ The Meaning of "Tarkyaan"

The name **Tarkyaan** is rooted in classical Sanskrit and Hindi etymology:
- **Tark (तर्क)**: Logical reasoning, rational deduction, dialectic inquiry, clarity of thought.
- **Yaan (यान)**: A vehicle, vessel, carrier, onward journey.

> **"A reasoning-driven vehicle that carries the learner forward."**

Tarkyaan is not just a repository of knowledge; it is an active companion designed to move the learner forward toward their intellectual and professional aspirations.

---

## ✦ Core Architectural Principle: Tarkyaan atop NOVA

Tarkyaan is built directly upon the proven, 881-test verified infrastructure of **NOVA**:

```
                  TARKYAAN
            LEARNING INTELLIGENCE
                     │
                     │  "WHAT to learn & WHY"
                     ▼
             NOVA CAPABILITY LAYER
                     │
                     │  "HOW to execute safely"
                     ▼
           SAFE VERIFIED EXECUTION
                     │
                     ▼
             LEARNER PROGRESS
```

- **Tarkyaan decides**: What the learner needs, what their knowledge gaps are, what learning strategy is optimal, what tasks to schedule, and whether conceptual mastery has been demonstrated.
- **NOVA executes**: Multi-provider AI routing (Gemini, Groq, OpenRouter, Cerebras), voice speech processing (Silero VAD, Faster-Whisper, Edge-TTS), native browser automation (Chrome/Safari via AppleScript), computer control & vision (Quartz CGEvents, Apple Vision OCR), and sandboxed filesystem operations.

---

## ✦ Master Technical Documentation Index

All architectural blueprints, integration contracts, data models, and audit records are documented across 12 comprehensive specifications:

| # | Master Document | Purpose & Key Topics |
| :-: | :--- | :--- |
| **1** | [**TARKYAAN_ARCHITECTURE.md**](./TARKYAAN_ARCHITECTURE.md) | Macro system blueprint, 20-stage autonomous learning loop, domain extensibility, and subsystem layout. |
| **2** | [**TARKYAAN_NOVA_INTEGRATION.md**](./TARKYAAN_NOVA_INTEGRATION.md) | Exhaustive integration matrix, direct reuse policies, prohibited rewrites, and API contracts. |
| **3** | [**TARKYAAN_CAPABILITY_MODEL.md**](./TARKYAAN_CAPABILITY_MODEL.md) | Capability ownership boundaries (Tarkyaan vs NOVA vs Shared), and CapabilityRegistry extensions. |
| **4** | [**TARKYAAN_PERSONALITY.md**](./TARKYAAN_PERSONALITY.md) | Persona, tone, anti-cheerleading rules, voice invariants (`hi-IN-SwaraNeural`), and exemplar dialogues. |
| **5** | [**TARKYAAN_LEARNER_MODEL.md**](./TARKYAAN_LEARNER_MODEL.md) | Cognitive graph, Bayesian mastery estimation, prerequisite DAG traversal, and misconception taxonomy. |
| **6** | [**TARKYAAN_LEARNING_MODEL.md**](./TARKYAAN_LEARNING_MODEL.md) | Pedagogical philosophy, the 5 tiers of mastery (Exposure $\to$ Mastery), and resource scoring. |
| **7** | [**TARKYAAN_AUTONOMY_MODEL.md**](./TARKYAAN_AUTONOMY_MODEL.md) | 6 Autonomy Levels (Levels 0 through 5), safety guardrails, permission boundaries, and cancellation. |
| **8** | [**TARKYAAN_DATA_MODEL.md**](./TARKYAAN_DATA_MODEL.md) | Strongly typed Pydantic v2 schemas for all entities and atomic persistence in Tarkyaan independent memory. |
| **9** | [**TARKYAAN_EVENT_MODEL.md**](./TARKYAAN_EVENT_MODEL.md) | 17-event educational event catalog, typed payload schemas, UI WebSocket broadcast, and telemetry. |
| **10** | [**TARKYAAN_UI_VISION.md**](./TARKYAAN_UI_VISION.md) | Learning Cockpit UI screens, dynamic avatar orb visual states, and tailored HSL dark mode tokens. |
| **11** | [**TARKYAAN_ROADMAP.md**](./TARKYAAN_ROADMAP.md) | 8-phase engineering plan, Grand Hackathon demonstration script, and quantitative validation metrics. |
| **12** | [**TARKYAAN_AUDIT_REPORT.md**](./TARKYAAN_AUDIT_REPORT.md) | Formal technical audit of 32 context documents, 881-test baseline verification, and reconciled discrepancies. |

---

## ✦ Current Status

- **Phase**: **PHASE 0 — UNDERSTAND + AUDIT + ARCHITECT (COMPLETED)**
- **Foundation Baseline**: 881 automated tests collected and passed (100% green).
- **Security & Hygiene**: Zero secrets committed; strict `.gitignore` and `.env.example` isolation in place.
- **Repository**: Synced with official remote repository: `https://github.com/nikhil-singh91/Anant_tark_Tarkyaan.git`.
