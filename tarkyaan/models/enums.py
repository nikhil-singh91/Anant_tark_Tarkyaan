"""
Canonical Enums for Tarkyaan.
Defines mastery tiers, task statuses, misconception taxonomies,
autonomy levels, and memory classification enums.
"""

from enum import Enum, IntEnum


class MasteryTier(str, Enum):
    """Classification tiers representing depth of concept mastery."""
    UNEXPLORED = "unexplored"
    INTRODUCED = "introduced"
    PRACTICING = "practicing"
    COMPETENT = "competent"
    MASTERED = "mastered"


class TaskStatus(str, Enum):
    """Lifecycle states of an atomic learning task."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class MisconceptionCategory(str, Enum):
    """Classification of errors and cognitive friction points."""
    CONCEPTUAL = "conceptual"
    ALGORITHMIC_LOGIC = "algorithmic_logic"
    SYNTAX_IDIOM = "syntax_idiom"
    COGNITIVE_FATIGUE = "cognitive_fatigue"


class AutonomyLevel(IntEnum):
    """Levels of autonomous agency granted to Tarkyaan."""
    LEVEL_0 = 0  # Pure Conversational Companion
    LEVEL_1 = 1  # Contextual Recommendations
    LEVEL_2 = 2  # Plan & Task Generation
    LEVEL_3 = 3  # Supervised Execution
    LEVEL_4 = 4  # Bounded Autonomous Tasks
    LEVEL_5 = 5  # Adaptive Autonomous Learning Loop


class MemoryType(str, Enum):
    """Categories of information stored in Tarkyaan's independent memory."""
    SEMANTIC_LEARNER = "semantic_learner"
    KNOWLEDGE_STATE = "knowledge_state"
    EPISODIC_LEARNING = "episodic_learning"
    GOAL_MEMORY = "goal_memory"
    PROGRESS_MEMORY = "progress_memory"
    INTERACTION_MEMORY = "interaction_memory"


class MemorySource(str, Enum):
    """Provenance/origin of a remembered item."""
    USER_EXPLICIT = "user_explicit"
    ASSESSMENT = "assessment"
    OBSERVED_BEHAVIOR = "observed_behavior"
    LEARNING_SESSION = "learning_session"
    SYSTEM_INFERENCE = "system_inference"


class EpistemicStatus(str, Enum):
    """Distinction between verified ground truth and model inference."""
    FACT = "fact"
    INFERENCE = "inference"
