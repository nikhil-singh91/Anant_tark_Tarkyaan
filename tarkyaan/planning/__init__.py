"""
Tarkyaan Planning Package.
Exports GoalDecomposer, PriorityEngine, StrategyEngine, DependencyScheduler,
WorkloadEngine, MilestoneEngine, PlanValidator, PlanBuilder, LearningPlanner,
and Phase 6: AdaptiveLearningEngine, ReplanningEngine, ReviewScheduler,
ProgressReportEngine, LearningDecisionEngine.
"""

from tarkyaan.planning.dependency_scheduler import DependencyScheduler, ScheduledConcept
from tarkyaan.planning.goal_decomposer import DecomposedGoal, GoalDecomposer
from tarkyaan.planning.milestone_engine import MilestoneEngine
from tarkyaan.planning.plan_builder import PlanBuilder
from tarkyaan.planning.plan_validator import PlanValidator
from tarkyaan.planning.planner import LearningPlanner
from tarkyaan.planning.priority_engine import ConceptPriorityScore, PriorityEngine
from tarkyaan.planning.strategy_engine import StrategyDecision, StrategyEngine
from tarkyaan.planning.workload_engine import WorkloadEngine

# Phase 6
from tarkyaan.planning.adaptive import (
    AdaptiveLearningEngine,
    LearningHealthAnalyzer,
    LearningHealthReport,
    MasteryTrajectoryAnalyzer,
    GapEvolutionAnalyzer,
    MisconceptionTrendAnalyzer,
)
from tarkyaan.planning.replanning import (
    ReplanningEngine,
    ReplanningRecord,
    ReplanningTriggerEngine,
    CurriculumMutationEngine,
    TaskPriorityRecalculator,
)
from tarkyaan.planning.review_scheduler import (
    ReviewScheduler,
    SpacedRepetitionScheduler,
    RetentionReviewEngine,
    ReviewInterval,
)
from tarkyaan.planning.progress_report import (
    ProgressReportEngine,
    LearningProgressReport,
    LearningVelocityAnalyzer,
    ResourceEffectivenessAnalyzer,
)
from tarkyaan.planning.decision_engine import (
    LearningDecisionEngine,
    LearningDecision,
    DecisionType,
    DecisionConfidence,
)

__all__ = [
    # Phase 1-3
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
    # Phase 6
    "AdaptiveLearningEngine",
    "LearningHealthAnalyzer",
    "LearningHealthReport",
    "MasteryTrajectoryAnalyzer",
    "GapEvolutionAnalyzer",
    "MisconceptionTrendAnalyzer",
    "ReplanningEngine",
    "ReplanningRecord",
    "ReplanningTriggerEngine",
    "CurriculumMutationEngine",
    "TaskPriorityRecalculator",
    "ReviewScheduler",
    "SpacedRepetitionScheduler",
    "RetentionReviewEngine",
    "ReviewInterval",
    "ProgressReportEngine",
    "LearningProgressReport",
    "LearningVelocityAnalyzer",
    "ResourceEffectivenessAnalyzer",
    "LearningDecisionEngine",
    "LearningDecision",
    "DecisionType",
    "DecisionConfidence",
]
