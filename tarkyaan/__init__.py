"""
Tarkyaan (तर्कयान) — Autonomous Learning Companion
A reasoning-driven vehicle that carries the learner forward.
"""

__version__ = "0.1.0"
__author__ = "Nikhil Singh"

from tarkyaan.config.settings import TarkyaanSettings, settings
from tarkyaan.learner.learner_model import LearnerModel
from tarkyaan.learner.mastery_engine import MasteryEngine, MasteryUpdateResult
from tarkyaan.learner.retention_engine import RetentionEngine
from tarkyaan.memory.memory_consolidator import MemoryConsolidator
from tarkyaan.memory.memory_manager import TarkyaanMemoryManager
from tarkyaan.memory.memory_models import MemoryItem
from tarkyaan.memory.memory_retriever import ContextualMemorySummary, MemoryRetriever
from tarkyaan.memory.memory_store import TarkyaanMemoryStore
from tarkyaan.models.assessment import AssessmentResult
from tarkyaan.models.enums import (
    AutonomyLevel,
    EpistemicStatus,
    MasteryTier,
    MemorySource,
    MemoryType,
    MisconceptionCategory,
    TaskStatus,
)
from tarkyaan.models.gaps import KnowledgeGap, MisconceptionRecord
from tarkyaan.models.goals import LearningGoal
from tarkyaan.models.learner import LearnerProfile
from tarkyaan.models.learning import (
    LearningPlan,
    LearningResource,
    LearningSession,
    LearningTask,
    ProgressSnapshot,
    ReplanningRecord,
    ResourceEvaluationScore,
    StudyPhase,
)
from tarkyaan.models.mastery import Subject, Topic, TopicMastery
from tarkyaan.models.diagnostic import (
    DiagnosticDimension,
    DiagnosticQuestion,
    DiagnosticReport,
    DiagnosticSession,
    DiagnosticSessionStatus,
    QuestionType,
)
from tarkyaan.knowledge import (
    CandidateMisconception,
    ConceptNode,
    CyclicDependencyError,
    GapAnalyzer,
    GapSeverity,
    GapType,
    MisconceptionDetector,
    PrerequisiteDAG,
    RootCauseResult,
)
from tarkyaan.assessment import (
    AnswerEvaluator,
    DiagnosticEngine,
    DiagnosticEvidence,
    InferredEvaluation,
    ObservedEvidence,
    QuestionGenerator,
)
from tarkyaan.planning import (
    ConceptPriorityScore,
    DecomposedGoal,
    DependencyScheduler,
    GoalDecomposer,
    LearningPlanner,
    MilestoneEngine,
    PlanBuilder,
    PlanValidator,
    PriorityEngine,
    ScheduledConcept,
    StrategyDecision,
    StrategyEngine,
    WorkloadEngine,
)

from tarkyaan.capabilities import (
    CapabilityCategory,
    CapabilityDefinition,
    CapabilityRegistry,
    CapabilityStatus,
    capability_registry,
)
from tarkyaan.events import EventBus, TarkyaanEvent, event_bus
from tarkyaan.environment import EnvironmentContext, EnvironmentObserver
from tarkyaan.permissions import (
    PermissionCategory,
    PermissionManager,
    PermissionStatus,
    permission_manager,
)
from tarkyaan.providers import (
    BaseProvider,
    LLMProvider,
    ProviderHealth,
    ProviderManager,
    VoiceSTTProvider,
    VoiceTTSProvider,
    provider_manager,
)
from tarkyaan.safety import (
    ConfirmationRequest,
    PromptInjectionGuard,
    RiskLevel,
    SafetyPolicy,
    safety_policy,
)
from tarkyaan.tasks import (
    AutonomousTask,
    AutonomousTaskExecutor,
    StepResult,
    TaskAuditRecord,
    TaskExecutionStatus,
    TaskStep,
)
from tarkyaan.models.enums import (
    AutonomyLevel,
    EpistemicStatus,
    MasteryTier,
    MemorySource,
    MemoryType,
    MisconceptionCategory,
    ResearchDepth,
    ResourceType,
    SourceAuthorityTier,
    TaskStatus,
)
from tarkyaan.models.research import (
    CuratedResourceBundle,
    ResearchHistoryEntry,
    ResearchIntent,
    ResourceDimensionScores,
    ResourceProvenance,
    SearchResultCandidate,
)
from tarkyaan.research import (
    MockSearchProvider,
    QueryGenerator,
    ResearchCache,
    ResearchEngine,
    ResourceClassifier,
    ResourceCurator,
    ResourceEvaluator,
    ResourceExtractor,
    ResourceRanker,
    SearchOptions,
    SearchProvider,
    SearchResponse,
    TavilySearchProvider,
    URLNormalizer,
)

