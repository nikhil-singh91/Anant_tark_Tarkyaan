"""
End-to-End Acceptance Journey Tests for Tarkyaan Phase 5.
Validates Section 54 (Full Learning Journey) and Section 55 (Voice Companion Acceptance Journey).
"""

import pytest
from tarkyaan.capabilities.registry import CapabilityRegistry
from tarkyaan.events.event_bus import TarkyaanEvent, event_bus
from tarkyaan.learner.learner_model import LearnerModel
from tarkyaan.memory.memory_manager import TarkyaanMemoryManager
from tarkyaan.memory.memory_store import TarkyaanMemoryStore
from tarkyaan.models.enums import (
    ExplanationStyle,
    MasteryTier,
    SessionStage,
    SessionStatus,
    VoiceState,
)
from tarkyaan.models.learner import LearnerProfile
from tarkyaan.models.practice import PracticeQuestion
from tarkyaan.providers.mock_providers import MockSTTProvider, MockTTSProvider
from tarkyaan.session.session_engine import LearningSessionEngine
from tarkyaan.teaching.teaching_engine import TeachingEngine
from tarkyaan.voice.conversation_controller import VoiceConversationController


@pytest.fixture
def clean_environment():
    store = TarkyaanMemoryStore(":memory:")
    memory = TarkyaanMemoryManager(store=store)
    prof = LearnerProfile(learner_id="nikhil_dsa_learner", display_name="Nikhil", primary_domain="DSA")
    memory.create_learner(prof)
    model = LearnerModel(learner_id=prof.learner_id, memory_manager=memory)
    return memory, model, prof


class TestSection54LearningJourney:
    """
    SECTION 54 FINAL ACCEPTANCE SCENARIO:
    Learner: Nikhil
    Goal: "Become strong at DSA"
    Task: "Understand recursion"
    Tarkyaan starts:
    Learning Session -> checks mastery -> explains recursion at beginner level ->
    asks Socratic question -> learner answers with misconception -> identifies misconception ->
    gives small hint -> learner improves -> practice problem -> evaluates ->
    progressive hint -> learner solves -> collects evidence -> updates Tarkyaan knowledge state ->
    updates mastery through existing MasteryEngine -> summarizes session -> recommends next task.
    """

    def test_complete_section_54_learning_journey(self, clean_environment):
        memory, model, prof = clean_environment

        # 1. Goal & Task Setup
        goal = model.create_goal(title="Become strong at DSA", target_outcome="Master recursive algorithms and trees")
        model.register_topic("recursion", "Recursion", subject_id="dsa", subject_name="Data Structures & Algorithms")

        # 2. Check current mastery (unexplored)
        initial_mastery = model.get_topic_mastery("recursion")
        assert initial_mastery is not None
        assert initial_mastery.mastery_score == 0.0
        assert initial_mastery.tier == MasteryTier.UNEXPLORED

        # 3. Tarkyaan starts Learning Session
        session_engine = LearningSessionEngine(memory_manager=memory, learner_model=model)
        session = session_engine.create_session(
            learner_id=prof.learner_id,
            concept_id="recursion",
            objective="Understand recursion and call stack termination",
            goal_id=goal.goal_id
        )
        assert session.status == SessionStatus.CREATED
        session_engine.start_session(session.session_id)
        active_sess = session_engine.get_session(session.session_id)
        assert active_sess is not None
        assert active_sess.current_stage == SessionStage.TEACH

        # 4. Explains recursion at appropriate level (Beginner / Analogy)
        explanation = session_engine.teaching_engine.explain_concept(
            concept_id="recursion",
            current_mastery=initial_mastery.mastery_score,
            learner=prof
        )
        assert explanation.style_applied == ExplanationStyle.SIMPLE_ANALOGY
        assert "doll" in explanation.analogies[0].lower() or "nesting" in explanation.analogies[0].lower()
        assert len(explanation.key_invariants) >= 1

        # 5. Asks Socratic probe
        probe = session_engine.teaching_engine.probe_understanding("recursion", "Recursion")
        assert probe.concept_id == "recursion"
        assert "base case" in probe.target_insight.lower() or "stopping" in probe.target_insight.lower()

        # 6. Learner answers demonstrating a misconception
        struggling_answer = "Functions will naturally stop when the numbers reach zero or run out without base case."
        probe_eval = session_engine.teaching_engine.evaluate_socratic_response(probe, struggling_answer)
        assert probe_eval["achieved_insight"] is False

        # 7. Identifies misconception and delivers cognitive intervention
        intervention = session_engine.teaching_engine.remediate_misconception("recursion", struggling_answer)
        assert intervention.misconception_id == "recursion_no_base_case"
        assert "base case" in intervention.correct_mental_model.lower()
        assert len(intervention.counterexample) > 10
        assert len(intervention.correct_mental_model) > 10

        # 8. Learner receives small hint and reasons again with improved understanding
        improved_answer = "Every recursive function must have an explicit base case that stops new calls and returns a value."
        probe_eval_2 = session_engine.teaching_engine.evaluate_socratic_response(probe, improved_answer)
        assert probe_eval_2["achieved_insight"] is True

        # 9. Transition to PRACTICE stage
        session_engine.transition_stage(session.session_id, SessionStage.PRACTICE, "Concept understood, moving to application.")
        practice_q = session_engine.present_practice_question(session.session_id, difficulty=2)
        assert practice_q.concept_id == "recursion"
        assert practice_q.difficulty == 2

        # 10. Learner requests progressive hint on practice problem
        hint = session_engine.request_hint_for_active_question(session.session_id, question_id=practice_q.question_id)
        assert hint.hint_level.value == 1  # Tier 1 Nudge
        assert len(hint.hint_text) > 5

        # 11. Learner solves practice problem
        solution_resp = (
            "def sum_to_n(n):\n"
            "    if n <= 1:\n"
            "        return n\n"
            "    return n + sum_to_n(n - 1)"
        )
        answer_eval = session_engine.submit_answer(session.session_id, practice_q.question_id, solution_resp)
        assert answer_eval.is_correct is True
        assert answer_eval.score >= 0.80

        # 12. Verification question & Complete Session
        session_engine.transition_stage(session.session_id, SessionStage.ASSESS, "Verification assessment.")
        session_engine.transition_stage(session.session_id, SessionStage.REVIEW, "Reviewing outcomes.")

        summary = session_engine.complete_session(session.session_id)

        # 13. Verifies honest session summary
        assert summary.session_id == session.session_id
        assert summary.learner_id == prof.learner_id
        assert summary.questions_correct >= 1
        assert summary.hints_requested == 1
        assert len(summary.mastery_changes) == 1

        # 14. Verifies mastery update occurred through existing Phase 1 MasteryEngine
        updated_mastery = model.get_topic_mastery("recursion")
        assert updated_mastery is not None
        assert updated_mastery.mastery_score > 0.0
        assert updated_mastery.uncertainty < 1.0
        assert updated_mastery.tier in (MasteryTier.INTRODUCED, MasteryTier.PRACTICING)
        assert summary.recommended_next_action != ""


