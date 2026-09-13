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


class SessionStage(str, Enum):
    """Sequential and adaptive stages of a learning session."""
    INITIALIZE = "initialize"
    RECALL = "recall"
    TEACH = "teach"
    CHECK = "check"
    PRACTICE = "practice"
    ASSESS = "assess"
    REVIEW = "review"
    COMPLETE = "complete"


class SessionStatus(str, Enum):
    """Lifecycle status of a persistent learning session."""
    CREATED = "created"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class TeachingMode(str, Enum):
    """Operational mode of the companion teaching experience."""
    TEACH = "teach"
    PRACTICE = "practice"
    ASSESS = "assess"
    REVIEW = "review"
    RESEARCH = "research"
    COMPANION = "companion"


class ExplanationStyle(str, Enum):
    """Stylistic and pedagogical depth modes for concept explanation."""
    SIMPLE_ANALOGY = "simple_analogy"
    CONCEPTUAL = "conceptual"
    STEP_BY_STEP = "step_by_step"
    TECHNICAL = "technical"
    DEEP_FORMAL = "deep_formal"
    VISUAL_MENTAL = "visual_mental"
    COMPARATIVE = "comparative"


class PracticeQuestionType(str, Enum):
    """Taxonomy of exercises generated by the PracticeEngine."""
    RECALL = "recall"
    CONCEPTUAL = "conceptual"
    MULTIPLE_CHOICE = "multiple_choice"
    SHORT_ANSWER = "short_answer"
    EXPLAIN_IN_OWN_WORDS = "explain_in_own_words"
    CODE_TRACE = "code_trace"
    WHAT_IF = "what_if"
    COMPARISON = "comparison"
    APPLICATION = "application"
    DEBUGGING = "debugging"
    EDGE_CASE = "edge_case"
    TRANSFER = "transfer"


class HintLevel(IntEnum):
    """Progressive 5-tier guidance taxonomy (Anti-Answer-Dumping)."""
    NUDGE = 1            # Level 1: Conceptual nudge / reminder
    PRINCIPLE = 2        # Level 2: Relevant governing principle / invariant
    DIRECTION = 3        # Level 3: Partial direction or algorithmic approach
    STRONG_GUIDANCE = 4  # Level 4: Concrete skeleton or structured guidance
    NEAR_SOLUTION = 5    # Level 5: Penultimate step / near-complete logic
    FULL_SOLUTION = 6    # Level 6: Complete solution (explicit request only)


class VoiceState(str, Enum):
    """State machine for real-time voice conversation."""
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    INTERRUPTED = "interrupted"
    PAUSED = "paused"


class VoiceIntent(str, Enum):
    """Recognized intent categories from spoken user turns."""
    WAKE = "wake"
    TEACH_CONCEPT = "teach_concept"
    ASK_QUESTION = "ask_question"
    GIVE_HINT = "give_hint"
    SHOW_ANSWER = "show_answer"
    EXPLAIN_SIMPLY = "explain_simply"
    EXPLAIN_DEEPLY = "explain_deeply"
    GIVE_ANALOGY = "give_analogy"
    GIVE_EXAMPLE = "give_example"
    MAKE_HARDER = "make_harder"
    MAKE_EASIER = "make_easier"
    SKIP = "skip"
    INTERRUPT = "interrupt"
    STOP = "stop"
    PAUSE = "pause"
    RESUME = "resume"
    RUN_CAPABILITY = "run_capability"
    GENERAL_QUERY = "general_query"


# ============================================================
# Phase 6: Adaptive Learning Loop Enums
# ============================================================

class ReplanningTrigger(str, Enum):
    """Evidence-based triggers that cause autonomous curriculum replanning."""
    STALL = "stall"                            # No mastery progress over N sessions
    REGRESSION = "regression"                  # Mastery score decreased significantly
    OVERLOAD = "overload"                      # Learner failing consistently due to difficulty
    GAP_PERSISTENCE = "gap_persistence"        # Knowledge gap unresolved after many attempts
    PLATEAU = "plateau"                        # Mastery stuck at same tier despite practice
    MILESTONE_MISSED = "milestone_missed"      # Target date passed without milestone achieved
    PREREQUISITE_FAILURE = "prerequisite_failure"  # Prerequisite mastery below threshold
    MISCONCEPTION_LOOP = "misconception_loop"  # Same misconception recurring repeatedly
    VELOCITY_DROP = "velocity_drop"            # Learning velocity dropped below threshold
    MANUAL = "manual"                          # Explicitly triggered by learner/system


