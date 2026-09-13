"""Tests for Tarkyaan Provider Manager and Mock Providers."""

import pytest
from tarkyaan.providers.base import (
    BaseProvider,
    LLMProvider,
    ProviderHealth,
    ProviderType,
    VoiceSTTProvider,
    VoiceTTSProvider,
)
from tarkyaan.providers.manager import ProviderManager, provider_manager
from tarkyaan.providers.mock_providers import (
    MockLLMProvider,
    MockVoiceSTTProvider,
    MockVoiceTTSProvider,
)


def test_provider_registration_and_retrieval():
    """Test registering LLM, STT, and TTS providers and retrieving by type."""
    mgr = ProviderManager()
    llm = MockLLMProvider("cerebras_llama")
    stt = MockVoiceSTTProvider("whisper_local")
    tts = MockVoiceTTSProvider("elevenlabs_neural")

    mgr.register(llm, is_default=True)
    mgr.register(stt, is_default=True)
    mgr.register(tts, is_default=True)

    assert mgr.get("cerebras_llama") == llm
    assert mgr.get_default(ProviderType.LLM) == llm
    assert mgr.get_default(ProviderType.STT) == stt
    assert mgr.get_default(ProviderType.TTS) == tts
    assert len(mgr.list_providers()) == 3


def test_mock_llm_generation():
    """Verify deterministic mock LLM generation."""
    llm = MockLLMProvider()
    llm.initialize()
    health = llm.health_check()
    assert health.is_available is True

    response = llm.generate("Explain recursion in dynamic programming")
    assert "MOCK_LLM_RESPONSE" in response
    assert llm.last_prompt == "Explain recursion in dynamic programming"


def test_mock_voice_stt_and_tts():
    """Verify mock STT transcription and TTS audio synthesis."""
    stt = MockVoiceSTTProvider()
    tts = MockVoiceTTSProvider()

    transcription = stt.transcribe(b"fake_audio_bytes")
    assert "Explain binary search" in transcription

    audio = tts.synthesize("Welcome back to Tarkyaan")
    assert isinstance(audio, bytes)
    assert len(audio) > 0


def test_provider_manager_health_checks():
    """Verify health checks across multiple providers."""
    mgr = ProviderManager()
    llm = MockLLMProvider("llm_primary")
    tts = MockVoiceTTSProvider("tts_primary")
    mgr.register(llm)
    mgr.register(tts)

    health_map = mgr.check_health_all()
    assert "llm_primary" in health_map
    assert health_map["llm_primary"].is_available is True
    assert "tts_primary" in health_map
    assert health_map["tts_primary"].is_available is True
