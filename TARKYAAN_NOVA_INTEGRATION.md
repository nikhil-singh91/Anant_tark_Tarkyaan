# TARKYAAN ↔ NOVA Integration Specification
**Operational Mapping, Reusability Strategy, and API Contracts**

---

## 1. Executive Integration Principles

Tarkyaan is built directly upon the robust, 881-test verified infrastructure of NOVA. The foundational engineering rule is:
> **"Tarkyaan decides WHAT and WHY; NOVA executes HOW."**

Tarkyaan does not recreate foundational operating system bridges, hardware automation, speech processing, browser drivers, or LLM connection pools. Doing so would bloat the codebase, break tested invariants, introduce security risks, and discard months of platform hardening.

### Non-Duplication Enforcement
The following components are **strictly prohibited** from being rewritten:
- ❌ **TarkyaanLLMClient**: Prohibited. Route all LLM requests through `providers.provider_manager.ProviderManager`.
- ❌ **TarkyaanBrowserEngine**: Prohibited. Route browser interactions through `browser.manager.BrowserManager` and `browser.engine.MacOSNativeBrowserEngine`.
- ❌ **TarkyaanComputerAgent**: Prohibited. Route screen perception and mouse/keyboard events through `core.computer_agent.ComputerAgent` and `core.eyes.manager.NovaEyesManager`.
- ❌ **TarkyaanVoiceEngine**: Prohibited. Reuse `voice.manager.VoiceManager`, Silero VAD, Faster-Whisper, and Edge-TTS.
- ❌ **NOVA Memory Dependency**: Prohibited. Tarkyaan owns its own independent SQLite-based persistent memory system (`TarkyaanMemoryStore` & `TarkyaanMemoryManager`). NOVA memory is NOT used for learner state, goals, or knowledge tracking.

---

## 2. Comprehensive Subsystem Integration & Reuse Table

