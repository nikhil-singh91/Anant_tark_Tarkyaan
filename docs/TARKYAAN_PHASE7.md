# TARKYAAN — PHASE 7
## MULTIMODAL AUTONOMOUS LEARNING AGENT + VISION / SCREEN AWARENESS + BROWSER INTELLIGENCE + COMPUTER / APPLICATION INTERACTION + FILESYSTEM LEARNING + AUTONOMOUS TASK ORCHESTRATION + UNIFIED AI COMPANION + ADVANCED SAFETY & PERMISSIONS

---

## 1. Phase 7 Objective

Phase 7 marks a fundamental evolutionary leap for Tarkyaan:

- **Phases 1–6:** "Understand the learner, build cognitive mastery models, teach adaptively, and adapt the learning journey."
- **Phase 7:** "Understand the learner, perceive the learner's multi-modal computing environment (screens, documents, images, codebases), safely use appropriate tools, and actively orchestrate autonomous tasks to help the learner accomplish learning goals."

Tarkyaan is now a genuinely **multimodal, tool-using, autonomous AI learning companion**. Learning remains at the center; tools are the hands, vision is the eyes, voice is speech and hearing, reasoning is the brain, and safety is the uncompromisable boundary.

---

## 2. Multimodal Architecture

```
                    TARKYAAN UNIFIED COMPANION
                               │
            ┌──────────────────┼──────────────────┐
          VOICE               TEXT              VISION / SCREEN / DOCS
            │                  │                  │
            └──────────────────┼──────────────────┘
                               │
                    MULTIMODAL INPUT ENGINE
                               │
                    MULTIMODAL CONTEXT ENGINE
         (Learner Model + Active Goals + Environment + Multimodal Signals)
                               │
                    UNIFIED COMPANION ROUTER
                               │
            ┌──────────────────┼──────────────────┐
     LEARNING ENGINES   RESEARCH ENGINE    AUTONOMOUS TASK ENGINE
    (Teaching/Practice) (Web & Curated)    (Observe/Plan/Act/Verify)
            │                  │                  │
            │                  │           CAPABILITY REGISTRY
            │                  │         ┌────────┼────────┬────────┐
            │                  │      Browser  Computer  Files  Terminal
            │                  │         │        │        │        │
            └──────────────────┼─────────┴────────┴────────┴────────┘
                               │
                       TASK VERIFICATION
                               │
                       EVIDENCE & MEMORY
                               │
                        ADAPTIVE LOOP
```

---

## 3. Vision Perception Subsystem

Located in `tarkyaan/vision/`:
- `VisionProvider`: Abstract interface for visual understanding (`analyze_image`, `extract_text`, `analyze_code_image`, `understand_diagram`).
- `MockVisionProvider`: Deterministic, offline provider for unit and regression testing.
- `GeminiVisionProvider`: Live multi-modal provider leveraging Google Gemini Vision models when `GEMINI_API_KEY` is configured.
- `ImageUnderstandingEngine`: Pedagogical image parser that extracts problem statements from coding screenshots (e.g. LeetCode, IDEs), identifies algorithmic topics, discovers syntax or logic errors, and formulates Socratic follow-up prompts.

---

## 4. Document Understanding

Located in `tarkyaan/vision/document_understanding.py`:
- Parses PDFs, Markdown, plaintext, and source code files.
- Extracts structural headers, detects code blocks, and segments long documents into bounded sections.
- Keyword and term indexing for semantic topic identification.
- Bounded retrieval: Top-K relevant sections are retrieved on-demand; raw entire documents are **never dumped into the LLM context**, preventing context bloat.

---

## 5. PDF Learning Pipeline

When a learner uploads a textbook chapter, research paper, or lecture slides:
1. **Document Inspection**: Detects page structure, table of contents, and section headers.
2. **Structural Chunking**: Partitions text into bounded chunks (~400 words) with key terms.
3. **Relevance Mapping**: Queries the active learner roadmap and targets sections matching active learning goals.
4. **Pedagogical Delivery**: The Teaching Engine explains selected chunks incrementally, generates Socratic verification questions, assesses learner answers, and records mastery evidence.

---

## 6. Screen Awareness

Located in `tarkyaan/vision/screen_capture.py` and `screen_understanding.py`:
- Safe, on-demand screen observation using macOS `screencapture` CLI or Quartz, with mock fallbacks for headless testing.
- Translates visual pixels into structured `ScreenContext`: detected active application (e.g., VS Code, PyCharm), active source file, visible error tracebacks, and computer science concepts.
- Strict Privacy & Security:
  - Requires explicit `PermissionCategory.SCREEN_RECORDING` permission.
  - Never captures silently or continuously in the background.
  - Screenshots are held ephemerally in-memory and cleaned up immediately after perception.
  - Passwords, Bearer tokens, and API keys are automatically redacted via regex before reaching reasoning prompts.

