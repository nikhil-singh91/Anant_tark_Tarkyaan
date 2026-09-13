"""
Unit and Integration Tests for Tarkyaan Advanced Voice Companion Subsystem (Phase 5).
Verifies local command recognition, wake word normalization, barge-in interruption,
context resolution, voice-driven learning sessions, and capability routing.
"""

import pytest
from tarkyaan.capabilities.registry import CapabilityRegistry
from tarkyaan.events.event_bus import TarkyaanEvent, event_bus
from tarkyaan.learner.learner_model import LearnerModel
from tarkyaan.memory.memory_manager import TarkyaanMemoryManager
from tarkyaan.memory.memory_store import TarkyaanMemoryStore
from tarkyaan.models.enums import VoiceIntent, VoiceState
from tarkyaan.models.learner import LearnerProfile
from tarkyaan.providers.mock_providers import MockSTTProvider, MockTTSProvider
from tarkyaan.session.session_engine import LearningSessionEngine
from tarkyaan.voice.command_recognizer import VoiceCommandRecognizer
from tarkyaan.voice.context_resolver import VoiceContextResolver
from tarkyaan.voice.conversation_controller import VoiceConversationController


class TestVoiceCommandRecognizer:
    def test_interruption_and_cancellation_intents(self):
        phrases = [
            ("stop", VoiceIntent.INTERRUPT),
            ("wait a second", VoiceIntent.INTERRUPT),
            ("hold on", VoiceIntent.INTERRUPT),
            ("never mind", VoiceIntent.INTERRUPT),
            ("cancel that", VoiceIntent.INTERRUPT),
            ("रुको", VoiceIntent.INTERRUPT),
            ("रहने दो", VoiceIntent.INTERRUPT),
            ("बस करो", VoiceIntent.INTERRUPT),
        ]
        for phrase, expected_intent in phrases:
            intent, _ = VoiceCommandRecognizer.recognize_intent(phrase)
            assert intent == expected_intent, f"Failed for phrase: '{phrase}'"

    def test_pedagogical_and_control_intents(self):
        assert VoiceCommandRecognizer.recognize_intent("pause")[0] == VoiceIntent.PAUSE
        assert VoiceCommandRecognizer.recognize_intent("resume")[0] == VoiceIntent.RESUME
        assert VoiceCommandRecognizer.recognize_intent("give me a hint")[0] == VoiceIntent.GIVE_HINT
        assert VoiceCommandRecognizer.recognize_intent("show me the answer")[0] == VoiceIntent.SHOW_ANSWER
        assert VoiceCommandRecognizer.recognize_intent("explain it simply")[0] == VoiceIntent.EXPLAIN_SIMPLY
        assert VoiceCommandRecognizer.recognize_intent("explain deeply")[0] == VoiceIntent.EXPLAIN_DEEPLY
        assert VoiceCommandRecognizer.recognize_intent("make it harder")[0] == VoiceIntent.MAKE_HARDER
        assert VoiceCommandRecognizer.recognize_intent("make it easier")[0] == VoiceIntent.MAKE_EASIER

    def test_wake_word_stripping_and_concept_extraction(self):
        intent, arg = VoiceCommandRecognizer.recognize_intent("Hey Tarkyaan teach me recursion")
        assert intent == VoiceIntent.TEACH_CONCEPT
        assert arg == "recursion"

        intent2, arg2 = VoiceCommandRecognizer.recognize_intent("Tarkyaan search for dynamic programming")
        assert intent2 == VoiceIntent.RUN_CAPABILITY
        assert arg2 == "dynamic programming"


class TestVoiceContextResolver:
    def test_anaphoric_reference_resolution(self):
        resolver = VoiceContextResolver()
        resolver.update_context(concept_id="binary_search", difficulty=2)

        # "it" refers to binary_search
        assert resolver.resolve_concept("Explain it simply") == "binary_search"
        assert resolver.resolve_concept("Make it harder") == "binary_search"

        # Explicit concept updates context
        assert resolver.resolve_concept("Teach me recursion", "recursion") == "recursion"
        assert resolver.resolve_concept("Show an example of this") == "recursion"

    def test_difficulty_stepping(self):
        resolver = VoiceContextResolver()
        assert resolver.current_difficulty == 2
        assert resolver.adjust_difficulty("up") == 3
        assert resolver.adjust_difficulty("up") == 4
        assert resolver.adjust_difficulty("down") == 3


class TestVoiceConversationController:
    @pytest.fixture
    def setup_controller(self):
        store = TarkyaanMemoryStore(":memory:")
        memory = TarkyaanMemoryManager(store=store)
        prof = LearnerProfile(learner_id="voice_test_learner", display_name="Nikhil")
        memory.create_learner(prof)
        model = LearnerModel(learner_id=prof.learner_id, memory_manager=memory)

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
        return controller

    def test_barge_in_interruption_halts_speaking(self, setup_controller):
        controller = setup_controller
        controller.state = VoiceState.SPEAKING

        # Learner barges in
        controller.interrupt()
        assert controller.state == VoiceState.INTERRUPTED
        assert controller.is_speaking() is False

    def test_voice_driven_session_teaching_flow(self, setup_controller):
        controller = setup_controller

        # Step 1: User asks to teach binary search
        response = controller.process_transcript("Hey Tarkyaan teach me binary search")
        assert "Binary Search" in response or "binary search" in response.lower()
        assert controller.active_session is not None
        assert controller.active_session.concept_id == "binary_search"

        # Step 2: User requests practice question
        q_resp = controller.process_transcript("Test me on this")
        assert "practice problem" in q_resp.lower() or "?" in q_resp

        # Step 3: User requests progressive hint
        hint_resp = controller.process_transcript("Give me a hint")
        assert "Hint:" in hint_resp

        # Step 4: User requests harder problem
        harder_resp = controller.process_transcript("Make it harder")
        assert "Level 3" in harder_resp

        # Step 5: User pauses session
        pause_resp = controller.process_transcript("Pause")
        assert "Paused" in pause_resp
        assert controller.state == VoiceState.PAUSED

        # Step 6: User resumes session
        resume_resp = controller.process_transcript("Resume")
        assert "Resuming" in resume_resp

        # Step 7: User interrupts / stops
        stop_resp = controller.process_transcript("Stop")
        assert "Stopped" in stop_resp
        assert controller.state == VoiceState.IDLE

    def test_voice_event_bus_synchronization(self, setup_controller):
        controller = setup_controller
        captured_events = []

        def event_handler(envelope):
            captured_events.append(envelope.event)

        event_bus.subscribe(TarkyaanEvent.VOICE_SPEAKING_STARTED, event_handler)
        event_bus.subscribe(TarkyaanEvent.VOICE_SPEAKING_FINISHED, event_handler)
        event_bus.subscribe(TarkyaanEvent.USER_INPUT_RECEIVED, event_handler)

        controller.process_transcript("Hello Tarkyaan")

        assert TarkyaanEvent.USER_INPUT_RECEIVED in captured_events
        assert TarkyaanEvent.VOICE_SPEAKING_STARTED in captured_events
        assert TarkyaanEvent.VOICE_SPEAKING_FINISHED in captured_events

        event_bus.clear()

    def test_voice_capability_routing(self, setup_controller):
        controller = setup_controller
        reply = controller.process_transcript("Search for binary search tutorials")
        assert "researched" in reply.lower() or "research" in reply.lower()