class TestSection55VoiceAcceptanceScenario:
    """
    SECTION 55 VOICE ACCEPTANCE SCENARIO:
    User says: "Hey Tarkyaan, teach me binary search."
    VOICE -> STT -> context -> learner state -> task -> session start -> teach ->
    voice response -> question -> listen -> evaluate -> continue.
    Then: "Give me a hint." -> Understands active problem.
    Then: "Stop." -> TTS stops.
    Then: "Resume." -> Session continues.
    Then: "Make it harder." -> Practice difficulty adapts.
    """

    def test_voice_acceptance_scenario(self, clean_environment):
        memory, model, prof = clean_environment
        model.register_topic("binary_search", "Binary Search")

        session_engine = LearningSessionEngine(memory_manager=memory, learner_model=model)
        stt = MockSTTProvider()
        tts = MockTTSProvider()
        caps = CapabilityRegistry()

        controller = VoiceConversationController(
            stt_provider=stt,
            tts_provider=tts,
            session_engine=session_engine,
            capability_registry=caps,
            learner_id=prof.learner_id
        )

        # 1. User says: "Hey Tarkyaan, teach me binary search."
        resp1 = controller.process_transcript("Hey Tarkyaan, teach me binary search")
        assert "binary search" in resp1.lower()
        assert controller.active_session is not None
        assert controller.active_session.concept_id == "binary_search"

        # 2. User says: "Test me on this."
        resp2 = controller.process_transcript("Test me on this")
        assert "practice problem" in resp2.lower() or "?" in resp2
        assert len(controller.active_session.questions_asked) >= 1

        # 3. User says: "Give me a hint."
        resp3 = controller.process_transcript("Give me a hint")
        assert "Hint:" in resp3
        assert controller.active_session.hints_used >= 1

        # 4. User says: "Stop."
        resp4 = controller.process_transcript("Stop")
        assert "Stopped" in resp4
        assert controller.state == VoiceState.IDLE

        # 5. User says: "Resume."
        resp5 = controller.process_transcript("Resume")
        assert "Resuming" in resp5

        # 6. User says: "Make it harder."
        resp6 = controller.process_transcript("Make it harder")
        assert "Level 3" in resp6 or "increased" in resp6.lower()
        assert controller.context_resolver.current_difficulty == 3
