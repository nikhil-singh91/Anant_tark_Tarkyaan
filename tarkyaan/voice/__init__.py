"""
Tarkyaan Voice Subsystem (Phase 5).
Real-time AI learning companion voice architecture.
"""

from tarkyaan.models.enums import VoiceIntent, VoiceState
from tarkyaan.voice.command_recognizer import VoiceCommandRecognizer
from tarkyaan.voice.context_resolver import VoiceContextResolver
from tarkyaan.voice.conversation_controller import VoiceConversationController

# Backwards compatible alias and models
from pydantic import BaseModel, Field


class VoiceDialogueTurn(BaseModel):
    """Transcript and timing of a single voice exchange."""
    user_transcript: str
    companion_response: str
    detected_language: str = "en"
    duration_seconds: float = Field(default=0.0, ge=0.0)


class VoiceManager(VoiceConversationController):
    """Orchestrator alias for backwards compatibility."""
    pass


__all__ = [
    "VoiceCommandRecognizer",
    "VoiceContextResolver",
    "VoiceConversationController",
    "VoiceDialogueTurn",
    "VoiceIntent",
    "VoiceManager",
    "VoiceState",
]