---

## 7. Environment Awareness

Located in `tarkyaan/context/environment_context.py`:
- Identifies the learner's active desktop environment (frontmost macOS application, project directory path, platform metadata) via AppleScript and system process inspection.
- Provides graceful fallbacks on non-macOS platforms (`platform.system() != 'Darwin'`).

---

## 8. Browser Intelligence

Located in `tarkyaan/browser/`:
- `BrowserSessionManager`: Manages isolated browser sessions with explicit lifetimes, action budgets (default max 15 actions), timeout limits (default 120s), and instant cancellation support.
- `BrowserCapability`: Provides operations:
  - `open_url(url)`
  - `search_web(query)`
  - `navigate(url)`
  - `extract_content(session_id, max_words)`
  - `close_session(session_id)`
- Web pages are treated strictly as **UNTRUSTED DATA**. The capability wraps external page content in untrusted delimiters and sanitizes potential prompt injections.

---

## 9. Browser Learning

Integrates with Phase 4 `ResearchEngine`:
- The browser is a **capability**; research remains the **intelligence layer**.
- When the learner asks for research or learning resources, Tarkyaan queries search indexes, ranks candidate resources against the learner's mastery tier and learning style, extracts curated summaries, and delivers them via the Teaching Engine.

---

## 10. Computer Interaction

Located in `tarkyaan/computer/computer_controller.py`:
- Abstract interface: `ComputerController` with `click(x, y)`, `type_text(text)`, `press_key(key)`, `scroll(direction, amount)`.
- Implementations:
  - `MacOSComputerController`: Utilizes AppleScript and macOS System Events. Strictly gated on `PermissionCategory.ACCESSIBILITY`.
  - `MockComputerController`: Deterministic action recording and verification for testing.
  - `UnsupportedComputerController`: Graceful fallback for non-macOS platforms.
- Safety: Actions must be observed and verified before declaring success.

---

## 11. Application Control

Located in `tarkyaan/computer/application_adapter.py`:
- Manages application lifecycles for student tooling: Visual Studio Code, Terminal, Finder, Safari, Chrome.
- Operations:
  - `is_running(app)`: Checks process state via `pgrep` or mock state.
  - `open_app(app, path)`: Launches application and optionally opens a project directory or file.
  - `focus_app(app)`: Brings application window to the foreground.
- Empirical Verification: Never declares success until process detection verifies the app is active.

---

## 12. Filesystem Learning

Located in `tarkyaan/filesystem/filesystem_capability.py`:
- Enables project-based learning and codebase exploration.
- Operations:
  - `inspect_project_structure(dir_path)`: Scans workspace hierarchy, filters out `node_modules` / `.venv`, discovers entry points (`main.py`, `app.py`), and counts files by language.
  - `read_code_file(path, max_lines)`: Reads source code files with bounded line limits.
  - `search_symbols(query)`: Locates functions, classes, and variable declarations across project files.
- Security Boundaries:
  - **Default: READ-ONLY.**
  - **Path Traversal Defense**: Rejects any path that escapes the permitted workspace root (`..`).
  - **Secret Protection**: Unconditionally blocks access to `.env`, `.pem`, `.key`, `id_rsa`, `credentials.json`, and token files.

---

## 13. Terminal Boundaries

Located in `tarkyaan/terminal/terminal_capability.py`:
- Safe host command execution strictly separated from the `SecureCodingSandbox` (which runs student code in an isolated subprocess with AST validation).
- Pipeline: `CommandIntent` → `SafetyPolicy` check → `RiskClassification` → `PermissionCheck` → `BoundedSubprocess` → `Verification`.
- Classification:
  - `LOW`: Read-only inspection (`ls`, `pwd`, `echo`, `cat`).
  - `MEDIUM`: Safe test runners and compilers (`pytest`, `python3`, `git status`).
  - `HIGH`: File mutations (`mv`, `cp`, custom scripts). Requires explicit user confirmation.
  - `CRITICAL`: Destructive commands (`rm -rf /`, `mkfs`, `dd`, fork bombs). **Unconditionally blocked.**

---

## 14. Autonomous Task Engine

Located in `tarkyaan/agent/autonomous_task_engine.py`:
- Central orchestration layer for bounded multi-step autonomous tasks.
- Decomposes complex goals into sequential, risk-classified, verifiable steps.
- Enforces hard execution budgets (maximum 10 steps, timeout 120s).
- State Machine: `CREATED` → `PLANNING` → `WAITING_PERMISSION` → `EXECUTING` → `OBSERVING` → `VERIFYING` → `COMPLETED` (or `CANCELLED`, `FAILED`, `TIMEOUT`, `BLOCKED`).

