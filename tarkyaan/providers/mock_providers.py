"""
Deterministic Mock Providers for Tarkyaan Unit Testing and Offline Mode.
"""

from __future__ import annotations

from typing import Optional
from tarkyaan.providers.base import LLMProvider, ProviderHealth, ProviderType, VoiceSTTProvider, VoiceTTSProvider


class MockLLMProvider(LLMProvider):
    """Deterministic LLM mock returning controlled educational responses."""

    def __init__(self, name: str = "mock_llm") -> None:
        super().__init__(name=name)
        self.last_prompt: Optional[str] = None

    def initialize(self) -> None:
        self._is_initialized = True

    def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            provider_name=self.name,
            provider_type=ProviderType.LLM,
            is_available=True,
            status_message="Mock LLM ready"
        )

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        self.last_prompt = prompt
        return f"[MOCK_LLM_RESPONSE for: {prompt[:30]}...]"


class MockVoiceSTTProvider(VoiceSTTProvider):
    """Mock STT provider for voice transcription tests."""

    def __init__(self, name: str = "mock_stt") -> None:
        super().__init__(name=name)

    def initialize(self) -> None:
        self._is_initialized = True

    def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            provider_name=self.name,
            provider_type=ProviderType.STT,
            is_available=True,
            status_message="Mock STT ready"
        )

    def transcribe(self, audio_data: bytes, language: str = "auto") -> str:
        return "Explain binary search invariants"


class MockVoiceTTSProvider(VoiceTTSProvider):
    """Mock TTS provider for voice synthesis tests."""

    def __init__(self, name: str = "mock_tts") -> None:
        super().__init__(name=name)

    def initialize(self) -> None:
        self._is_initialized = True

    def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            provider_name=self.name,
            provider_type=ProviderType.TTS,
            is_available=True,
            status_message="Mock TTS ready"
        )

    def synthesize(self, text: str, voice: str = "hi-IN-SwaraNeural") -> bytes:
        return b"RIFFmockwavheaderdata"
