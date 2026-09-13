"""
Image Understanding Engine.
Performs higher-level pedagogical visual reasoning on images, diagrams, and coding screenshots.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from tarkyaan.events.event_bus import EventBus, TarkyaanEvent
from tarkyaan.vision.mock_provider import MockVisionProvider
from tarkyaan.vision.provider import (
    CodeAnalysisResult,
    DiagramExplanation,
    VisionProvider,
    VisionResult,
)


class ProblemExtraction(BaseModel):
    """Pedagogically parsed problem extracted from an image or screenshot."""
    title: str = "Coding Challenge"
    problem_statement: str
    code_context: str = ""
    error_context: Optional[str] = None
    target_topic: str = "algorithms"
    difficulty_estimate: str = "intermediate"
    identified_misconceptions: list[str] = Field(default_factory=list)
    recommended_socratic_prompt: str = ""


class ImageUnderstandingEngine:
    """
    Pedagogical vision engine.
    Extracts educational intent, code context, and problem statements from visual inputs.
    """

    def __init__(
        self,
        provider: Optional[VisionProvider] = None,
        event_bus: Optional[EventBus] = None,
    ) -> None:
        self.provider = provider or MockVisionProvider()
        self.event_bus = event_bus

    def understand_image(
        self,
        image_bytes_or_path: bytes | str,
        context: Optional[Dict[str, Any]] = None,
    ) -> VisionResult:
        """Run general image understanding and publish telemetry."""
        if self.event_bus:
            self.event_bus.publish(TarkyaanEvent.VISION_ANALYSIS_STARTED, {"operation": "general"})

        res = self.provider.analyze_image(image_bytes_or_path, context=context)

        if self.event_bus:
            self.event_bus.publish(
                TarkyaanEvent.VISION_ANALYSIS_COMPLETED,
                {"success": res.success, "labels": res.detected_labels},
            )
        return res

    def extract_problem_from_image(
        self,
        image_bytes_or_path: bytes | str,
        learner_context: Optional[Dict[str, Any]] = None,
    ) -> ProblemExtraction:
        """
        Analyze a coding problem screenshot (e.g. LeetCode, Codeforces, IDE).
        Extracts the problem statement, error traces, and formulates a Socratic prompt.
        """
        if self.event_bus:
            self.event_bus.publish(
                TarkyaanEvent.VISION_ANALYSIS_STARTED,
                {"operation": "extract_problem"},
            )

        code_res: CodeAnalysisResult = self.provider.analyze_code_image(
            image_bytes_or_path,
            context=learner_context,
        )

        snippet = code_res.code_snippet or "No explicit code snippet detected"
        error_msg = code_res.error_message
        suspected_bug = code_res.suspected_bug
        topic = code_res.algorithmic_concept or "algorithms"

        # Build Socratic pedagogical prompt based on findings
        if error_msg:
            socratic_prompt = f"I see you encountered `{error_msg}`. What do you think is causing that line to fail?"
        elif suspected_bug:
            socratic_prompt = f"Take a look at your loop or termination boundary. What happens when the collection is empty or has a single element?"
        else:
            socratic_prompt = "What is the primary condition or invariant your algorithm is trying to maintain at each iteration?"

        misconceptions = []
        if suspected_bug and "boundary" in suspected_bug.lower():
            misconceptions.append("boundary_off_by_one")

        extraction = ProblemExtraction(
            title=f"Problem: {topic.replace('_', ' ').title()}",
            problem_statement=code_res.explanation or snippet,
            code_context=snippet,
            error_context=error_msg,
            target_topic=topic,
            identified_misconceptions=misconceptions,
            recommended_socratic_prompt=socratic_prompt,
        )

        if self.event_bus:
            self.event_bus.publish(
                TarkyaanEvent.VISION_ANALYSIS_COMPLETED,
                {"operation": "extract_problem", "topic": topic, "success": code_res.success},
            )
        return extraction

    def explain_diagram(
        self,
        image_bytes_or_path: bytes | str,
        topic_hint: Optional[str] = None,
    ) -> DiagramExplanation:
        """Analyze an educational architecture, algorithm flowchart, or data structure diagram."""
        if self.event_bus:
            self.event_bus.publish(
                TarkyaanEvent.VISION_ANALYSIS_STARTED,
                {"operation": "explain_diagram", "topic_hint": topic_hint},
            )
        diag = self.provider.understand_diagram(image_bytes_or_path, context={"topic_hint": topic_hint})
        if self.event_bus:
            self.event_bus.publish(
                TarkyaanEvent.VISION_ANALYSIS_COMPLETED,
                {"operation": "explain_diagram", "diagram_type": diag.diagram_type},
            )
        return diag