---

## 15. Agent Planning

Located in `tarkyaan/agent/task_planner.py`:
- Decomposes user goals into structured plans:
  - Code Debugging: Observe screen/error → Inspect source file → Diagnose logic flaw → Run sandbox verification.
  - Project Walkthrough: Launch VS Code → Map project structure → Explain architectural design.
  - Web Research: Search academic sources → Evaluate resources → Synthesize curated explanation.
  - DSA Exam Prep: Inspect mastery & gaps → Socratic lesson → Interactive practice challenge.

---

## 16. Observe → Plan → Act → Verify Loop

1. **OBSERVE**: Inspect learner state, active screen context, and environment.
2. **PLAN**: Synthesize a bounded step sequence with capability assignments and verification criteria.
3. **ACT**: Check risk and permissions. If high-risk, pause for user confirmation (`WAITING_PERMISSION`). Dispatch action to capability.
4. **OBSERVE & VERIFY**: The `TaskVerifier` checks postconditions (process running, file modified, exit code 0).
5. **DECIDE**: If verified, proceed to next step. If failed, attempt bounded retry (max 1 retry) before marking task failed.

---

## 17. Tool Selection

The agent dispatches tools based on domain intent:
- Concept explanation → `TeachingEngine`
- Question / Hint generation → `PracticeEngine`
- Web research → `BrowserCapability` + `ResearchEngine`
- Coding practice → `SecureCodingSandbox`
- Codebase navigation → `FilesystemCapability`
- App launch → `ApplicationAdapter`
- Screen inspection → `ScreenUnderstandingEngine`

---

## 18. Permission Model

Integrated with `tarkyaan/safety/permissions.py`:
- Supported Categories: `MICROPHONE`, `SCREEN_RECORDING`, `ACCESSIBILITY`, `FILESYSTEM`, `TERMINAL`, `AUTOMATION`, `NETWORK`.
- Gating: Capabilities requiring permissions check `permission_manager.is_granted(category)`. If denied or undetermined, the agent halts with an honest explanation rather than faking execution.

---

## 19. Safety & Human Control

- **Human-in-the-Loop**: High-risk actions (modifying files, running shell commands) require explicit confirmation before execution.
- **Explainability**: Every action decision includes human-readable rationale and observed evidence.
- **No Unrestricted Autonomy**: Hard bounds on execution steps, action counts, and timeouts.

---

## 20. Prompt Injection Defense

Located in `tarkyaan/companion/prompt_defense.py`:
- Treats all external content (webpages, PDFs, code comments, OCR text) as untrusted data.
- Detects instruction override patterns ("ignore previous instructions", "system prompt", "you are now in developer mode", "delete files").
- Wraps all external text in strict untrusted data boundaries. Untrusted text cannot hijack capability authorization.

---

## 21. Privacy & Redaction

- Ephemeral screen capture: No continuous video streaming or silent recording.
- Automatic Secret Scrubbing: Passwords, OpenAI keys (`sk-...`), Google API keys (`AIza...`), GitHub tokens (`ghp_...`), and Bearer tokens are scrubbed from screenshots, logs, and timelines.
- No credential leakage to UI or EventBus.

---

## 22. Voice Integration

Integrated with Phase 5 `VoiceConversationController`:
- Unified Companion Router synthesizes responses formatted for Voice TTS (`voice_script`).
- Barge-in and interruption: When user speaks or says "Stop", active speech and autonomous tasks halt immediately.

---

## 23. Multimodal Context

Located in `tarkyaan/context/multimodal_context.py`:
- Synthesizes 6 dimensions into a bounded reasoning package:
  1. *Learner State*: Active topic, mastery score, learning health, misconceptions.
  2. *Learner Input*: Voice transcript, text, image, or document.
  3. *Sensory Perception*: Screen context, visual problem extraction.
  4. *Environment*: Active frontmost desktop application.
  5. *Conversation History*: Recent dialogue turns (bounded to last 4 turns).
  6. *Tool Results*: Latest capability outputs.

---

## 24. EventBus Foundation