| # | Tarkyaan Educational Requirement | NOVA Infrastructure Subsystem | Existing NOVA API Contract | Reuse Strategy | New Work Required in Tarkyaan | Operational Risk & Mitigation |
| :-: | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | Pedagogical reasoning, plan synthesis, question generation, and conversational mentorship | Multi-Provider Brain (`providers.provider_manager.ProviderManager`) | `generate_response(prompt, system_prompt, task_type, mode, max_tokens)`<br>`stream_response(...)` | **DIRECT REUSE** | Create prompt profile templates (`TarkyaanSystemPrompts`) and task routing tags (`TaskType.REASONING` vs `TaskType.FAST`). | **Low**: Automatic failover (Gemini $\to$ OpenRouter $\to$ Groq $\to$ Cerebras) guarantees 99.9% uptime. |
| **2** | Storing persistent learner profile, knowledge state, goals, study history, and misconceptions | **Tarkyaan Independent Memory** (`tarkyaan.memory.TarkyaanMemoryManager`) | `create_learner(...)`<br>`update_topic_mastery(...)`<br>`retrieve_context(...)` | **INDEPENDENT (NO NOVA MEMORY)** | Implemented Tarkyaan's own multi-table SQLite memory engine (`data/tarkyaan.db`) with strict learner isolation and epistemic status tracking. | **Zero NOVA Risk**: Decoupled from NOVA storage; zero risk of corrupting NOVA store. |
| **3** | Semantic search across study notes, lecture excerpts, textbook summaries, and problem sets | **Tarkyaan Knowledge Store** (`tarkyaan.memory.memory_store`) | SQL query & contextual token budget retrieval | **INDEPENDENT (NO NOVA VECTORSTORE)** | Local-first relational indexing with semantic metadata in Tarkyaan's own SQLite store. | **Zero NOVA Risk**: Complete isolation from NOVA vectors. |
| **4** | Natural voice dialogue, hands-free study coaching, pronunciation & verbal explanation | Voice V2 Audio Pipeline (`voice.manager.VoiceManager`) | `start_listening()`<br>`stop_listening()`<br>`speak(text)`<br>`is_speaking()` | **DIRECT REUSE** | Inject educational response cleaning so formulas and code blocks speak naturally without raw syntax reading. | **Low**: Reuses proven 16kHz PyAudio stream, Silero VAD, and Faster-Whisper ASR. |
| **5** | Empathetic reaction to non-verbal cues (sighs, hesitations, throat clearing during study) | Acoustic Event Detector (`voice.audio_events.AudioEventDetector`) | `detect_events(audio_chunk)` | **DIRECT REUSE** | Map frustration or fatigue acoustic markers to encouraging pedagogical checkpoints. | **Low**: Runs sub-10ms acoustic classifier without calling external LLMs. |
| **6** | Researching official documentation, tutorials, competitive programming problems, and papers | Browser Automation (`browser.manager.BrowserManager`, `MacOSNativeBrowserEngine`) | `execute_command(text)`<br>`execute_plan(plan)`<br>`open_url(url)`<br>`search_web(query)` | **DIRECT REUSE** | Build `EducationalResourceCurator` that queries Google/GitHub/YouTube via existing site skills. | **Low**: AppleScript native control avoids third-party extension breakages. |
| **7** | Extracting clean readable text and code examples from online educational articles | Webpage Extractor (`browser.extractor.WebpageExtractor`) | `extract_from_url(url)`<br>`extract_active_tab()` | **DIRECT REUSE** | Format extracted article text into clean markdown study cards for the learner. | **Low**: Headless DOM parsing filters out ads, navigation menus, and footers. |
| **8** | Inspecting learner's active IDE, terminal errors, math formulas, or diagrams on screen | Perception Engine (`core.eyes.manager.NovaEyesManager`, `core.eyes.vision_ocr`) | `observe_now(force_ocr)` $\to$ `ScreenState`<br>`AccessibilityInspector.get_active_window()` | **DIRECT REUSE** | Analyze active code editors (VS Code) or browser tabs during practice to provide context-aware hints. | **Medium**: OCR processing overhead; cached with 0.5s TTL and called on-demand. |
| **9** | Clicking learning buttons, launching IDEs, scaffolding project workspaces on learner's Mac | Computer Agent (`core.computer_agent.ComputerAgent`) | `execute_visual_goal(goal)`<br>`type_into_focused_or_target(...)`<br>`close_popup()` | **WRAPPER** | Expose high-level actions: *"Open VS Code with practice template"* or *"Focus problem window"*. | **Medium**: Multi-monitor offsets; mitigated by primary display coordinate normalization. |
| **10** | Resolving learner spoken references: *"Explain this code"*, *"Run that test"*, *"Summarize this tab"* | Environment & Pronoun Resolver (`core.environment.EnvironmentObserver`, `core.context.ContextResolver`) | `refresh()` $\to$ `EnvironmentContext`<br>`resolve_target("this", context, "file"\|"url")` | **DIRECT REUSE** | Bind educational queries directly to frontmost IDE code or active browser documentation tab. | **Low**: AppleScript-based resolution eliminates ambiguous pronoun guessing. |
| **11** | Orchestrating multi-step study sessions: scaffold folders, download data, open references | Autonomous Task Agent V3 (`core.task_agent.planner.TaskPlanner`, `TaskExecutor`) | `plan_goal(goal_text)`<br>`execute_plan(plan)`<br>`cancel_task()` | **EXTENSION** | Register learning-specific capability definitions into `CapabilityRegistry`. | **Low**: Step-by-step verification, rollback, and dynamic error replanning built-in. |
| **12** | Dynamic plan adjustments when a learning step or exercise setup fails | Dynamic Replanner (`core.task_agent.replanner.DynamicReplanner`) | `replan(failed_step, error, context)` | **DIRECT REUSE** | Feed educational fallback strategies (e.g. use local compiler if cloud runner fails). | **Low**: Bounds recovery attempts to `max_replans=3` before alerting user. |
| **13** | Scaffolding practice repositories, creating flashcard files, saving study notes safely | Filesystem Management (`desktop.files.FileSystemManager`) | `create_folder(name, parent)`<br>`create_files(file_names, parent, content_map)`<br>`safe_move_to_trash(path)` | **DIRECT REUSE** | Confine all educational generated materials to `~/Desktop/NOVA_WORKSPACE/Tarkyaan/`. | **Low**: Multi-root search, safe trash integration, and automatic incremental suffixing. |
| **14** | Launching IDEs (VS Code), PDF readers (Preview), terminals, and study software | Desktop Action Manager (`desktop.manager.DesktopActionManager`, `AppLauncher`) | `launch_app(app_name)`<br>`close_app(app_name)` | **DIRECT REUSE** | Seamlessly launch VS Code, Terminal, Chrome, or Preview when starting study sessions. | **Low**: Direct macOS bundle launch with process active verification. |
| **15** | Broadcasting real-time learner state, roadmap updates, and session milestones to UI | Application EventBus (`core.event_bus.EventBus`) | `publish(event, **payload)`<br>`subscribe(event, handler)` | **EXTENSION** | Define and emit `TarkyaanEvent` catalog alongside core `NovaEvent` stream. | **Low**: Thread-safe publish-subscribe with non-blocking subscriber execution. |
| **16** | Formatting dual-channel outputs: concise spoken voice vs rich formatted UI display | Response Orchestrator (`personality.response_orchestrator.ResponseOrchestrator`) | `orchestrate(response_text)` $\to$<br>`(spoken_audio_text, rich_ui_markdown)` | **ADAPTER** | Optimize technical/mathematical notation formatting for clear spoken output. | **Low**: Strips complex markdown, ASCII diagrams, and raw code from TTS voice stream. |
| **17** | Real-time WebSocket bridge connecting Python backend to React/Electron desktop UI | UI Gateway (`ui.backend.server.NovaUIServer`, `ui.backend.event_bridge.EventBridge`) | WebSocket server at `127.0.0.1:8765`<br>`broadcast_event(UIEvent)` | **DIRECT REUSE** | Add specialized learning cards and roadmap payload schemas to the WebSocket pipeline. | **Low**: Localhost-only binding (127.0.0.1) prevents remote LAN exposure. |
| **18** | Preventing unauthorized file modifications, dangerous scripts, or unintended OS changes | Safety Engine (`desktop.safety.DesktopSafetyPolicy`, `browser.safety.BrowserSafetyPolicy`) | `validate_path(path)`<br>`validate_url(url)`<br>`requires_confirmation(action)` | **DIRECT REUSE** | Enforce confirmation gates for any destructive OS operation during study tasks. | **Low**: Sandboxed roots strictly prevent writes to system directories. |