class HealthStatus(str, Enum):
    """Holistic learning health classification of a learner's current trajectory."""
    HEALTHY = "healthy"           # On track, good velocity, mastery improving
    STALLED = "stalled"           # No progress detected recently
    REGRESSING = "regressing"     # Mastery scores going down
    OVERLOADED = "overloaded"     # Consistently failing; difficulty too high
    PLATEAUED = "plateaued"       # Progress has flatlined at a tier
    AT_RISK = "at_risk"           # Multiple warning signals present
    RECOVERING = "recovering"     # Improving after a stall/regression


class ReviewUrgency(str, Enum):
    """Priority classification for spaced-repetition review tasks."""
    CRITICAL = "critical"   # Severely overdue (> 3× expected interval)
    HIGH = "high"           # Overdue (> 1.5× expected interval)
    NORMAL = "normal"       # Due within expected interval
    LOW = "low"             # Not yet due; pre-scheduled
    OPTIONAL = "optional"   # Bonus review for already-mastered topics


class SandboxLanguage(str, Enum):
    """Supported programming languages in the secure coding sandbox."""
    PYTHON = "python"
    JAVASCRIPT = "javascript"  # Planned


class SandboxStatus(str, Enum):
    """Execution outcome of a sandbox code run."""
    SUCCESS = "success"
    TIMEOUT = "timeout"
    BLOCKED = "blocked"        # Blocked by allowlist / safety check
    ERROR = "error"            # Runtime error in the submitted code
    SYSTEM_ERROR = "system_error"  # Sandbox infrastructure failure


# ==============================================================================
# Phase 7: Multimodal Autonomous Learning Agent Enums
# ==============================================================================


class MultimodalInputType(str, Enum):
    """Channel/Modality through which learner input or observation arrived."""
    TEXT = "text"
    VOICE = "voice"
    IMAGE = "image"
    SCREENSHOT = "screenshot"
    DOCUMENT = "document"
    PDF = "pdf"
    SCREEN = "screen"
    EVENT = "event"


class VisionOperation(str, Enum):
    """Visual perception operations supported by vision providers."""
    ANALYZE_IMAGE = "analyze_image"
    DESCRIBE_IMAGE = "describe_image"
    EXTRACT_TEXT = "extract_text"
    UNDERSTAND_DIAGRAM = "understand_diagram"
    UNDERSTAND_CHART = "understand_chart"
    ANALYZE_CODE_IMAGE = "analyze_code_image"


class AgentTaskStatus(str, Enum):
    """Lifecycle states of an autonomous agent task."""
    CREATED = "created"
    PLANNING = "planning"
    WAITING_PERMISSION = "waiting_permission"
    EXECUTING = "executing"
    OBSERVING = "observing"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"
    BLOCKED = "blocked"
    TIMEOUT = "timeout"


class AgentStepStatus(str, Enum):
    """Execution state of an individual planned step within an autonomous task."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class AgentRiskLevel(str, Enum):
    """Risk tiers for autonomous actions and steps."""
    LOW = "low"          # Read-only, inspection, query
    MEDIUM = "medium"    # Window focus, navigation, app launch
    HIGH = "high"        # File modification, project changes, terminal command
    CRITICAL = "critical"  # Deleting files, modifying system configuration


class BrowserActionType(str, Enum):
    """Atomic browser interaction operations."""
    OPEN_URL = "open_url"
    SEARCH = "search"
    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE_TEXT = "type_text"
    SCROLL = "scroll"
    EXTRACT_CONTENT = "extract_content"
    CLOSE_SESSION = "close_session"


class CompanionChannel(str, Enum):
    """Delivery channels for unified companion responses."""
    TEXT = "text"
    VOICE = "voice"
    MULTIMODAL = "multimodal"


class CompanionIntentDomain(str, Enum):
    """Domain categorization for incoming user requests."""
    LEARNING = "learning"        # Teaching, practice, assessment, concepts
    RESEARCH = "research"        # Web search, paper search, resource curation
    TOOL = "tool"                # Browser, app control, terminal, computer
    DEBUGGING = "debugging"      # Code inspection, error diagnosis, project fix
    PROJECT_STUDY = "project_study"  # Explain project, architecture, codebase
    COMPANION = "companion"      # Conversational, motivation, meta questions


class ProjectLearningType(str, Enum):
    """Focus areas for learning from a codebase or project."""
    CODEBASE_EXPLANATION = "codebase_explanation"
    DEBUGGING = "debugging"
    ARCHITECTURE_WALKTHROUGH = "architecture_walkthrough"
    VIVA_PREPARATION = "viva_preparation"
    CODE_OPTIMIZATION = "code_optimization"

