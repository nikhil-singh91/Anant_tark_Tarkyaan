"""
Unit tests for TarkyaanMemoryManager API.
"""

from datetime import datetime, timezone
import pytest

from tarkyaan.memory.memory_manager import TarkyaanMemoryManager
from tarkyaan.memory.memory_models import MemoryItem
from tarkyaan.memory.memory_store import TarkyaanMemoryStore
from tarkyaan.models.assessment import AssessmentResult
from tarkyaan.models.enums import (
    AutonomyLevel,
    EpistemicStatus,
    MasteryTier,
    MemorySource,
    MemoryType,
    MisconceptionCategory,
)
from tarkyaan.models.gaps import KnowledgeGap, MisconceptionRecord
from tarkyaan.models.goals import LearningGoal
from tarkyaan.models.learner import LearnerProfile
from tarkyaan.models.learning import LearningSession
from tarkyaan.models.mastery import Subject, Topic, TopicMastery


@pytest.fixture
def memory_manager():
    store = TarkyaanMemoryStore(":memory:")
    mgr = TarkyaanMemoryManager(store=store)
    yield mgr
    store.close()


class TestMemoryManager:
    def test_learner_crud(self, memory_manager):
        profile = LearnerProfile(
            display_name="Dev",
            primary_domain="Systems Programming",
            preferred_language="Rust",
            daily_time_budget_minutes=90,
            current_autonomy_level=AutonomyLevel.LEVEL_4
        )
        created = memory_manager.create_learner(profile)
        assert created.learner_id == profile.learner_id

        fetched = memory_manager.get_learner(profile.learner_id)
        assert fetched is not None
        assert fetched.display_name == "Dev"
        assert fetched.preferred_language == "Rust"
        assert fetched.current_autonomy_level == AutonomyLevel.LEVEL_4

        fetched.display_name = "Devendra"
        updated = memory_manager.update_learner(fetched)
        assert updated.display_name == "Devendra"

        re_fetched = memory_manager.get_learner(profile.learner_id)
        assert re_fetched.display_name == "Devendra"

    def test_goal_management(self, memory_manager):
        learner = memory_manager.create_learner(LearnerProfile(display_name="User"))
        goal1 = memory_manager.create_goal(LearningGoal(
            learner_id=learner.learner_id,
            title="Learn Trees",
            target_outcome="Solve BFS/DFS",
            priority=4
        ))
        goal2 = memory_manager.create_goal(LearningGoal(
            learner_id=learner.learner_id,
            title="Learn DP",
            target_outcome="Solve 1D DP",
            priority=5
        ))

        goals = memory_manager.get_goals(learner.learner_id)
        assert len(goals) == 2
        # Priority 5 should come first
        assert goals[0].title == "Learn DP"

        # Complete goal
        goal1.mark_completed()
        memory_manager.update_goal(goal1)

        active = memory_manager.get_goals(learner.learner_id, active_only=True)
        assert len(active) == 1
        assert active[0].title == "Learn DP"

    def test_topics_and_prerequisites(self, memory_manager):
        memory_manager.create_subject(Subject(subject_id="cs", name="Computer Science"))
        t1 = memory_manager.create_topic(Topic(topic_id="recursion", subject_id="cs", name="Recursion"))
        t2 = memory_manager.create_topic(Topic(
            topic_id="trees",
            subject_id="cs",
            name="Trees",
            prerequisites=["recursion"]
        ))

        prereqs = memory_manager.get_prerequisites("trees")
        assert "recursion" in prereqs

    def test_topic_mastery_persistence(self, memory_manager):
        learner = memory_manager.create_learner(LearnerProfile(display_name="Learner"))
        memory_manager.create_subject(Subject(subject_id="algo", name="Algorithms"))
        memory_manager.create_topic(Topic(topic_id="binary_search", subject_id="algo", name="Binary Search"))

        mastery = TopicMastery(
            learner_id=learner.learner_id,
            topic_id="binary_search",
            subject_id="algo",
            name="Binary Search",
            mastery_score=0.75,
            uncertainty=0.25,
            tier=MasteryTier.COMPETENT
        )
        saved = memory_manager.update_topic_mastery(mastery)
        assert saved.mastery_score == 0.75

        fetched = memory_manager.get_topic_mastery(learner.learner_id, "binary_search")
        assert fetched is not None
        assert fetched.mastery_score == 0.75
        assert fetched.tier == MasteryTier.COMPETENT

    def test_knowledge_gap_lifecycle(self, memory_manager):
        learner = memory_manager.create_learner(LearnerProfile(display_name="Learner"))
        gap = memory_manager.create_knowledge_gap(KnowledgeGap(
            learner_id=learner.learner_id,
            concept_id="base_case",
            blocking_topic_id="recursion",
            severity="high",
            diagnostic_evidence="Infinite recursion in test case"
        ))

        active_gaps = memory_manager.get_active_gaps(learner.learner_id)
        assert len(active_gaps) == 1
        assert active_gaps[0].concept_id == "base_case"

        # Resolve gap
        success = memory_manager.resolve_knowledge_gap(learner.learner_id, gap.gap_id)
        assert success is True
        assert len(memory_manager.get_active_gaps(learner.learner_id)) == 0

    def test_misconception_and_assessment(self, memory_manager):
        learner = memory_manager.create_learner(LearnerProfile(display_name="Learner"))
        misc = memory_manager.record_misconception(MisconceptionRecord(
            learner_id=learner.learner_id,
            topic_id="recursion",
            category=MisconceptionCategory.ALGORITHMIC_LOGIC,
            description="Skipped base case"
        ))
        assert misc.record_id.startswith("misc_")

        assess = memory_manager.record_assessment(AssessmentResult(
            learner_id=learner.learner_id,
            topic_id="recursion",
            score=0.8,
            prior_mastery=0.4,
            new_mastery=0.6,
            evaluated_tier=MasteryTier.PRACTICING
        ))
        assert assess.assessment_id.startswith("assess_")

        records = memory_manager.get_assessments(learner.learner_id, topic_id="recursion")
        assert len(records) == 1
        assert records[0].score == 0.8

    def test_typed_memory_items_and_epistemic_status(self, memory_manager):
        learner = memory_manager.create_learner(LearnerProfile(display_name="Learner"))

        fact = MemoryItem(
            learner_id=learner.learner_id,
            memory_type=MemoryType.SEMANTIC_LEARNER,
            key="user_target_role",
            content="Targeting SWE placement at tier 1 firm",
            source=MemorySource.USER_EXPLICIT,
            epistemic_status=EpistemicStatus.FACT,
            importance=5
        )
        inference = MemoryItem(
            learner_id=learner.learner_id,
            memory_type=MemoryType.KNOWLEDGE_STATE,
            key="inferred_struggle_pattern",
            content="Prone to off-by-one errors in while loops",
            source=MemorySource.SYSTEM_INFERENCE,
            epistemic_status=EpistemicStatus.INFERENCE,
            importance=4,
            confidence=0.82
        )

        memory_manager.store_memory_item(fact)
        memory_manager.store_memory_item(inference)

        items = memory_manager.get_memory_items(learner.learner_id)
        assert len(items) == 2

        facts = [i for i in items if i.epistemic_status == EpistemicStatus.FACT]
        inferences = [i for i in items if i.epistemic_status == EpistemicStatus.INFERENCE]
        assert len(facts) == 1
        assert len(inferences) == 1
        assert inferences[0].confidence == 0.82
