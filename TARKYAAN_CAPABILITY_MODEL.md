# TARKYAAN — Capability Model & Ownership Matrix
**Boundary Classification, Capability Registry Extensions, and Tool Specifications**

---

## 1. Explicit Capability Ownership Architecture

To prevent architectural entropy, duplicate implementations, or ambiguous responsibility, all capabilities are strictly segregated across three ownership domains:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        TARKYAAN OWNS (Cognition)                       │
│  • Learner Profile & Epistemic State     • Knowledge Gap Analysis       │
│  • Pedagogical Strategy & Scaffolding   • Curriculum & Plan Generation │
│  • Multi-Tier Rubric Assessment          • Empirical Progress Evaluation│
│  • Learning Resource Quality Evaluation • Dynamic Curriculum Adapting  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    SHARED ADAPTER LAYER (Mediation)                    │
│  • Educational Task Dispatch            • Curated Resource Extraction  │
│  • Memory Schema Mapping (EDUCATION)     • Learning Event Broadcast     │
│  • Dual-channel Voice/UI Presentation   • Safe Practice Sandboxing     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         NOVA OWNS (Execution)                          │
│  • Multi-Provider Routing & Failover     • Audio VAD & Whisper STT      │
│  • Native Chrome/Safari Engine           • Quartz Screen & Apple Vision │
│  • Native AXUIElement Accessibility     • Multi-Root Filesystem        │
│  • System Hardware & Mac Controls       • Thread-Safe EventBus         │
│  • Task Execution & Step Verifier       • Sandboxing & Safety Policies │
└────────────────────────────────────────────────────────────────────────┘
```

### 1.1 Tarkyaan Ownership Domain (The "What" and "Why")
Tarkyaan strictly owns all logic pertaining to human learning, knowledge modeling, and pedagogy:
1. **Learner Knowledge State Modeling**: Maintaining Bayesian/belief mastery levels ($0.0 \le m \le 1.0$) per concept in a prerequisite graph.
2. **Knowledge Gap Detection**: Tracing misconceptions backwards from symptom errors to root prerequisite deficiencies.
3. **Pedagogical Strategy**: Deciding whether the learner needs Socratic probing, worked examples, Feynman simplification, or hard practice.
4. **Curriculum Synthesis**: Sequencing topics into an optimized learning DAG respecting available study hours and deadlines.
5. **Educational Assessment & Scoring**: Evaluating solutions across conceptual correctness, algorithmic efficiency, and edge case coverage.
6. **Resource Quality & Suitability Scoring**: Rating web tutorials, repositories, and documentation on pedagogical clarity, learner alignment, and credibility.
7. **Curriculum Adaptation**: Automatically rescheduling and reorganizing roadmaps when learner velocity accelerates or falters.

### 1.2 NOVA Ownership Domain (The "How")
NOVA owns all foundational OS-level execution, hardware control, and multi-model dispatch:
1. **AI Provider Infrastructure**: Request dispatch, token rate-limiting, and instant zero-crash failover across Gemini, Groq, OpenRouter, and Cerebras.
2. **Audio & Voice Pipeline**: 16kHz microphone stream capture, Silero VAD, acoustic non-speech event interception, local Faster-Whisper ASR, and Edge-TTS voice synthesis.
3. **Browser Automation Engine**: AppleScript manipulation of real Chrome/Safari tabs, DOM extraction, auto-scrolling, and site skills.
4. **Computer Control & Vision**: In-memory Retina frame grabbing, Apple Vision OCR text bounding boxes, AXUIElement accessibility queries, and Quartz CGEvent clicks/keystrokes.
5. **Filesystem & Desktop Control**: Multi-root search, safe trash integration, directory scaffolding, and macOS application lifecycle.
6. **Execution Engine**: `TaskPlanner`, sequential `TaskExecutor`, and `DynamicReplanner` failure recovery loops.
7. **System Safety & Guardrails**: Sandboxed directory roots, dangerous URL protocol blocking, and user confirmation prompts for destructive actions.

### 1.3 Shared Adapter Layer (The Bridge)
The adapter layer binds educational intent to system execution:
- **`EducationalTaskAdapter`**: Translates a high-level learning action (*"Scaffold practice project for Binary Search Trees"*) into atomic NOVA `TaskStep` commands.
- **`LearningMemoryAdapter`**: Serializes rich learning graphs into atomic JSON structures for NOVA's `MemoryManager`.
- **`ResourceResearchAdapter`**: Formulates search queries for NOVA's `BrowserManager` and parses resulting DOM extracts into concise study cards.
- **`LearningEventBridge`**: Translates internal pedagogical milestones into `NovaEvent` publications over `EventBus`.

---

## 2. NOVA Capability Registry Extensions

Tarkyaan extends NOVA's `CapabilityRegistry` (`core.task_agent.registry.CapabilityRegistry`) by registering specialized learning tools. This allows NOVA's autonomous `TaskExecutor` and `DynamicReplanner` to seamlessly plan, execute, and verify learning actions.

### Registered Learning Tool Catalog

| Tool Identifier | Subsystem | Handler Function | Postcondition Verifier | Risk Level | Requires Confirmation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `tarkyaan.scaffold_practice` | `tarkyaan` | `_handle_scaffold_practice` | `_verify_scaffold_practice` | `RiskLevel.LOW` | `False` |
| `tarkyaan.launch_ide_problem` | `tarkyaan` | `_handle_launch_ide_problem` | `_verify_launch_ide_problem` | `RiskLevel.LOW` | `False` |
| `tarkyaan.evaluate_code_solution`| `tarkyaan` | `_handle_evaluate_solution` | `_verify_evaluate_solution` | `RiskLevel.LOW` | `False` |
| `tarkyaan.extract_concept_docs` | `tarkyaan` | `_handle_extract_concept_docs`| `_verify_extract_concept_docs` | `RiskLevel.LOW` | `False` |
| `tarkyaan.capture_ide_context` | `tarkyaan` | `_handle_capture_ide_context` | `_verify_capture_ide_context` | `RiskLevel.LOW` | `False` |
| `tarkyaan.record_assessment` | `tarkyaan` | `_handle_record_assessment` | `_verify_record_assessment` | `RiskLevel.LOW` | `False` |

---

## 3. Concrete Tool Implementation Specifications

### 3.1 `tarkyaan.scaffold_practice`
Creates a dedicated practice directory inside `~/Desktop/NOVA_WORKSPACE/Tarkyaan/` with problem boilerplate, test harness, and README instructions.

```python
from pathlib import Path
from typing import Any
from core.task_agent.models import CapabilityDefinition, RiskLevel, TaskContext
from desktop.files import FileSystemManager

