"""
Vision Provider Abstraction and Data Models.
Defines interfaces for image perception, OCR, diagram understanding, and visual code analysis.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class VisionResult(BaseModel):
    """Standardized visual perception outcome."""
    success: bool
    description: str
    detected_text: str = ""
    detected_labels: List[str] = Field(default_factory=list)
    confidence: float = 1.0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None


class CodeAnalysisResult(BaseModel):
    """Structured understanding of a code screenshot or IDE capture."""
    success: bool
    language: str = "python"
    code_snippet: str = ""
    error_message: Optional[str] = None
    suspected_bug: Optional[str] = None
    algorithmic_concept: Optional[str] = None
    confidence: float = 1.0
    explanation: str = ""
    error: Optional[str] = None


class DiagramExplanation(BaseModel):
    """Structured understanding of an educational diagram, graph, or architecture visual."""
    success: bool
    diagram_type: str = "flowchart"  # flowchart, graph, tree, architecture, circuit
    components: List[str] = Field(default_factory=list)
    relationships: List[str] = Field(default_factory=list)
    core_concept: str = ""
    educational_summary: str = ""
    confidence: float = 1.0
    error: Optional[str] = None


class VisionProvider(ABC):
    """Abstract base provider for visual intelligence and perception."""

    @abstractmethod
    def analyze_image(
        self,
        image_bytes_or_path: bytes | str,
        prompt: str = "Describe this image in educational detail.",
        context: Optional[Dict[str, Any]] = None,
    ) -> VisionResult:
        """Perform general visual understanding on an image."""
        pass

    @abstractmethod
    def extract_text(self, image_bytes_or_path: bytes | str) -> str:
        """Extract visible text / OCR from an image."""
        pass

    @abstractmethod
    def analyze_code_image(
        self,
        image_bytes_or_path: bytes | str,
        context: Optional[Dict[str, Any]] = None,
    ) -> CodeAnalysisResult:
        """Extract and diagnose code, errors, or algorithm structures from an image."""
        pass

    @abstractmethod
    def understand_diagram(
        self,
        image_bytes_or_path: bytes | str,
        context: Optional[Dict[str, Any]] = None,
    ) -> DiagramExplanation:
        """Understand an educational diagram, graph, or chart."""
        pass
