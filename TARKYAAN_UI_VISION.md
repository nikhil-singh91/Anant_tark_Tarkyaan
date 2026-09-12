# TARKYAAN — User Interface & Experience Blueprint
**Learning-First Interface, Visual Design System, and Dynamic Avatar States**

---

## 1. UI Philosophy: The Learning Cockpit

Tarkyaan's interface is not a basic chat window with an input box at the bottom. It is a **Learning Cockpit** engineered to minimize distraction, maximize focus, provide visual clarity over multi-week roadmaps, and surface cognitive insights transparently.

```
┌────────────────────────────────────────────────────────────────────────┐
│ TOP BAR: Active Goal | Autonomy Level [Lv 3] | Audio / Mic | Settings  │
├────────────┬──────────────────────────────────────────┬────────────────┤
│ SIDEBAR    │ MAIN WORKSPACE VIEW                      │ COPILOT PANEL  │
│            │                                          │                │
│ • Overview │ [ Interactive Roadmap & Knowledge Graph ]│ Tarkyaan Orb   │
│ • Roadmap  │                                          │ (Live Avatar)  │
│ • Tasks    │ [ Today's Actionable Study Cards ]        │                │
│ • Practice │                                          │ Dual Dialogue  │
│ • Gaps     │ [ Focus Mode Session & Live Timer ]      │ - Clean Speech │
│ • Memory   │                                          │ - Rich Code    │
│ • Resources│ [ Real-time Diagnostic Matrix ]          │ - LaTeX Math   │
└────────────┴──────────────────────────────────────────┴────────────────┘
```

---

## 2. Dedicated Learning Screens

### 2.1 The Companion & Dialogue Hub (`CompanionScreen`)
- **Dual-Channel Rendering**: Displays the full conversational exchange with rich formatting—syntax-highlighted code with copy buttons, rendered LaTeX formulas (e.g. $O(2^n)$), and collapsible step traces.
- **Socratic Hint Mode**: When solving problems, hints appear in collapsible accordions so the learner is not accidentally spoiled.

### 2.2 Dynamic Roadmap & Prerequisite Graph (`RoadmapScreen`)
- **Interactive Visual DAG**: Rendered with SVG/Canvas. Concepts appear as glowing nodes connected by prerequisite edges.
- **Node Mastery Colors**:
  - Gray (`#374151`): Unexplored
  - Amber (`#F59E0B`): Practicing / In Progress ($0.4 \le M < 0.7$)
  - Emerald (`#10B981`): Competent / Mastered ($M \ge 0.7$)
  - Crimson pulse (`#EF4444`): Active Diagnosed Knowledge Gap
- Clicking any node opens its prerequisite chain, recommended resources, and past assessment scores.

### 2.3 Today's Actionable Study Deck (`TasksScreen`)
- Displays 2–4 prioritized tasks for the day (e.g. *Task 1: Warmup boundary checks (15m)*, *Task 2: Rotated Array practice in VS Code (45m)*).
- Each card has an **"Execute with Tarkyaan"** button that leverages NOVA's desktop and browser automation to launch required tools in one click.

### 2.4 Focus Session & Pomodoro Checkpoint (`FocusScreen`)
- Clean full-screen focus view with minimal distractions.
- Displays current sub-goal, active timer, and Socratic checkpoint questions at 25-minute intervals.
- Integrated ambient audio / white noise toggle.

### 2.5 Diagnostic Gap & Misconception Matrix (`GapsScreen`)
- Transparently shows the learner *why* they struggled with certain topics.
- Displays diagnosed root causes (e.g. *"Pointer Arithmetic confusion"*), when they were detected, and the assigned remedial exercises.

### 2.6 Curated Educational Resource Hub (`ResourcesScreen`)
- Lists articles, papers, documentation, and video timestamps discovered by NOVA's autonomous browser research.
- Each resource displays its objective **Resource Quality Score (0–100)** with breakdowns for clarity, credibility, and relevance.

### 2.7 Autonomy & System Permissions Center (`GovernanceScreen`)
- Interactive slider to switch between **Autonomy Levels 0 through 5**.
- Live indicators for macOS system permissions (Accessibility, Screen Recording, Microphone, Automation).

---

## 3. Dynamic Interactive Avatar States

Tarkyaan's visual avatar extends NOVA's dynamic orb with specialized educational states:

| Avatar Visual State | Visual Presentation & Dynamics | System Trigger |
| :--- | :--- | :--- |
| **`IDLE`** | Calm, slow indigo breathing glow (`#4F46E5`). | Standing by; awaiting learner query. |
| **`LISTENING`** | Vibrant cyan audio waveform pulse reacting to mic frequency. | Learner is speaking; VAD active. |
| **`THINKING`** | Rapid concentric orbiting geometric particles. | ProviderManager query executing. |
| **`PLANNING`** | Multi-node matrix linking and rearranging. | Synthesizing roadmap or replanning syllabus. |
| **`TEACHING`** | Soft warm amber amplitude wave radiating outward. | Speaking conceptual explanation via Edge-TTS. |
| **`EVALUATING`** | Dual circling scanning lasers with emerald highlights. | Running tests or analyzing submitted code. |
| **`GAP_FOUND`** | Subtle crimson cautionary beacon with soft pulse. | Knowledge gap or misconception diagnosed. |
| **`SUCCESS`** | Radiant emerald flash with gentle settling particle burst. | Concept mastered or exercise passed. |

---

## 4. Visual Design System & Aesthetics

### Color Palette (Tailored HSL & Dark Mode Tokens)
- **Background Deep**: `hsl(222, 47%, 7%)` (`#0B0F19`)
- **Card Surface Glass**: `hsla(222, 47%, 12%, 0.75)` with `backdrop-blur-md`
- **Border Subtlety**: `hsla(217, 33%, 25%, 0.5)`
- **Accent Primary (Reasoning Indigo)**: `hsl(238, 84%, 67%)` (`#6366F1`)
- **Accent Secondary (Clarity Cyan)**: `hsl(187, 92%, 53%)` (`#06B6D4`)
- **Success Mastery (Emerald)**: `hsl(158, 64%, 52%)` (`#10B981`)
- **Warning Gap (Amber / Gold)**: `hsl(38, 92%, 50%)` (`#F59E0B`)
- **Critical Alert (Crimson)**: `hsl(0, 84%, 60%)` (`#EF4444`)

### Typography
- **Primary Body & UI**: `Inter`, sans-serif (clean, modern legibility).
- **Headings & Hero Brand**: `Outfit`, sans-serif (warm, futuristic geometric elegance).
- **Code & Terminals**: `JetBrains Mono`, monospace (ligatures, clear punctuation).
