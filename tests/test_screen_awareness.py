"""Tests for Screen Awareness, Permission Guards, and OCR Redaction."""

from __future__ import annotations

import pytest

from tarkyaan.safety.permissions import PermissionCategory, PermissionManager
from tarkyaan.vision.mock_provider import MockVisionProvider
from tarkyaan.vision.screen_capture import ScreenCaptureProvider, ScreenCaptureResult
from tarkyaan.vision.screen_understanding import ScreenContext, ScreenUnderstandingEngine


def test_screen_capture_permission_denied():
    """Verify screen capture is blocked when SCREEN_RECORDING permission is not granted."""
    perms = PermissionManager()
    # Revoke or leave undetermined
    perms.revoke(PermissionCategory.SCREEN_RECORDING)

    cap_provider = ScreenCaptureProvider(perms=perms, mock_mode=True)
    res: ScreenCaptureResult = cap_provider.capture_screen()
    assert res.success is False
    assert "Screen Recording permission is not granted" in str(res.error)


def test_screen_capture_with_permission_granted():
    """Verify screen capture succeeds in mock mode when explicit permission is granted."""
    perms = PermissionManager()
    perms.grant(PermissionCategory.SCREEN_RECORDING, rationale="User approved screen inspection")

    cap_provider = ScreenCaptureProvider(perms=perms, mock_mode=True)
    res: ScreenCaptureResult = cap_provider.capture_screen()
    assert res.success is True
    assert res.width == 1920
    assert res.height == 1080
    assert res.image_bytes is not None


def test_secret_redaction_from_screen_text():
    """Verify passwords, OpenAI keys, and Bearer tokens are sanitized from screen OCR."""
    raw_ocr = (
        "def connect():\n"
        "    api_key = 'sk-1234567890abcdef1234567890abcdef'\n"
        "    password = 'super_secret_password'\n"
        "    token = 'Bearer abc123def456ghi789jkl012'\n"
    )
    sanitized = ScreenCaptureProvider.redact_secrets_from_text(raw_ocr)
    assert "sk-1234567890" not in sanitized
    assert "[REDACTED_API_KEY]" in sanitized
    assert "super_secret_password" not in sanitized
    assert "Bearer [REDACTED_TOKEN]" in sanitized


def test_screen_understanding_engine_observes_ide():
    """Verify ScreenUnderstandingEngine builds educational screen context."""
    perms = PermissionManager()
    perms.grant(PermissionCategory.SCREEN_RECORDING)

    cap_provider = ScreenCaptureProvider(perms=perms, mock_mode=True)
    vis_provider = MockVisionProvider(
        default_text="IndexError: list index out of range\nwhile low <= high:\n    mid = (low + high) // 2\n"
    )
    engine = ScreenUnderstandingEngine(
        capture_provider=cap_provider,
        vision_provider=vis_provider,
    )

    ctx: ScreenContext = engine.observe_screen(target_app="Visual Studio Code")
    assert ctx.success is True
    assert ctx.detected_app == "Visual Studio Code"
    assert "IndexError" in str(ctx.visible_error)
    assert "binary_search" in str(ctx.topic_detected)
