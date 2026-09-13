"""
Mock Vision Provider for deterministic testing.
Provides predictable visual responses, code parsing, and diagram understanding without live API keys.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from tarkyaan.vision.provider import (
    CodeAnalysisResult,
    DiagramExplanation,
    VisionProvider,
    VisionResult,
)


class MockVisionProvider(VisionProvider):
    """Deterministic mock provider for testing vision perception workflows."""

    def __init__(
        self,
        default_text: str = "Binary Search Implementation in Python\ndef binary_search(arr, target):\n    low, high = 0, len(arr) - 1\n",
        default_description: str = "A screenshot of an IDE showing binary search algorithm code.",
        simulate_error: bool = False,
        error_message: str = "Mock vision provider failure",
    ) -> None:
        self.default_text = default_text
        self.default_description = default_description
        self.simulate_error = simulate_error
        self.error_message = error_message
        self.call_history: list[Dict[str, Any]] = []

    def analyze_image(
        self,
        image_bytes_or_path: bytes | str,
        prompt: str = "Describe this image in educational detail.",
        context: Optional[Dict[str, Any]] = None,
    ) -> VisionResult:
        self.call_history.append({"operation": "analyze_image", "prompt": prompt, "context": context})
        if self.simulate_error:
            return VisionResult(
                success=False,
                description="",
                error=self.error_message,
            )
        return VisionResult(
            success=True,
            description=self.default_description,
            detected_text=self.default_text,
            detected_labels=["code", "editor", "python", "algorithm"],
            confidence=0.98,
            metadata={"simulated": True},
        )

    def extract_text(self, image_bytes_or_path: bytes | str) -> str:
        self.call_history.append({"operation": "extract_text"})
        if self.simulate_error:
            return ""
        return self.default_text

    def analyze_code_image(
        self,
        image_bytes_or_path: bytes | str,
        context: Optional[Dict[str, Any]] = None,
    ) -> CodeAnalysisResult:
        self.call_history.append({"operation": "analyze_code_image", "context": context})
        if self.simulate_error:
            return CodeAnalysisResult(
                success=False,
                error=self.error_message,
            )

        # Check if error or bug mentioned in custom default text
        snippet = self.default_text
        error_msg = None
        suspected_bug = None
        if "IndexError" in snippet or "while low <= high" in snippet and "mid + 1" not in snippet:
            suspected_bug = "Infinite loop or boundary calculation flaw in binary search pointer updates."
            error_msg = "IndexError: list index out of range"

        return CodeAnalysisResult(
            success=True,
            language="python",
            code_snippet=snippet,
            error_message=error_msg,
            suspected_bug=suspected_bug,
            algorithmic_concept="binary_search",
            confidence=0.95,
            explanation="The screenshot shows a binary search routine. The while loop condition requires careful pointer updates (low = mid + 1, high = mid - 1).",
        )

    def understand_diagram(
        self,
        image_bytes_or_path: bytes | str,
        context: Optional[Dict[str, Any]] = None,
    ) -> DiagramExplanation:
        self.call_history.append({"operation": "understand_diagram", "context": context})
        if self.simulate_error:
            return DiagramExplanation(
                success=False,
                error=self.error_message,
            )
        return DiagramExplanation(
            success=True,
            diagram_type="flowchart",
            components=["Start", "Check condition", "Calculate Mid", "Adjust bounds", "Target found"],
            relationships=["Start -> Check condition", "Check condition -> Calculate Mid"],
            core_concept="Divide and conquer algorithm flow",
            educational_summary="Flowchart visualizing binary search decision tree dividing search space in half at each step.",
            confidence=0.96,
        )
