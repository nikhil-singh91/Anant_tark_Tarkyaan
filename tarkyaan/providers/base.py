"""
Unified Provider Abstractions for Tarkyaan.
Decouples external AI, search, voice, and cloud services from core learning logic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ProviderType(str, Enum):
    """Broad categories of external service providers."""
    LLM = "llm"
    SEARCH = "search"
    STT = "stt"
    TTS = "tts"
    TOOL = "tool"


class ProviderHealth(BaseModel):
    """Health and readiness diagnostic for a provider."""
    provider_name: str
    provider_type: ProviderType
    is_available: bool
    status_message: str = "ok"
    latency_ms: Optional[float] = None


class BaseProvider(ABC):
    """Abstract contract that every concrete provider must fulfill."""

    def __init__(self, name: str, provider_type: ProviderType) -> None:
        self.name = name
        self.provider_type = provider_type
        self._is_initialized = False

    @abstractmethod
    def initialize(self) -> None:
        """Connect or configure provider client."""
        pass

    @abstractmethod
    def health_check(self) -> ProviderHealth:
        """Test provider connectivity and credentials."""
        pass

    def shutdown(self) -> None:
        """Gracefully release client resources."""
        self._is_initialized = False


class LLMProvider(BaseProvider):
    """Abstract interface for large language model reasoning providers."""

    def __init__(self, name: str) -> None:
        super().__init__(name=name, provider_type=ProviderType.LLM)

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """Generate structured text response from the model."""
        pass


class VoiceSTTProvider(BaseProvider):
    """Abstract interface for speech-to-text audio transcription."""

    def __init__(self, name: str) -> None:
        super().__init__(name=name, provider_type=ProviderType.STT)

    @abstractmethod
    def transcribe(self, audio_data: bytes, language: str = "auto") -> str:
        """Transcribe speech audio data into text."""
        pass


class VoiceTTSProvider(BaseProvider):
    """Abstract interface for text-to-speech audio synthesis."""

    def __init__(self, name: str) -> None:
        super().__init__(name=name, provider_type=ProviderType.TTS)

    @abstractmethod
    def synthesize(self, text: str, voice: str = "hi-IN-SwaraNeural") -> bytes:
        """Synthesize natural voice audio from text."""
        pass
