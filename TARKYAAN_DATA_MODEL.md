# TARKYAAN — Data Models & Schemas
**Type Contracts, Pydantic Specifications, and Storage Bindings**

---

## 1. Domain Entities Overview

All data in Tarkyaan is strongly typed using **Pydantic v2** models, ensuring runtime validation, JSON serialization safety, and schema synchronization with NOVA's atomic storage engine.

```
Tarkyaan Core Entity Hierarchy:
├── LearnerProfile
├── LearningGoal
├── TopicMastery (Graph Node)
├── KnowledgeGap
├── MisconceptionRecord
├── LearningPlan
│   ├── StudyPhase
│   └── LearningTask
├── LearningSession
├── AssessmentResult
├── LearningResource
└── ReplanningRecord
```

---

## 2. Formal Pydantic Model Specifications

```python
"""
tarkyaan.models - Canonical Data Models for Tarkyaan
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, List, Optional
from pydantic import BaseModel, Field, HttpUrl


class MasteryTier(str, Enum):
    UNEXPLORED = "unexplored"
    INTRODUCED = "introduced"
    PRACTICING = "practicing"
    COMPETENT = "competent"
    MASTERED = "mastered"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class MisconceptionCategory(str, Enum):
    CONCEPTUAL = "conceptual"
    ALGORITHMIC_LOGIC = "algorithmic_logic"
    SYNTAX_IDIOM = "syntax_idiom"
    COGNITIVE_FATIGUE = "cognitive_fatigue"


class AutonomyLevel(int, Enum):
    LEVEL_0 = 0  # Conversational
    LEVEL_1 = 1  # Recommendations
    LEVEL_2 = 2  # Plan Generation
    LEVEL_3 = 3  # Supervised Execution
    LEVEL_4 = 4  # Bounded Autonomous Tasks
    LEVEL_5 = 5  # Adaptive Learning Loop


# =====================================================================
# LEARNER PROFILE & COGNITIVE STATE
# =====================================================================

class LearnerProfile(BaseModel):
    learner_id: str = Field(..., description="Unique persistent identifier")
    display_name: str = Field(default="Learner")
    primary_domain: str = Field(default="Computer Science / DSA")
    preferred_language: str = Field(default="C++")
    daily_time_budget_minutes: int = Field(default=120, ge=15, le=720)
    current_autonomy_level: AutonomyLevel = Field(default=AutonomyLevel.LEVEL_3)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active_at: datetime = Field(default_factory=datetime.utcnow)


class TopicMastery(BaseModel):
    topic_id: str = Field(..., description="Unique concept slug, e.g. 'recursion_tree'")
    subject_id: str = Field(..., description="Parent subject, e.g. 'algorithms'")
    name: str
    mastery_score: float = Field(default=0.0, ge=0.0, le=1.0)
    uncertainty: float = Field(default=1.0, ge=0.0, le=1.0)
    tier: MasteryTier = Field(default=MasteryTier.UNEXPLORED)
    prerequisites: List[str] = Field(default_factory=list)
    last_practiced: Optional[datetime] = None
    successful_recalls: int = Field(default=0)
    failed_recalls: int = Field(default=0)


class KnowledgeGap(BaseModel):
    gap_id: str
    concept_id: str
    blocking_topic_id: str
    severity: str = Field(default="high")  # low, medium, high, critical
    diagnostic_evidence: str
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    resolved: bool = Field(default=False)


class MisconceptionRecord(BaseModel):
    record_id: str
    topic_id: str
    category: MisconceptionCategory
    description: str
    observed_code_snippet: Optional[str] = None
    corrective_action_taken: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# =====================================================================
# GOALS, ROADMAPS, & TASKS
# =====================================================================

class LearningGoal(BaseModel):
    goal_id: str
    title: str = Field(..., description="e.g. 'Master DSA for Summer Placement Interviews'")
    target_outcome: str
    deadline: Optional[datetime] = None
    daily_hours: float = Field(default=2.0, ge=0.5, le=10.0)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class LearningTask(BaseModel):
    task_id: str
    title: str
    topic_id: str
    estimated_minutes: int = Field(default=30)
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    nova_capability: Optional[str] = None  # e.g. 'tarkyaan.scaffold_practice'
    parameters: dict[str, Any] = Field(default_factory=dict)
    completed_at: Optional[datetime] = None


class StudyPhase(BaseModel):
    phase_id: str
    name: str = Field(..., description="e.g. 'Phase 1: Recursive Thinking & Backtracking'")
    milestone_order: int
    tasks: List[LearningTask] = Field(default_factory=list)
    is_completed: bool = Field(default=False)


class LearningPlan(BaseModel):
    plan_id: str
    goal_id: str
    title: str
    phases: List[StudyPhase] = Field(default_factory=list)
    total_estimated_hours: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# =====================================================================
# RESOURCES & ASSESSMENTS
# =====================================================================

class ResourceEvaluationScore(BaseModel):
    relevance: float = Field(ge=0, le=10)
    clarity: float = Field(ge=0, le=10)
    credibility: float = Field(ge=0, le=10)
    level_alignment: float = Field(ge=0, le=10)
    completeness: float = Field(ge=0, le=10)
    time_efficiency: float = Field(ge=0, le=10)
    composite_score: float = Field(ge=0, le=100)


class LearningResource(BaseModel):
    resource_id: str
    topic_id: str
    title: str
    url: HttpUrl
    resource_type: str  # video, article, problem, textbook
    evaluation: ResourceEvaluationScore
    recommended_order: int = 1


class AssessmentResult(BaseModel):
    assessment_id: str
    topic_id: str
    task_id: Optional[str] = None
    score: float = Field(ge=0.0, le=1.0)
    prior_mastery: float
    new_mastery: float
    evaluated_tier: MasteryTier
    identified_misconceptions: List[str] = Field(default_factory=list)
    feedback_notes: str
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)


class ReplanningRecord(BaseModel):
    replan_id: str
    plan_id: str
    trigger_reason: str
    changes_summary: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

---

## 3. Storage Binding: NOVA MemoryManager Mapping

Tarkyaan persists all data models through NOVA's atomic JSON `MemoryManager`. No parallel SQLite or MongoDB processes are introduced.

| Entity Model | NOVA `MemoryCategory` | Persistent Key Convention | Storage Format |
| :--- | :--- | :--- | :--- |
| `LearnerProfile` | `MemoryCategory.PROFILE` | `tarkyaan_profile_{learner_id}` | Serialized JSON dictionary |
| `LearningGoal` | `MemoryCategory.GOALS` | `tarkyaan_goal_{goal_id}` | Serialized JSON dictionary |
| `TopicMastery` | `MemoryCategory.EDUCATION` | `tarkyaan_mastery_{topic_id}` | Serialized JSON dictionary |
| `KnowledgeGap` | `MemoryCategory.EDUCATION` | `tarkyaan_gap_{gap_id}` | Serialized JSON dictionary |
| `LearningPlan` | `MemoryCategory.EDUCATION` | `tarkyaan_plan_{plan_id}` | Hierarchical JSON dictionary |
| `AssessmentResult` | `MemoryCategory.EDUCATION` | `tarkyaan_assessment_{id}` | Serialized JSON dictionary |
| `MisconceptionRecord` | `MemoryCategory.CODING` | `tarkyaan_misconception_{id}` | Serialized JSON dictionary |

### Atomic Read/Write Guarantees
- Write operations serialize the Pydantic instance via `.model_dump_json()`.
- NOVA's `MemoryManager` performs an atomic write to a temporary file followed by `os.replace()`, preventing partial corruption during unexpected shutdowns.
- If data corruption occurs, NOVA's store quarantine mechanism captures the corrupt file to `memory_store.json.corrupt.<timestamp>` and initializes a clean fallback store.

---

## 4. Vector Store Document Schemas

Educational reference texts, notes, and problem statements are embedded into NOVA's `VectorStore` (ChromaDB with in-memory mock fallback) with structured metadata:

```json
{
  "document_id": "doc_recursion_backtracking_notes_001",
  "text": "In recursive backtracking, the state must be explicitly restored before returning to the parent stack frame...",
  "metadata": {
    "subsystem": "tarkyaan",
    "topic_id": "backtracking_fundamentals",
    "domain": "DSA",
    "difficulty": "intermediate",
    "format": "note"
  }
}
```
Queries use semantic distance filtered by `{"subsystem": "tarkyaan", "topic_id": active_topic}` to ensure high precision.
