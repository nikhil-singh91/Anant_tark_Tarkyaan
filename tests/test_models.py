"""
Unit tests for Tarkyaan canonical models and enums.
"""

import pytest
from pydantic import ValidationError

from tarkyaan.models.enums import (
    AutonomyLevel,
    EpistemicStatus,
    MasteryTier,
    MemorySource,
    MemoryType,
    MisconceptionCategory,
    TaskStatus,
)
from tarkyaan.models.learner import LearnerProfile
from tarkyaan.models.goals import LearningGoal
from tarkyaan.models.mastery import Subject, Topic, TopicMastery
from tarkyaan.models.gaps import KnowledgeGap, MisconceptionRecord
from tarkyaan.models.assessment import AssessmentResult
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


class TestTarkyaanModels:
    def test_learner_profile_creation(self):
        profile = LearnerProfile(
            display_name="Arjun",
            primary_domain="Data Structures & Algorithms",
            preferred_language="C++",
            daily_time_budget_minutes=150,
            current_autonomy_level=AutonomyLevel.LEVEL_3
        )
        assert profile.display_name == "Arjun"
        assert profile.preferred_language == "C++"
        assert profile.daily_time_budget_minutes == 150
        assert profile.current_autonomy_level == AutonomyLevel.LEVEL_3
        assert profile.learner_id.startswith("learner_")

    def test_learner_profile_validation_bounds(self):
        # Time budget under 15 minutes should fail
        with pytest.raises(ValidationError):
            LearnerProfile(daily_time_budget_minutes=10)

        # Time budget over 720 minutes should fail
        with pytest.raises(ValidationError):
            LearnerProfile(daily_time_budget_minutes=800)

    def test_topic_mastery_bounds(self):
        valid = TopicMastery(
            learner_id="l1",
            topic_id="recursion",
            name="Recursion",
            mastery_score=0.85,
            uncertainty=0.2,
            tier=MasteryTier.COMPETENT
        )
        assert valid.mastery_score == 0.85

        # Mastery > 1.0 must fail
        with pytest.raises(ValidationError):
            TopicMastery(
                learner_id="l1",
                topic_id="recursion",
                name="Recursion",
                mastery_score=1.5
            )

        # Mastery < 0.0 must fail
        with pytest.raises(ValidationError):
            TopicMastery(
                learner_id="l1",
                topic_id="recursion",
                name="Recursion",
                mastery_score=-0.1
            )

        # Uncertainty > 1.0 must fail
        with pytest.raises(ValidationError):
            TopicMastery(
                learner_id="l1",
                topic_id="recursion",
                name="Recursion",
                uncertainty=1.2
            )

    def test_assessment_result_validation(self):
        res = AssessmentResult(
            learner_id="l1",
            topic_id="binary_search",
            score=0.9,
            prior_mastery=0.5,
            new_mastery=0.75,
            evaluated_tier=MasteryTier.COMPETENT,
            feedback_notes="Clean boundary conditions"
        )
        assert res.score == 0.9
        assert res.evaluated_tier == MasteryTier.COMPETENT

        with pytest.raises(ValidationError):
            AssessmentResult(
                learner_id="l1",
                topic_id="binary_search",
                score=1.1
            )

    def test_knowledge_gap_and_misconceptions(self):
        gap = KnowledgeGap(
            learner_id="l1",
            concept_id="recursion_stack",
            blocking_topic_id="trees",
            severity="critical",
            diagnostic_evidence="Failed recursive call trace"
        )
        assert not gap.resolved
        gap.resolve()
        assert gap.resolved
        assert gap.resolved_at is not None

        misc = MisconceptionRecord(
            learner_id="l1",
            topic_id="trees",
            category=MisconceptionCategory.CONCEPTUAL,
            description="Confused height with depth"
        )
        assert misc.category == MisconceptionCategory.CONCEPTUAL

    def test_serialization_round_trip(self):
        goal = LearningGoal(
            learner_id="l1",
            title="Master DP in 30 days",
            target_outcome="Solve medium LeetCode DP",
            daily_hours=2.5,
            milestones=["1D DP", "2D DP", "Digit DP"]
        )
        json_str = goal.model_dump_json()
        restored = LearningGoal.model_validate_json(json_str)
        assert restored.goal_id == goal.goal_id
        assert restored.title == goal.title
        assert restored.daily_hours == 2.5
        assert len(restored.milestones) == 3
