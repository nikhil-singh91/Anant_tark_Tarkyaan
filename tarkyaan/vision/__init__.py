"""
Tarkyaan Vision Subsystem.
Multimodal image understanding, diagram parsing, document chunking, and screen perception.
"""

from tarkyaan.vision.provider import (
    CodeAnalysisResult,
    DiagramExplanation,
    VisionProvider,
    VisionResult,
)
from tarkyaan.vision.mock_provider import MockVisionProvider
from tarkyaan.vision.gemini_provider import GeminiVisionProvider
from tarkyaan.vision.image_understanding import (
    ImageUnderstandingEngine,
    ProblemExtraction,
)
from tarkyaan.vision.document_understanding import (
    DocumentOutline,
    DocumentSection,
    DocumentUnderstandingEngine,
)
from tarkyaan.vision.screen_capture import (
    ScreenCaptureProvider,
    ScreenCaptureResult,
)
from tarkyaan.vision.screen_understanding import (
    ScreenContext,
    ScreenUnderstandingEngine,
)

__all__ = [
    "CodeAnalysisResult",
    "DiagramExplanation",
    "DocumentOutline",
    "DocumentSection",
    "DocumentUnderstandingEngine",
    "GeminiVisionProvider",
    "ImageUnderstandingEngine",
    "MockVisionProvider",
    "ProblemExtraction",
    "ScreenCaptureProvider",
    "ScreenCaptureResult",
    "ScreenContext",
    "ScreenUnderstandingEngine",
    "VisionProvider",
    "VisionResult",
]