def _handle_scaffold_practice(params: dict[str, Any], ctx: TaskContext) -> dict[str, Any]:
    topic = params.get("topic", "general_practice")
    problem_name = params.get("problem_name", "exercise_1")
    boilerplate_code = params.get("code", "// Solution goes here\n")
    language = params.get("language", "cpp")
    
    fs = FileSystemManager()
    base_dir = "~/Desktop/NOVA_WORKSPACE/Tarkyaan"
    folder_path = fs.create_folder(f"{topic}_{problem_name}", parent=base_dir)
    
    ext_map = {"cpp": "cpp", "python": "py", "javascript": "js", "java": "java"}
    ext = ext_map.get(language.lower(), "txt")
    
    file_map = {
        f"solution.{ext}": boilerplate_code,
        "README.md": f"# Practice: {problem_name}\n\n**Topic**: {topic}\n\n## Instructions\nImplement your solution in `solution.{ext}`."
    }
    fs.create_files(list(file_map.keys()), parent=str(folder_path), content_map=file_map)
    
    return {"success": True, "workspace_path": str(folder_path), "topic": topic}

def _verify_scaffold_practice(params: dict[str, Any], result: dict[str, Any], ctx: TaskContext) -> bool:
    if not result.get("success"):
        return False
    path_str = result.get("workspace_path")
    if not path_str:
        return False
    path = Path(path_str).expanduser()
    return path.is_dir() and (path / "README.md").is_file()
