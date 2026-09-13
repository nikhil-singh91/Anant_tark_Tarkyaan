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


class PlanStatus(str, Enum):
    """Lifecycle statuses of a personalized learning plan."""
    DRAFT = "draft"
    PROPOSED = "proposed"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    SUPERSEDED = "superseded"


class TaskType(str, Enum):
    """Pedagogical inquiry and work types for atomic learning tasks."""
    LEARN = "learn"
    UNDERSTAND = "understand"
    RECALL = "recall"
    PRACTICE = "practice"
    APPLY = "apply"
    EXPLAIN = "explain"
    COMPARE = "compare"
    SOLVE = "solve"
    DEBUG = "debug"
    REVIEW = "review"
    ASSESSMENT = "assessment"


class LearningStrategy(str, Enum):
    """Pedagogical ordering strategies for learning plans."""
    PREREQUISITE_FIRST = "prerequisite_first"
    GAP_FIRST = "gap_first"
    FOUNDATION_FIRST = "foundation_first"
    PRACTICE_HEAVY = "practice_heavy"
    BALANCED = "balanced"
    REVIEW_HEAVY = "review_heavy"
    EXAM_FOCUSED = "exam_focused"
    PROJECT_FOCUSED = "project_focused"


class MilestoneStatus(str, Enum):
    """Lifecycle state of a measurable curriculum milestone."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    ACHIEVED = "achieved"


class PlanValidationStatus(str, Enum):
    """Deterministic validation state of a generated plan."""
    VALID = "valid"
    INVALID = "invalid"
    WARNING = "warning"


class ResourceType(str, Enum):
    """Classification of educational and technical learning resources."""
    OFFICIAL_DOCS = "official_docs"
    DOCUMENTATION = "documentation"
    TUTORIAL = "tutorial"
    VIDEO = "video"
    COURSE = "course"
    BOOK = "book"
    PAPER = "paper"
    RESEARCH_PAPER = "research_paper"
    CODING_PROBLEM = "coding_problem"
    EXERCISE = "exercise"
    PROJECT = "project"
    REFERENCE = "reference"
    LECTURE = "lecture"
    DATASET = "dataset"
    INTERACTIVE = "interactive"
    ARTICLE = "article"


class ResearchDepth(str, Enum):
    """Depth specification for autonomous research inquiry."""
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"
    EXHAUSTIVE = "exhaustive"


class SourceAuthorityTier(str, Enum):
    """Evaluated tier of authority and institutional credibility."""
    TIER_1_OFFICIAL = "tier_1_official"
    TIER_2_ACADEMIC_PRIMARY = "tier_2_academic_primary"
    TIER_3_REPUTABLE_EDUCATIONAL = "tier_3_reputable_educational"
    TIER_4_COMMUNITY_PRACTITIONER = "tier_4_community_practitioner"
    TIER_5_UNVERIFIED = "tier_5_unverified"

