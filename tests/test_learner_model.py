"""
Unit tests for LearnerModel.
Validates the integrated cognitive representation, evidence updates,
gap management, and snapshot serialization.
"""

from datetime import datetime, timedelta, timezone
import pytest

from tarkyaan.learner.learner_model import LearnerModel
from tarkyaan.memory.memory_manager import TarkyaanMemoryManager
from tarkyaan.memory.memory_store import TarkyaanMemoryStore
from tarkyaan.models.enums import AutonomyLevel, MasteryTier, MisconceptionCategory


@pytest.fixture
def learner_model():
    store = TarkyaanMemoryStore(":memory:")
    mgr = TarkyaanMemoryManager(store=store)
    model = LearnerModel(memory_manager=mgr)
    yield model
    store.close()


class TestLearnerModel:
    def test_initialize_and_load_learner(self, learner_model):
        prof = learner_model.initialize_learner(
            display_name="Rohan",
            primary_domain="Data Structures",
            preferred_language="C++",
            daily_time_budget_minutes=120,
            autonomy_level=AutonomyLevel.LEVEL_4
        )
        assert prof.display_name == "Rohan"
        assert learner_model.learner_id == prof.learner_id
        assert learner_model.profile.preferred_language == "C++"

        # Load into another model instance
        new_instance = LearnerModel(memory_manager=learner_model.memory)
        loaded = new_instance.load_learner(prof.learner_id)
        assert loaded is not None
        assert loaded.display_name == "Rohan"
        assert new_instance.profile.current_autonomy_level == AutonomyLevel.LEVEL_4

    def test_goal_tracking(self, learner_model):
        learner_model.initialize_learner(display_name="Rohan")
        goal = learner_model.create_goal(
            title="Master DP",
            target_outcome="Solve 2D DP problems",
            daily_hours=2.5,
            priority=5
        )
        assert goal.title == "Master DP"
        active = learner_model.get_active_goals()
        assert len(active) == 1
        assert active[0].goal_id == goal.goal_id

    def test_curriculum_and_assessment_update(self, learner_model):
        learner_model.initialize_learner(display_name="Rohan")
        topic = learner_model.register_topic(
            topic_id="recursion",
            name="Recursion Fundamentals",
            subject_id="algo",
            subject_name="Algorithms"
        )
        assert topic.tier == MasteryTier.UNEXPLORED
        assert topic.mastery_score == 0.0
        assert topic.uncertainty == 1.0

        # Learner takes a diagnostic quiz and scores 0.8
        assessment = learner_model.update_mastery_from_assessment(
            topic_id="recursion",
            score=0.8,
            feedback="Strong base-case handling"
        )
        assert assessment.score == 0.8
        assert assessment.new_mastery > 0.0
        assert assessment.new_uncertainty < 1.0
        assert assessment.evaluated_tier in (MasteryTier.INTRODUCED, MasteryTier.PRACTICING)

        # Check that topic mastery in memory matches
        updated_topic = learner_model.get_topic_mastery("recursion")
        assert updated_topic.mastery_score == assessment.new_mastery
        assert updated_topic.successful_recalls == 1

    def test_knowledge_gap_lifecycle(self, learner_model):
        learner_model.initialize_learner(display_name="Rohan")
        learner_model.register_topic(topic_id="trees", name="Trees")
        gap = learner_model.flag_knowledge_gap(
            concept_id="recursion",
            blocking_topic_id="trees",
            diagnostic_evidence="Cannot compute tree height due to recursion misunderstanding",
            severity="critical"
        )
        assert gap.concept_id == "recursion"
        assert not gap.resolved

        # Verify it appears in active gaps
        gaps = learner_model.memory.get_active_gaps(learner_model.learner_id)
        assert len(gaps) == 1

        # Resolve gap
        success = learner_model.resolve_knowledge_gap(gap.gap_id)
        assert success is True
        assert len(learner_model.memory.get_active_gaps(learner_model.learner_id)) == 0

    def test_misconception_and_session_logging(self, learner_model):
        learner_model.initialize_learner(display_name="Rohan")
        misc = learner_model.flag_misconception(
            topic_id="binary_search",
            category=MisconceptionCategory.ALGORITHMIC_LOGIC,
            description="Infinite loop on left <= right when mid calculation not advancing",
            code_snippet="while(left < right) mid = (left+right)/2;"
        )
        assert misc.topic_id == "binary_search"

        sess = learner_model.log_learning_session(
            goal_id=None,
            duration_minutes=45.0,
            topics_covered=["binary_search"],
            tasks_completed=["task_bs_01"],
            notes="Practiced rotated array problems"
        )
        assert sess.duration_minutes == 45.0
        assert len(sess.topics_covered) == 1

    def test_retention_decay_integration(self, learner_model):
        learner_model.initialize_learner(display_name="Rohan")
        learner_model.register_topic(topic_id="arrays", name="Arrays")
        # Perform multiple successful practices so mastery exceeds baseline
        for _ in range(6):
            learner_model.update_mastery_from_assessment(topic_id="arrays", score=1.0)
        initial_m = learner_model.get_topic_mastery("arrays").mastery_score
        assert initial_m > 0.5

        # Simulate 30 days later
        t_future = datetime.now(timezone.utc) + timedelta(days=30)
        decayed_m = learner_model.apply_temporal_decay("arrays", as_of=t_future)
        assert decayed_m < initial_m
        assert decayed_m >= 0.1

    def test_learner_snapshot(self, learner_model):
        learner_model.initialize_learner(display_name="Rohan")
        learner_model.create_goal(title="Goal 1", target_outcome="Outcome 1")
        learner_model.register_topic(topic_id="graphs", name="Graphs")
        learner_model.flag_knowledge_gap(
            concept_id="dfs",
            blocking_topic_id="graphs",
            diagnostic_evidence="DFS stack confusion"
        )

        snapshot = learner_model.get_learner_snapshot()
        assert snapshot["display_name"] == "Rohan"
        assert len(snapshot["active_goals"]) == 1
        assert snapshot["total_topics_tracked"] == 1
        assert len(snapshot["active_knowledge_gaps"]) == 1
        assert "snapshot_taken_at" in snapshot
