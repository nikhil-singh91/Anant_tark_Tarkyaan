"""
Screen Understanding Engine.
Translates raw screen captures into pedagogical context (IDE code, active errors, problem descriptions).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from tarkyaan.events.event_bus import EventBus, TarkyaanEvent
from tarkyaan.vision.mock_provider import MockVisionProvider
from tarkyaan.vision.provider import CodeAnalysisResult, VisionProvider
from tarkyaan.vision.screen_capture import ScreenCaptureProvider, ScreenCaptureResult


class ScreenContext(BaseModel):
    """Structured understanding of learner's screen for educational assistance."""
    success: bool
    detected_app: str = "Unknown"  # VS Code, Terminal, Browser, PyCharm, etc.
    active_file: Optional[str] = None
    extracted_code: Optional[str] = None
    visible_error: Optional[str] = None
    topic_detected: Optional[str] = None
    pedagogical_summary: str = ""
    error: Optional[str] = None


class ScreenUnderstandingEngine:
    """
    Combines on-demand screen capture with vision perception
    to understand what the learner is currently working on.
    """

    def __init__(
        self,
        capture_provider: Optional[ScreenCaptureProvider] = None,
        vision_provider: Optional[VisionProvider] = None,
        event_bus: Optional[EventBus] = None,
    ) -> None:
        self.capture_provider = capture_provider or ScreenCaptureProvider(mock_mode=True)
        self.vision_provider = vision_provider or MockVisionProvider()
        self.event_bus = event_bus

    def observe_screen(
        self,
        target_app: Optional[str] = None,
        learner_context: Optional[Dict[str, Any]] = None,
    ) -> ScreenContext:
        """
        Observe current screen, perform vision analysis, and extract pedagogical context.
        Strictly checks permissions; fails gracefully with an honest message if permission is missing.
        """
        # 1. Capture screen
        cap: ScreenCaptureResult = self.capture_provider.capture_screen(target_app=target_app)
        if not cap.success:
            return ScreenContext(
                success=False,
                error=cap.error or "Failed to capture screen.",
                pedagogical_summary="Unable to inspect screen context.",
            )

        # 2. Vision analysis
        img_data = cap.image_bytes or b""
        code_analysis: CodeAnalysisResult = self.vision_provider.analyze_code_image(
            img_data,
            context=learner_context,
        )

        if not code_analysis.success:
            return ScreenContext(
                success=False,
                error=code_analysis.error or "Failed to analyze screen content.",
                pedagogical_summary="Visual analysis of screen content failed.",
            )

        # 3. Sanitize extracted text against secret leakage
        sanitized_code = ScreenCaptureProvider.redact_secrets_from_text(
            code_analysis.code_snippet or ""
        )
        sanitized_error = None
        if code_analysis.error_message:
            sanitized_error = ScreenCaptureProvider.redact_secrets_from_text(
                code_analysis.error_message
            )

        # 4. Infer application and active topic
        app_name = target_app or "VS Code"
        topic = code_analysis.algorithmic_concept or "Computer Science Problem"

        summary = f"Learner is working in {app_name} on {topic}."
        if sanitized_error:
            summary += f" Visible error detected: {sanitized_error}"

        ctx = ScreenContext(
            success=True,
            detected_app=app_name,
            extracted_code=sanitized_code,
            visible_error=sanitized_error,
            topic_detected=topic,
            pedagogical_summary=summary,
        )

        if self.event_bus:
            self.event_bus.publish(
                TarkyaanEvent.SCREEN_ANALYSIS_COMPLETED,
                {
                    "app": app_name,
                    "topic": topic,
                    "has_error": bool(sanitized_error),
                },
            )

        return ctx