__all__ = [
    "__version__",
    "settings",
    "TarkyaanSettings",
    # Enums
    "AutonomyLevel",
    "EpistemicStatus",
    "MasteryTier",
    "MemorySource",
    "MemoryType",
    "MisconceptionCategory",
    "TaskStatus",
    "ResourceType",
    "ResearchDepth",
    "SourceAuthorityTier",
    # Models
    "LearnerProfile",
    "LearningGoal",
    "Subject",
    "Topic",
    "TopicMastery",
    "KnowledgeGap",
    "MisconceptionRecord",
    "AssessmentResult",
    "LearningPlan",
    "LearningResource",
    "LearningSession",
    "LearningTask",
    "ProgressSnapshot",
    "ReplanningRecord",
    "ResourceEvaluationScore",
    "StudyPhase",
    "ResearchIntent",
    "SearchResultCandidate",
    "ResourceDimensionScores",
    "ResourceProvenance",
    "CuratedResourceBundle",
    "ResearchHistoryEntry",
    # Memory
    "MemoryItem",
    "TarkyaanMemoryStore",
    "TarkyaanMemoryManager",
    "ContextualMemorySummary",
    "MemoryRetriever",
    "MemoryConsolidator",
    # Knowledge Graph & Gaps
    "PrerequisiteDAG",
    "ConceptNode",
    "CyclicDependencyError",
    "GapAnalyzer",
    "RootCauseResult",
    "GapSeverity",
    "GapType",
    "MisconceptionDetector",
    "CandidateMisconception",
    # Diagnostic Assessment
    "QuestionType",
    "DiagnosticDimension",
    "DiagnosticSessionStatus",
    "DiagnosticQuestion",
    "DiagnosticSession",
    "DiagnosticReport",
    "DiagnosticEvidence",
    "ObservedEvidence",
    "InferredEvaluation",
    "QuestionGenerator",
    "AnswerEvaluator",
    "DiagnosticEngine",
    # Learner Engines
    "MasteryEngine",
    "MasteryUpdateResult",
    "RetentionEngine",
    "LearnerModel",
    # Planning Brain
    "GoalDecomposer",
    "DecomposedGoal",
    "PriorityEngine",
    "ConceptPriorityScore",
    "StrategyEngine",
    "StrategyDecision",
    "DependencyScheduler",
    "ScheduledConcept",
    "WorkloadEngine",
    "MilestoneEngine",
    "PlanValidator",
    "PlanBuilder",
    "LearningPlanner",
    # Phase 4 Capabilities Foundation
    "CapabilityRegistry",
    "CapabilityDefinition",
    "CapabilityCategory",
    "CapabilityStatus",
    "capability_registry",
    # Events
    "EventBus",
    "TarkyaanEvent",
    "event_bus",
    # Safety & Permissions
    "SafetyPolicy",
    "PromptInjectionGuard",
    "RiskLevel",
    "ConfirmationRequest",
    "safety_policy",
    "PermissionManager",
    "PermissionCategory",
    "PermissionStatus",
    "permission_manager",
    # Providers
    "ProviderManager",
    "BaseProvider",
    "LLMProvider",
    "VoiceSTTProvider",
    "VoiceTTSProvider",
    "ProviderHealth",
    "provider_manager",
    # Autonomous Tasks
    "AutonomousTask",
    "TaskStep",
    "StepResult",
    "TaskExecutionStatus",
    "TaskAuditRecord",
    "AutonomousTaskExecutor",
    # Environment
    "EnvironmentContext",
    "EnvironmentObserver",
    # Research Engine
    "ResearchEngine",
    "QueryGenerator",
    "URLNormalizer",
    "ResourceExtractor",
    "ResourceClassifier",
    "ResourceEvaluator",
    "ResourceRanker",
    "ResourceCurator",
    "ResearchCache",
    "SearchProvider",
    "SearchOptions",
    "SearchResponse",
    "MockSearchProvider",
    "TavilySearchProvider",
]
