"""Tests for Tarkyaan Vision and Image Understanding Subsystem."""

from __future__ import annotations

import pytest

from tarkyaan.models.enums import MultimodalInputType
from tarkyaan.multimodal.input_engine import MultimodalInputEngine
from tarkyaan.vision.gemini_provider import GeminiVisionProvider
from tarkyaan.vision.image_understanding import ImageUnderstandingEngine, ProblemExtraction
from tarkyaan.vision.mock_provider import MockVisionProvider
from tarkyaan.vision.provider import VisionResult


def test_mock_vision_provider_operations():
    """Verify MockVisionProvider returns structured, deterministic perception results."""
    provider = MockVisionProvider(default_text="def two_sum(nums, target):\n    pass\n")
    res: VisionResult = provider.analyze_image(b"fake_image_bytes")
    assert res.success is True
    assert "code" in res.detected_labels
    assert res.confidence >= 0.9

    text = provider.extract_text(b"fake_image_bytes")
    assert "two_sum" in text

    diag = provider.understand_diagram(b"fake_diagram_bytes")
    assert diag.success is True
    assert diag.diagram_type == "flowchart"


def test_mock_vision_provider_error_handling():
    """Verify vision provider handles simulated failures gracefully without crashing."""
    provider = MockVisionProvider(simulate_error=True, error_message="Camera sensor malfunction")
    res = provider.analyze_image(b"bytes")
    assert res.success is False
    assert "Camera sensor malfunction" in str(res.error)

    code_res = provider.analyze_code_image(b"bytes")
    assert code_res.success is False
    assert "Camera sensor malfunction" in str(code_res.error)


def test_gemini_vision_provider_unconfigured_fallback():
    """Verify GeminiVisionProvider fails gracefully with informative error when API key is missing."""
    gemini = GeminiVisionProvider(api_key="")
    assert gemini.is_available() is False
    res = gemini.analyze_image(b"test")
    assert res.success is False
    assert "GEMINI_API_KEY is not configured" in str(res.error)


def test_image_understanding_problem_extraction():
    """Verify ImageUnderstandingEngine extracts problem, code, error, and Socratic prompt."""
    custom_snippet = "while low <= high:\n    mid = (low + high) // 2\n    # Missing pointer update\nIndexError: list index out of range"
    provider = MockVisionProvider(default_text=custom_snippet)
    engine = ImageUnderstandingEngine(provider=provider)

    problem: ProblemExtraction = engine.extract_problem_from_image(b"fake_screenshot")
    assert problem.target_topic == "binary_search"
    assert "IndexError" in str(problem.error_context)
    assert "IndexError" in problem.recommended_socratic_prompt
    assert "boundary_off_by_one" in problem.identified_misconceptions


def test_multimodal_input_engine_normalization():
    """Verify MultimodalInputEngine normalizes diverse input channels into unified models."""
    engine = MultimodalInputEngine()

    # 1. Text input
    inp_text = engine.process_text_input(learner_id="lrn_001", text="Explain quicksort")
    assert inp_text.primary_type == MultimodalInputType.TEXT
    assert inp_text.text_content == "Explain quicksort"

    # 2. Voice input
    inp_voice = engine.process_voice_input(
        learner_id="lrn_001",
        transcript="Why is merge sort stable?",
        audio_duration_seconds=2.8,
    )
    assert inp_voice.primary_type == MultimodalInputType.VOICE
    assert inp_voice.voice_transcript == "Why is merge sort stable?"
    assert inp_voice.metadata["audio_duration_seconds"] == 2.8

    # 3. Image input
    inp_img = engine.process_image_input(
        learner_id="lrn_001",
        image_path_or_bytes=b"png_data",
        accompanying_text="What is wrong with my binary search?",
    )
    assert inp_img.primary_type == MultimodalInputType.IMAGE
    assert inp_img.extracted_problem is not None
    assert inp_img.extracted_problem.target_topic == "binary_search"
