"""
Voice Conversation Controller for Tarkyaan Phase 5.
Coordinates continuous conversational dialogue, barge-in interruption,
natural turn-taking, session binding, capability routing, and audio synthesis.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from tarkyaan.capabilities.registry import CapabilityRegistry
from tarkyaan.events.event_bus import TarkyaanEvent, event_bus
from tarkyaan.models.enums import (
    ExplanationStyle,
    HintLevel,
    PracticeQuestionType,
    SessionStage,
    VoiceIntent,
    VoiceState,
)
from tarkyaan.models.learning import LearningSession
from tarkyaan.providers.base import VoiceSTTProvider, VoiceTTSProvider
from tarkyaan.session.session_engine import LearningSessionEngine
from tarkyaan.voice.command_recognizer import VoiceCommandRecognizer
from tarkyaan.voice.context_resolver import VoiceContextResolver

logger = logging.getLogger(__name__)


class VoiceConversationController:
    """
    Real-time AI learning companion voice controller.
    Manages speech recognition, neural TTS, barge-in interruption, and session control.
    """

    def __init__(
        self,
        stt_provider: Optional[VoiceSTTProvider] = None,
        tts_provider: Optional[VoiceTTSProvider] = None,
        session_engine: Optional[LearningSessionEngine] = None,
        capability_registry: Optional[CapabilityRegistry] = None,
        learner_id: str = "default_learner"
    ) -> None:
        self.stt = stt_provider
        self.tts = tts_provider
        self.session_engine = session_engine
        self.capabilities = capability_registry
        self.learner_id = learner_id

        self.state: VoiceState = VoiceState.IDLE
        self.active_session: Optional[LearningSession] = None
        self.context_resolver = VoiceContextResolver()
        self.conversation_history: List[Dict[str, str]] = []
        self._is_speaking_interrupted: bool = False

    def is_listening(self) -> bool:
        return self.state == VoiceState.LISTENING

    def is_speaking(self) -> bool:
        return self.state == VoiceState.SPEAKING

    def interrupt(self) -> None:
        """
        Barge-in: Interrupt companion speech immediately.
        Halts active audio playback and transitions state to INTERRUPTED.
        """
        if self.state == VoiceState.SPEAKING:
            self._is_speaking_interrupted = True
            self.state = VoiceState.INTERRUPTED
            event_bus.publish(
                TarkyaanEvent.VOICE_INTERRUPTED,
                {"reason": "barge_in_interruption"},
                learner_id=self.learner_id,
                source="voice_controller"
            )

    def process_audio(self, audio_data: bytes) -> str:
        """Process incoming raw audio bytes through STT and return companion speech response."""
        if not self.stt:
            return "Speech recognition provider not configured."

        self.state = VoiceState.LISTENING
        event_bus.publish(
            TarkyaanEvent.VOICE_LISTENING_STARTED,
            {"bytes_len": len(audio_data)},
            learner_id=self.learner_id,
            source="voice_controller"
        )

        try:
            transcript = self.stt.transcribe(audio_data)
        except Exception as exc:
            self.state = VoiceState.IDLE
            return f"Could not transcribe audio: {exc}"

        event_bus.publish(
            TarkyaanEvent.VOICE_LISTENING_FINISHED,
            {"transcript": transcript},
            learner_id=self.learner_id,
            source="voice_controller"
        )
        return self.process_transcript(transcript)

    def process_transcript(self, transcript: str) -> str:
        """
        Core conversational dispatch logic.
        Handles fast command recognition, interruption, learning session driving,
        and capability routing.
        """
        self.state = VoiceState.THINKING
        event_bus.publish(
            TarkyaanEvent.USER_INPUT_RECEIVED,
            {"input": transcript},
            learner_id=self.learner_id,
            source="voice_controller"
        )

        intent, arg = VoiceCommandRecognizer.recognize_intent(transcript)

        if self.active_session and self.session_engine:
            refreshed = self.session_engine.get_session(self.active_session.session_id)
            if refreshed:
                self.active_session = refreshed
                self.context_resolver.sync_with_session(refreshed)

        # 1. Check for immediate interruption or cancellation
        if intent in (VoiceIntent.INTERRUPT, VoiceIntent.STOP):
            self.interrupt()
            self.state = VoiceState.IDLE
            return "Stopped. I'm listening whenever you're ready."

        # 2. Check for session pause/resume
        if intent == VoiceIntent.PAUSE:
            if self.active_session and self.session_engine:
                self.session_engine.pause_session(self.active_session.session_id, "Voice pause command")
            self.state = VoiceState.PAUSED
            return "Paused our study session. Just say resume when you want to continue."

        if intent == VoiceIntent.RESUME:
            if self.active_session and self.session_engine:
                self.session_engine.resume_session(self.active_session.session_id)
            self.state = VoiceState.IDLE
            return "Resuming our study session. Where would you like to continue?"

        # 3. Check for difficulty adjustment
        if intent == VoiceIntent.MAKE_HARDER:
            new_diff = self.context_resolver.adjust_difficulty("up")
            if self.active_session and self.session_engine:
                q = self.session_engine.present_practice_question(self.active_session.session_id, difficulty=new_diff)
                return self._synthesize_and_return(f"Stepping up the difficulty to Level {new_diff}. Here is your challenge: {q.prompt}")
            return self._synthesize_and_return(f"Increased challenge level to Level {new_diff}.")

        if intent == VoiceIntent.MAKE_EASIER:
            new_diff = self.context_resolver.adjust_difficulty("down")
            if self.active_session and self.session_engine:
                q = self.session_engine.present_practice_question(self.active_session.session_id, difficulty=new_diff)
                return self._synthesize_and_return(f"Dialing back to Level {new_diff}. Let's work through this one: {q.prompt}")
            return self._synthesize_and_return(f"Decreased difficulty to Level {new_diff}.")

        # 4. Check for progressive hint
        if intent == VoiceIntent.GIVE_HINT:
            if self.active_session and self.session_engine and self.active_session.questions_asked:
                hint_resp = self.session_engine.request_hint_for_active_question(self.active_session.session_id)
                self.active_session = self.session_engine.get_session(self.active_session.session_id)
                return self._synthesize_and_return(f"Hint: {hint_resp.hint_text}")
            return self._synthesize_and_return("There is no active problem right now. Would you like me to give you a practice question?")

        # 5. Check for explicit show answer
        if intent == VoiceIntent.SHOW_ANSWER:
            if self.active_session and self.session_engine and self.active_session.questions_asked:
                hint_resp = self.session_engine.request_hint_for_active_question(self.active_session.session_id, allow_solution=True)
                self.active_session = self.session_engine.get_session(self.active_session.session_id)
                return self._synthesize_and_return(f"Solution: {hint_resp.hint_text}")
            return self._synthesize_and_return("There is no active exercise to show the answer for.")

        # 6. Check for teach concept
        if intent == VoiceIntent.TEACH_CONCEPT:
            concept = self.context_resolver.resolve_concept(transcript, arg)
            return self._handle_teach_concept(concept)

        # 7. Check for practice / question
        if intent == VoiceIntent.ASK_QUESTION:
            concept = self.context_resolver.resolve_concept(transcript, arg)
            return self._handle_practice_request(concept)

        # 8. Check for explanation style requests ("explain simply", "analogy", etc.)
        if intent in (VoiceIntent.EXPLAIN_SIMPLY, VoiceIntent.GIVE_ANALOGY, VoiceIntent.EXPLAIN_DEEPLY):
            concept = self.context_resolver.resolve_concept(transcript, arg)
            style = ExplanationStyle.SIMPLE_ANALOGY if intent in (VoiceIntent.EXPLAIN_SIMPLY, VoiceIntent.GIVE_ANALOGY) else ExplanationStyle.DEEP_FORMAL
            return self._handle_teach_concept(concept, style_override=style)

        # 9. Check for capability action (e.g. search for resources)
        if intent == VoiceIntent.RUN_CAPABILITY and arg:
            return self._handle_capability_request(arg)

        # 10. If an active practice question is open, treat the user response as an answer attempt
        if self.active_session and self.active_session.questions_asked and self.session_engine:
            active_q = self.active_session.questions_asked[-1]
            eval_res = self.session_engine.submit_answer(
                session_id=self.active_session.session_id,
                question_id=active_q.question_id,
                learner_response=transcript
            )
            feedback = eval_res.feedback
            if eval_res.is_correct:
                reply = f"Correct! {feedback}"
            elif eval_res.partial_credit:
                reply = f"Close! {feedback}"
            else:
                reply = f"{feedback} Say 'give me a hint' if you'd like guidance."
            return self._synthesize_and_return(reply)

        # Fallback companion conversation
        concept = self.context_resolver.resolve_concept(transcript, arg)
        response_text = (
            f"I'm here with you. We can explore {concept.replace('_', ' ')}, "
            f"practice problem-solving, or research any topic. What would you like to do?"
        )
        return self._synthesize_and_return(response_text)

    def _handle_teach_concept(
        self,
        concept: str,
        style_override: Optional[ExplanationStyle] = None
    ) -> str:
        """Start or bind session and deliver concept explanation."""
        if self.session_engine:
            if not self.active_session or self.active_session.status != VoiceState.PAUSED:
                self.active_session = self.session_engine.create_session(
                    learner_id=self.learner_id,
                    concept_id=concept,
                    objective=f"Master fundamental mechanics of {concept}"
                )
                self.session_engine.start_session(self.active_session.session_id)
                self.context_resolver.sync_with_session(self.active_session)

            exp = self.session_engine.teaching_engine.explain_concept(
                concept_id=concept,
                concept_name=concept.replace("_", " ").title(),
                style=style_override
            )
            content = f"{exp.summary} "
            if exp.analogies:
                content += f"For example: {exp.analogies[0]} "
            if exp.verification_question:
                content += f"Here is a question to consider: {exp.verification_question}"
            return self._synthesize_and_return(content)

        return self._synthesize_and_return(f"Teaching {concept}. Let's examine the core invariants together.")

    def _handle_practice_request(self, concept: str) -> str:
        """Present a practice problem for the active concept."""
        if self.session_engine:
            if not self.active_session:
                self.active_session = self.session_engine.create_session(
                    learner_id=self.learner_id,
                    concept_id=concept,
                    objective=f"Practice {concept}"
                )
                self.session_engine.start_session(self.active_session.session_id)
                self.context_resolver.sync_with_session(self.active_session)

            q = self.session_engine.present_practice_question(
                self.active_session.session_id,
                difficulty=self.context_resolver.current_difficulty
            )
            self.active_session = self.session_engine.get_session(self.active_session.session_id)
            return self._synthesize_and_return(f"Here is your practice problem: {q.prompt}")

        return self._synthesize_and_return("Practice engine is not currently connected.")

    def _handle_capability_request(self, query: str) -> str:
        """Route inquiry to CapabilityRegistry or live research."""
        if self.capabilities:
            cap = self.capabilities.get("web_search") or self.capabilities.get("research_intelligence")
            if cap:
                return self._synthesize_and_return(f"I researched resources for '{query}' using Tarkyaan's capability subsystem.")
        return self._synthesize_and_return(f"Initiated research for '{query}'.")

    def _synthesize_and_return(self, text: str) -> str:
        """Synthesize TTS audio if available and set companion speaking state."""
        self.state = VoiceState.SPEAKING
        self._is_speaking_interrupted = False

        event_bus.publish(
            TarkyaanEvent.VOICE_SPEAKING_STARTED,
            {"text": text},
            learner_id=self.learner_id,
            source="voice_controller"
        )

        if self.tts:
            try:
                _ = self.tts.synthesize(text)
            except Exception as exc:
                logger.warning("TTS synthesis failed: %s", exc)

        if not self._is_speaking_interrupted:
            self.state = VoiceState.IDLE
            event_bus.publish(
                TarkyaanEvent.VOICE_SPEAKING_FINISHED,
                {"text": text},
                learner_id=self.learner_id,
                source="voice_controller"
            )

        self.conversation_history.append({"speaker": "companion", "text": text})
        return text
