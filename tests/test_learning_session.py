"""
Unit and Integration Tests for Tarkyaan Learning Session Subsystem (Phase 5).
Verifies stage machine transitions, pause/resume persistence, interaction tracking,
evidence collection, mastery updates, and session summaries.
"""

import pytest
from tarkyaan.learner.learner_model import LearnerModel
from tarkyaan.memory.memory_manager import TarkyaanMemoryManager
from tarkyaan.memory.memory_store import TarkyaanMemoryStore
from tarkyaan.models.enums import MasteryTier, SessionStage, SessionStatus
from tarkyaan.models.learner import LearnerProfile
from tarkyaan.session.evidence_collector import MasteryEvidenceCollector
from tarkyaan.session.session_engine import LearningSessionEngine
from tarkyaan.session.state_machine import (
    InvalidStageTransitionError,
    SessionStateMachine,
)


@pytest.fixture
def memory_manager():
    store = TarkyaanMemoryStore(":memory:")
    return TarkyaanMemoryManager(store=store)


@pytest.fixture
def learner_model(memory_manager):
    prof = LearnerProfile(learner_id="learner_session_test", display_name="Nikhil")
    memory_manager.create_learner(prof)
    return LearnerModel(learner_id=prof.learner_id, memory_manager=memory_manager)


class TestSessionStateMachine:
    def test_valid_sequential_stage_progression(self):
        # INITIALIZE -> TEACH -> CHECK -> PRACTICE -> ASSESS -> REVIEW -> COMPLETE
        stages = [
            (SessionStage.INITIALIZE, SessionStage.TEACH),
            (SessionStage.TEACH, SessionStage.CHECK),
            (SessionStage.CHECK, SessionStage.PRACTICE),
            (SessionStage.PRACTICE, SessionStage.ASSESS),
            (SessionStage.ASSESS, SessionStage.REVIEW),
            (SessionStage.REVIEW, SessionStage.COMPLETE),
        ]
        for from_s, to_s in stages:
            assert SessionStateMachine.can_transition(from_s, to_s) is True
            rec = SessionStateMachine.create_transition_record(from_s, to_s, "Normal progression")
            assert rec.from_stage == from_s
            assert rec.to_stage == to_s

    def test_dynamic_remediation_branch_transitions(self):
        # PRACTICE -> TEACH (remediation loop)
        assert SessionStateMachine.can_transition(SessionStage.PRACTICE, SessionStage.TEACH) is True
        # ASSESS -> PRACTICE (additional practice needed)
        assert SessionStateMachine.can_transition(SessionStage.ASSESS, SessionStage.PRACTICE) is True

    def test_invalid_stage_transition_raises_error(self):
        # INITIALIZE directly to REVIEW is illegal
        assert SessionStateMachine.can_transition(SessionStage.INITIALIZE, SessionStage.REVIEW) is False
        with pytest.raises(InvalidStageTransitionError):
            SessionStateMachine.validate_transition(SessionStage.INITIALIZE, SessionStage.REVIEW)


class TestLearningSessionLifecycle:
    def test_create_and_start_session(self, memory_manager, learner_model):
        engine = LearningSessionEngine(memory_manager=memory_manager, learner_model=learner_model)

        session = engine.create_session(
            learner_id=learner_model.profile.learner_id,
            concept_id="binary_search",
            objective="Understand boundary conditions of binary search"
        )
        assert session.status == SessionStatus.CREATED
        assert session.current_stage == SessionStage.INITIALIZE

        # Start session
        active_sess = engine.start_session(session.session_id)
        assert active_sess.status == SessionStatus.ACTIVE
        assert active_sess.current_stage == SessionStage.TEACH
        assert len(active_sess.stage_history) >= 1

    def test_pause_and_resume_with_full_persistence(self, memory_manager, learner_model):
        engine = LearningSessionEngine(memory_manager=memory_manager, learner_model=learner_model)

        session = engine.create_session(
            learner_id=learner_model.profile.learner_id,
            concept_id="recursion",
            objective="Master call stack mechanics"
        )
        engine.start_session(session.session_id)
        engine.transition_stage(session.session_id, SessionStage.PRACTICE, "Starting exercises")

        # Pause
        paused = engine.pause_session(session.session_id, notes="Break for lunch")
        assert paused.status == SessionStatus.PAUSED
        assert paused.current_stage == SessionStage.PRACTICE

        # Fetch fresh from SQLite to verify persistence
        loaded = engine.get_session(session.session_id)
        assert loaded is not None
        assert loaded.status == SessionStatus.PAUSED
        assert loaded.current_stage == SessionStage.PRACTICE

        # Resume
        resumed = engine.resume_session(session.session_id)
        assert resumed.status == SessionStatus.ACTIVE
        assert resumed.current_stage == SessionStage.PRACTICE

    def test_practice_question_presentation_and_hint_flow(self, memory_manager, learner_model):
        engine = LearningSessionEngine(memory_manager=memory_manager, learner_model=learner_model)
        session = engine.create_session(
            learner_id=learner_model.profile.learner_id,
            concept_id="binary_search",
            objective="Practice array indexing"
        )
        engine.start_session(session.session_id)
        engine.transition_stage(session.session_id, SessionStage.PRACTICE)

        # Present question
        q = engine.present_practice_question(session.session_id, difficulty=2)
        assert q is not None
        assert q.concept_id == "binary_search"

        # Request progressive hint
        hint = engine.request_hint_for_active_question(session.session_id, question_id=q.question_id)
        assert hint is not None
        assert len(hint.hint_text) > 5

        # Check session recorded hint usage
        sess_after_hint = engine.get_session(session.session_id)
        assert sess_after_hint is not None
        assert sess_after_hint.hints_used == 1

        # Submit answer
        eval_res = engine.submit_answer(
            session_id=session.session_id,
            question_id=q.question_id,
            learner_response="low is 0, high is 9, mid is 4, arr[mid] is 16"
        )
        assert eval_res.is_correct is True

        sess_after_ans = engine.get_session(session.session_id)
        assert sess_after_ans is not None
        assert len(sess_after_ans.answers_received) == 1

    def test_session_completion_updates_mastery_and_produces_summary(self, memory_manager, learner_model):
        # Register topic in learner model
        learner_model.register_topic("binary_search", "Binary Search")
        prior_mastery = learner_model.get_topic_mastery("binary_search")
        assert prior_mastery.mastery_score == 0.0

        engine = LearningSessionEngine(memory_manager=memory_manager, learner_model=learner_model)
        session = engine.create_session(
            learner_id=learner_model.profile.learner_id,
            concept_id="binary_search",
            objective="Complete binary search unit"
        )
        engine.start_session(session.session_id)
        engine.transition_stage(session.session_id, SessionStage.PRACTICE)

        # Present and answer question correctly
        q = engine.present_practice_question(session.session_id, difficulty=2)
        engine.submit_answer(
            session_id=session.session_id,
            question_id=q.question_id,
            learner_response="low is 0, high is 9, mid is 4, and arr[mid] is 16."
        )

        # Complete session
        summary = engine.complete_session(session.session_id)

        assert summary.session_id == session.session_id
        assert summary.questions_attempted == 1
        assert summary.questions_correct == 1
        assert len(summary.strengths_demonstrated) >= 1
        assert len(summary.mastery_changes) == 1

        # Verify Bayesian mastery update occurred in LearnerModel
        updated_m = learner_model.get_topic_mastery("binary_search")
        assert updated_m.mastery_score > 0.0
        assert updated_m.uncertainty < 1.0