Phase 7 adds 22 new educational and autonomous events to `TarkyaanEvent`:
- Multimodal: `MULTIMODAL_INPUT_RECEIVED`, `VISION_ANALYSIS_STARTED`, `VISION_ANALYSIS_COMPLETED`, `SCREEN_CAPTURE_STARTED`, `SCREEN_ANALYSIS_COMPLETED`, `DOCUMENT_PARSED`.
- Capabilities: `BROWSER_SESSION_STARTED`, `BROWSER_ACTION_STARTED`, `BROWSER_ACTION_COMPLETED`, `APPLICATION_ACTION_STARTED`, `APPLICATION_ACTION_COMPLETED`, `FILESYSTEM_ACTION_STARTED`, `FILESYSTEM_ACTION_COMPLETED`, `COMPUTER_ACTION_STARTED`, `COMPUTER_ACTION_COMPLETED`, `TERMINAL_ACTION_STARTED`, `TERMINAL_ACTION_COMPLETED`.
- Agent: `AGENT_TASK_CREATED`, `AGENT_PLAN_CREATED`, `AGENT_STEP_STARTED`, `AGENT_STEP_COMPLETED`, `AGENT_WAITING_PERMISSION`, `AGENT_VERIFICATION_STARTED`, `AGENT_VERIFICATION_COMPLETED`, `AGENT_TASK_COMPLETED`, `AGENT_TASK_CANCELLED`, `AGENT_TASK_BLOCKED`, `AGENT_TASK_FAILED`.

---

## 25. Persistence Architecture

Integrated into `tarkyaan/memory/memory_store.py` (SQLite):
- `autonomous_tasks`: Task records, goals, risk tier, step progress, cancellation reason, result.
- `agent_steps`: Step-by-step action parameters, results, and verification audit.
- `permission_audit_log`: Record of permission checks, grants, and elevation requests.
- `project_learning_contexts`: Tracked project paths, languages, and architecture notes.
- `multimodal_artifacts`: Metadata and bounded summaries for processed images, documents, and screenshots.

---

## 26. User Interface Experience

The CLI and UI render transparent agent states:
```
┌────────────────────────────────────────────────────────┐
│ Tarkyaan Autonomous Learning Companion                 │
│                                                        │
│ [State: VIEWING] Understanding screen context...       │
│   ✓ Identified Visual Studio Code                      │
│   ✓ Extracted error: IndexError: list index out of     │
│       range                                            │
│ [State: PLANNING] Creating 4-step debugging plan...    │
│   ✓ Step 1: Observe IDE error output                   │
│   ✓ Step 2: Read source file                           │
│   ✓ Step 3: Socratic misconception explanation         │
│   ✓ Step 4: Run sandbox test                           │
│                                                        │
│ [State: TEACHING] Socratic inquiry presented to learner│
└────────────────────────────────────────────────────────┘
```

---

## 27. Testing Strategy

Deterministic test suite requiring **zero live API keys**:
- `tests/test_vision.py`: Vision provider, MockVisionProvider, Gemini fallback, ImageUnderstandingEngine problem extraction.
- `tests/test_document_understanding.py`: Markdown chunking, code file parsing, bounded section retrieval.
- `tests/test_screen_awareness.py`: Permission gates, mock screen capture, secret redaction, screen context.
- `tests/test_browser_capability.py`: Session manager budgets, web search, prompt injection defense.
- `tests/test_computer_interaction.py`: Mock controller actions, macOS accessibility gates, app adapter lifecycle.
- `tests/test_filesystem_capability.py`: Project mapping, path traversal block, secret file protection, symbol search.
- `tests/test_terminal_capability.py`: Risk classification, critical command blocking, confirmation gates.
- `tests/test_autonomous_agent.py`: Planner, verifier, executor, Observe->Plan->Act->Verify loop, secret scrubbing in timeline.
- `tests/test_prompt_injection.py`: Adversarial injection detection.
- `tests/test_multimodal_acceptance.py`: Full end-to-end acceptance tests (§94–§98).

**Full Regression Result: 341 tests passing (0 failures).**

---

## 28. Platform Support

- **macOS (Darwin)**: Primary target platform with native AppleScript, System Events, and screencapture integration.
- **Linux & Windows**: Graceful degradation; OS automation components report unsupported cleanly without crashing.
- **Headless / CI**: Mock providers enable complete regression testing without OS permissions or display servers.

---

## 29. Known Limitations

- Real screen capture and computer control require the user to manually enable Screen Recording and Accessibility permissions in macOS System Settings.
- Live Gemini Vision requires configuring `GEMINI_API_KEY` in `.env`.
- Live browser control uses HTTP/search abstractions; full headless browser rendering (e.g. Playwright) can be plugged in during Phase 8.

---

## 30. Phase 8 Extension Points

- Direct Playwright browser automation for interactive web-based coding environments.
- Continuous multi-display desktop eye tracking for real-time proactive study nudges.
- Collaborative multi-agent tutoring (e.g., student peer simulation agent).
- Native Swift macOS menu bar and overlay companion UI.
