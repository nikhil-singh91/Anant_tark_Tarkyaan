"""
Tarkyaan Voice Subsystem Architecture (Category B: Architecture & Interface Now).
Defines contracts for speech recognition, neural synthesis, and continuous dialogue.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class VoiceState(str, Enum):
    """Lifecycle states of the voice conversation engine."""
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    INTERRUPTED = "interrupted"


class VoiceDialogueTurn(BaseModel):
    """Transcript and timing of a single voice exchange."""
    user_transcript: str
    companion_response: str
    detected_language: str = "en"
    duration_seconds: float = Field(default=0.0, ge=0.0)


class VoiceManager:
    """
    Orchestrator interface for Voice Activity Detection, ASR, and TTS.
    Implementation will connect to Whisper and EdgeTTS/ElevenLabs in Phase 5.
    """

    def __init__(self) -> None:
        self.state: VoiceState = VoiceState.IDLE
        self.active_voice: str = "hi-IN-SwaraNeural"

    def is_listening(self) -> bool:
        return self.state == VoiceState.LISTENING

    def is_speaking(self) -> bool:
        return self.state == VoiceState.SPEAKING

    def interrupt(self) -> None:
        """Interrupt active speech synthesis immediately."""
        self.state = VoiceState.INTERRUPTED
