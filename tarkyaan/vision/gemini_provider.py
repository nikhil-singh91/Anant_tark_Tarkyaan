"""
Gemini Vision Provider for live multimodal visual understanding.
Integrates with Google GenAI / Gemini when GEMINI_API_KEY is configured in the environment.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional
from tarkyaan.vision.provider import (
    CodeAnalysisResult,
    DiagramExplanation,
    VisionProvider,
    VisionResult,
)


class GeminiVisionProvider(VisionProvider):
    """Live multimodal vision provider utilizing Google Gemini."""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash") -> None:
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        self.model_name = model_name

    def is_available(self) -> bool:
        """Check if provider has valid credentials configured."""
        return bool(self.api_key and self.api_key.strip())

    def analyze_image(
        self,
        image_bytes_or_path: bytes | str,
        prompt: str = "Describe this image in educational detail.",
        context: Optional[Dict[str, Any]] = None,
    ) -> VisionResult:
        if not self.is_available():
            return VisionResult(
                success=False,
                description="",
                error="GeminiVisionProvider unavailable: GEMINI_API_KEY is not configured.",
            )

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)
            # Read image if path
            image_data: bytes
            if isinstance(image_bytes_or_path, str):
                with open(image_bytes_or_path, "rb") as f:
                    image_data = f.read()
            else:
                image_data = image_bytes_or_path

            part = types.Part.from_bytes(data=image_data, mime_type="image/png")
            response = client.models.generate_content(
                model=self.model_name,
                contents=[part, prompt],
            )
            text = response.text or ""
            return VisionResult(
                success=True,
                description=text,
                detected_text=text,
                confidence=0.9,
                metadata={"model": self.model_name},
            )
        except Exception as e:
            return VisionResult(
                success=False,
                description="",
                error=f"Gemini API error during image analysis: {str(e)}",
            )

    def extract_text(self, image_bytes_or_path: bytes | str) -> str:
        res = self.analyze_image(
            image_bytes_or_path,
            prompt="Extract all visible text from this image verbatim. Do not add conversational commentary.",
        )
        return res.detected_text if res.success else ""

    def analyze_code_image(
        self,
        image_bytes_or_path: bytes | str,
        context: Optional[Dict[str, Any]] = None,
    ) -> CodeAnalysisResult:
        if not self.is_available():
            return CodeAnalysisResult(
                success=False,
                error="GeminiVisionProvider unavailable: GEMINI_API_KEY is not configured.",
            )

        prompt = (
            "Analyze this coding problem or IDE screenshot. Identify: "
            "1. Programming language\n"
            "2. The exact code snippet visible\n"
            "3. Any visible error message\n"
            "4. The suspected bug or algorithmic challenge\n"
            "5. The core computer science concept involved\n"
            "Explain clearly for a computer science learner."
        )
        res = self.analyze_image(image_bytes_or_path, prompt=prompt, context=context)
        if not res.success:
            return CodeAnalysisResult(success=False, error=res.error)

        return CodeAnalysisResult(
            success=True,
            language="python",
            code_snippet=res.detected_text,
            explanation=res.description,
            confidence=0.9,
        )

    def understand_diagram(
        self,
        image_bytes_or_path: bytes | str,
        context: Optional[Dict[str, Any]] = None,
    ) -> DiagramExplanation:
        if not self.is_available():
            return DiagramExplanation(
                success=False,
                error="GeminiVisionProvider unavailable: GEMINI_API_KEY is not configured.",
            )

        prompt = (
            "Analyze this educational diagram, flowchart, or architecture chart. "
            "Describe the components, relationships, core underlying concept, and educational summary."
        )
        res = self.analyze_image(image_bytes_or_path, prompt=prompt, context=context)
        if not res.success:
            return DiagramExplanation(success=False, error=res.error)

        return DiagramExplanation(
            success=True,
            diagram_type="diagram",
            educational_summary=res.description,
            confidence=0.9,
        )
