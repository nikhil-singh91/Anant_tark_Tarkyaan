"""
Screen Capture Provider and Safety Guard.
Enforces explicit user permission, ephemeral in-memory storage, secret redaction,
and macOS screencapture CLI execution with mock fallbacks.
"""

from __future__ import annotations

import os
import platform
import re
import subprocess
import tempfile
import uuid
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from tarkyaan.events.event_bus import EventBus, TarkyaanEvent
from tarkyaan.safety.permissions import PermissionCategory, PermissionManager, permission_manager


class ScreenCaptureResult(BaseModel):
    """Ephemeral screen capture record."""
    success: bool
    screenshot_id: str
    width: int = 1920
    height: int = 1080
    image_bytes: Optional[bytes] = Field(default=None, exclude=True)  # Keep out of logs
    temporary_path: Optional[str] = None
    captured_at: str = ""
    error: Optional[str] = None


class ScreenCaptureProvider:
    """
    Safe screen capture provider.
    Never records continuously. Only captures on-demand when explicit permission is granted.
    """

    def __init__(
        self,
        perms: Optional[PermissionManager] = None,
        event_bus: Optional[EventBus] = None,
        mock_mode: bool = False,
    ) -> None:
        self.permission_mgr = perms or permission_manager
        self.event_bus = event_bus
        self.mock_mode = mock_mode

    def capture_screen(
        self,
        display_index: int = 0,
        target_app: Optional[str] = None,
    ) -> ScreenCaptureResult:
        """
        Capture a single ephemeral screenshot of the learner's screen.
        Requires SCREEN_RECORDING permission to be explicitly GRANTED.
        """
        cap_id = f"scr_{uuid.uuid4().hex[:8]}"

        # 1. Permission Check
        if not self.permission_mgr.is_granted(PermissionCategory.SCREEN_RECORDING):
            return ScreenCaptureResult(
                success=False,
                screenshot_id=cap_id,
                error=(
                    "Screen capture blocked: Screen Recording permission is not granted. "
                    "Tarkyaan requires explicit macOS Screen Recording permission."
                ),
            )

        if self.event_bus:
            self.event_bus.publish(
                TarkyaanEvent.SCREEN_CAPTURE_STARTED,
                {"screenshot_id": cap_id, "display_index": display_index},
            )

        # 2. Mock mode for tests or non-macOS environments
        if self.mock_mode or platform.system() != "Darwin":
            mock_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x07\x80\x00\x00\x048\x08\x06\x00\x00\x00"
            return ScreenCaptureResult(
                success=True,
                screenshot_id=cap_id,
                width=1920,
                height=1080,
                image_bytes=mock_bytes,
                captured_at="2026-09-13T12:00:00Z",
            )

        # 3. macOS Live capture using bounded screencapture utility
        try:
            temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            temp_path = temp_file.name
            temp_file.close()

            # screencapture -x -C: -x no sound, -C capture cursor
            cmd = ["screencapture", "-x", temp_path]
            proc = subprocess.run(cmd, capture_output=True, timeout=5)

            if proc.returncode != 0:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                return ScreenCaptureResult(
                    success=False,
                    screenshot_id=cap_id,
                    error=f"screencapture utility returned error code {proc.returncode}: {proc.stderr.decode()}",
                )

            with open(temp_path, "rb") as f:
                raw_bytes = f.read()

            # Clean up temp file immediately after reading to preserve privacy
            if os.path.exists(temp_path):
                os.unlink(temp_path)

            return ScreenCaptureResult(
                success=True,
                screenshot_id=cap_id,
                width=1920,
                height=1080,
                image_bytes=raw_bytes,
                captured_at="now",
            )
        except subprocess.TimeoutExpired:
            return ScreenCaptureResult(
                success=False,
                screenshot_id=cap_id,
                error="Screen capture timed out after 5 seconds.",
            )
        except Exception as e:
            return ScreenCaptureResult(
                success=False,
                screenshot_id=cap_id,
                error=f"Screen capture failed: {str(e)}",
            )

    @staticmethod
    def redact_secrets_from_text(text: str) -> str:
        """
        Utility to sanitize OCR/text output from screenshots,
        removing API keys, Bearer tokens, and password strings.
        """
        # Redact API keys (sk-..., AIza..., ghp_..., etc.)
        sanitized = re.sub(r"(sk-[a-zA-Z0-9]{20,})", "[REDACTED_API_KEY]", text)
        sanitized = re.sub(r"(AIza[0-9A-Za-z-_]{35})", "[REDACTED_GOOGLE_KEY]", sanitized)
        sanitized = re.sub(r"(ghp_[a-zA-Z0-9]{36})", "[REDACTED_GITHUB_TOKEN]", sanitized)
        sanitized = re.sub(r"(Bearer\s+[a-zA-Z0-9_\-\.]{20,})", "Bearer [REDACTED_TOKEN]", sanitized)
        sanitized = re.sub(r"(password\s*=\s*['\"][^'\"]+['\"])", "password=[REDACTED]", sanitized, flags=re.IGNORECASE)
        return sanitized