---

## 3. Deep Subsystem Integration Specifications

### 3.1 AI Reasoning & Provider Failover Integration
All prompts originating in Tarkyaan (diagnostic probes, curriculum synthesis, exercise evaluation, code analysis) route through NOVA's `ProviderManager`:

```python
# Tarkyaan AI Provider Adapter
from providers.provider_manager import ProviderManager, TaskType

class TarkyaanAIBridge:
    def __init__(self, provider_manager: ProviderManager):
        self._provider_mgr = provider_manager

    def reason_about_curriculum(self, prompt: str, system_prompt: str) -> str:
        """Uses REASONING routing priority (Gemini -> OpenRouter -> Groq -> Cerebras)."""
        return self._provider_mgr.generate_response(
            prompt=prompt,
            system_prompt=system_prompt,
            task_type=TaskType.REASONING,
            mode="auto"
        )

    def generate_quick_hint(self, prompt: str, system_prompt: str) -> str:
        """Uses FAST routing priority (Groq -> Cerebras -> Gemini -> OpenRouter) for sub-second Socratic hints."""
        return self._provider_mgr.generate_response(
            prompt=prompt,
            system_prompt=system_prompt,
            task_type=TaskType.FAST,
            mode="auto",
            max_tokens=150
        )
```

### 3.2 Memory Subsystem: Complete Tarkyaan Independence
**HARD ARCHITECTURAL INVARIANT: Tarkyaan MUST NOT use NOVA's memory system.**
Tarkyaan learner data, cognitive state, goals, curriculum progress, and interaction memories are maintained in Tarkyaan's own local-first SQLite persistent database (`tarkyaan/memory/` and `data/tarkyaan.db`).

- **Learner Isolation**: Enforced by foreign keys and per-learner SQLite queries; Learner A's data can never bleed into Learner B's context.
- **Epistemic Tracking**: Explicit separation between verified ground truths (`FACT`) and model-generated inferences (`INFERENCE`).
- **Zero NOVA Memory Pollution**: NOVA's `MemoryManager` and `VectorStore` are neither imported nor invoked.

```python
# Tarkyaan Independent Memory Usage
from tarkyaan.memory import TarkyaanMemoryManager, TarkyaanMemoryStore
from tarkyaan.models import LearnerProfile, TopicMastery, MasteryTier

store = TarkyaanMemoryStore("data/tarkyaan.db")
mem = TarkyaanMemoryManager(store=store)

# Storing learner mastery in Tarkyaan's own isolated relational store
mem.update_topic_mastery(TopicMastery(
    learner_id="learner_001",
    topic_id="binary_search",
    name="Binary Search",
    mastery_score=0.85,
    uncertainty=0.15,
    tier=MasteryTier.COMPETENT
))
```

### 3.3 Task Execution & Capability Registry Integration
When Tarkyaan needs to perform system actions (e.g. creating a study workspace, downloading practice datasets, opening documentation in Chrome), it registers learning tools in `CapabilityRegistry` and dispatches plans via `TaskExecutor`:

```python
# Tarkyaan Capability Registration
from core.task_agent.models import CapabilityDefinition, RiskLevel, TaskContext
from core.task_agent.registry import capability_registry

def _setup_study_folder_handler(params: dict, ctx: TaskContext) -> dict:
    folder_name = params.get("folder_name", "Tarkyaan_Practice")
    # Invokes existing FileSystemManager
    from desktop.files import FileSystemManager
    fs = FileSystemManager()
    path = fs.create_folder(folder_name, parent="~/Desktop/NOVA_WORKSPACE")
    return {"success": True, "created_path": str(path)}

def _setup_study_folder_verifier(params: dict, result: dict, ctx: TaskContext) -> bool:
    from pathlib import Path
    path_str = result.get("created_path")
    return bool(path_str and Path(path_str).is_dir())

capability_registry.register(
    CapabilityDefinition(
        name="tarkyaan.setup_workspace",
        subsystem="tarkyaan",
        description="Creates an isolated practice workspace for the current learning session.",
        risk_level=RiskLevel.LOW,
        handler=_setup_study_folder_handler,
        verifier=_setup_study_folder_verifier,
        requires_confirmation=False
    )
)
```

---

## 4. Integration Invariants Check

1. **No Polling Loops**: Tarkyaan does not introduce background busy-wait threads. It reacts via `EventBus` subscriptions and `turn_queue` messages.
2. **Zero Direct Mock Pollution**: Tests never modify global singletons permanently. All tests use teardown fixtures.
3. **Graceful Teardown**: Tarkyaan components register teardown callbacks with `core.lifecycle.ServiceLifecycle` to ensure clean state serialization on application exit.
4. **Zero Key Hardcoding**: Configuration is ingested strictly from `config.settings.Settings`.