```

### 3.2 `tarkyaan.extract_concept_docs`
Fetches educational documentation or reference tutorials via NOVA's browser engine and extracts clean structured explanations.

```python
def _handle_extract_concept_docs(params: dict[str, Any], ctx: TaskContext) -> dict[str, Any]:
    url = params.get("url")
    concept = params.get("concept", "general")
    if not url:
        return {"success": False, "error": "Missing URL"}
        
    from browser.extractor import WebpageExtractor
    extractor = WebpageExtractor()
    article = extractor.extract_from_url(url)
    
    return {
        "success": True,
        "title": article.title,
        "summary": article.summary,
        "key_points": article.key_points,
        "concept": concept
    }

def _verify_extract_concept_docs(params: dict[str, Any], result: dict[str, Any], ctx: TaskContext) -> bool:
    return result.get("success", False) and bool(result.get("summary"))
```

### 3.3 `tarkyaan.capture_ide_context`
Uses NOVA's in-memory Quartz screen perception (`NovaEyesManager`) and Apple Vision OCR to inspect the learner's current IDE window without dumping images to disk.

```python
def _handle_capture_ide_context(params: dict[str, Any], ctx: TaskContext) -> dict[str, Any]:
    from core.eyes.manager import NovaEyesManager
    eyes = NovaEyesManager()
    screen_state = eyes.observe_now(force_ocr=True)
    
    # Check if frontmost window is an IDE or terminal
    front_window = screen_state.active_window or ""
    visible_code_lines = [b.text for b in screen_state.bounding_boxes if b.confidence > 0.6]
    
    return {
        "success": True,
        "front_window": front_window,
        "code_snippet": "\n".join(visible_code_lines[:40]),
        "total_tokens_detected": len(visible_code_lines)
    }

def _verify_capture_ide_context(params: dict[str, Any], result: dict[str, Any], ctx: TaskContext) -> bool:
    return result.get("success", False) and result.get("total_tokens_detected", 0) >= 0
```

---

## 4. System Prompt Profile Extensions

Tarkyaan registers a specialized personality profile in NOVA's `SystemPromptManager` (`personality.system_prompt.SystemPromptManager`):

```python
# Registered Prompt Profile
TARKYAAN_SYSTEM_PROMPT_PROFILE = {
    "name": "tarkyaan_mentor",
    "identity": "Tarkyaan (तर्कयान) — Autonomous Learning Companion",
    "tagline": "Your Autonomous Learning Companion",
    "tone": "Warm, intellectual, patient, honest, practical, calm, encouraging without fake enthusiasm",
    "rules": [
        "Never say empty cheerleading phrases like 'Great job!' or 'You are doing amazing!'",
        "Diagnose the underlying misconception before answering technical queries.",
        "Ground recommendations in learner goals, available study hours, and knowledge state.",
        "Emphasize conceptual understanding, active recall, and deliberate practice.",
        "Format spoken audio cleanly: strip raw markdown, URLs, and code blocks for speech synthesis."
    ]
}
```

---

## 5. EventBus Extensions

Tarkyaan emits custom pedagogical events through NOVA's thread-safe `EventBus`:

```python
from core.event_bus import event_bus

class TarkyaanEvent:
    GOAL_CREATED = "tarkyaan:goal_created"
    KNOWLEDGE_GAP_DETECTED = "tarkyaan:knowledge_gap_detected"
    PLAN_REPLANNED = "tarkyaan:plan_replanned"
    MASTERY_UPDATED = "tarkyaan:mastery_updated"
    SESSION_STARTED = "tarkyaan:session_started"
    SESSION_COMPLETED = "tarkyaan:session_completed"
```

All subscribers (including the WebSocket `EventBridge` broadcasting to the React UI) receive these structured events without breaking existing `NovaEvent` consumers.
