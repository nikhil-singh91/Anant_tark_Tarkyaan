"""
Multimodal Input Engine.
Ingests, normalizes, and validates user inputs across text, voice, images, screenshots, and documents.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from tarkyaan.events.event_bus import EventBus, TarkyaanEvent
from tarkyaan.models.enums import MultimodalInputType
from tarkyaan.vision.document_understanding import DocumentOutline, DocumentUnderstandingEngine
from tarkyaan.vision.image_understanding import ImageUnderstandingEngine, ProblemExtraction
from tarkyaan.vision.screen_understanding import ScreenContext, ScreenUnderstandingEngine


class MultimodalInput(BaseModel):
    """Normalized multimodal container wrapping text, voice, visual, and document signals."""
    input_id: str
    learner_id: str
    primary_type: MultimodalInputType
    text_content: str = ""
    voice_transcript: Optional[str] = None
    image_path: Optional[str] = None
    document_path: Optional[str] = None
    extracted_problem: Optional[ProblemExtraction] = None
    screen_context: Optional[ScreenContext] = None
    document_outline: Optional[DocumentOutline] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = ""


class MultimodalInputEngine:
    """
    Ingests and coordinates multimodal sensory processing.
    Produces a normalized MultimodalInput payload ready for the Context Engine and Companion Router.
    """

    def __init__(
        self,
        image_engine: Optional[ImageUnderstandingEngine] = None,
        screen_engine: Optional[ScreenUnderstandingEngine] = None,
        document_engine: Optional[DocumentUnderstandingEngine] = None,
        event_bus: Optional[EventBus] = None,
    ) -> None:
        self.image_engine = image_engine or ImageUnderstandingEngine()
        self.screen_engine = screen_engine or ScreenUnderstandingEngine()
        self.document_engine = document_engine or DocumentUnderstandingEngine()
        self.event_bus = event_bus

    def process_text_input(
        self,
        learner_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MultimodalInput:
        """Process plain text learner input."""
        inp = MultimodalInput(
            input_id=f"inp_{uuid.uuid4().hex[:8]}",
            learner_id=learner_id,
            primary_type=MultimodalInputType.TEXT,
            text_content=text.strip(),
            metadata=metadata or {},
        )
        self._notify(inp)
        return inp

    def process_voice_input(
        self,
        learner_id: str,
        transcript: str,
        audio_duration_seconds: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MultimodalInput:
        """Process voice transcript input from the Voice subsystem."""
        meta = metadata or {}
        meta["audio_duration_seconds"] = audio_duration_seconds
        inp = MultimodalInput(
            input_id=f"inp_{uuid.uuid4().hex[:8]}",
            learner_id=learner_id,
            primary_type=MultimodalInputType.VOICE,
            text_content=transcript.strip(),
            voice_transcript=transcript.strip(),
            metadata=meta,
        )
        self._notify(inp)
        return inp

    def process_image_input(
        self,
        learner_id: str,
        image_path_or_bytes: str | bytes,
        accompanying_text: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MultimodalInput:
        """Process an uploaded educational image or code screenshot."""
        problem = self.image_engine.extract_problem_from_image(image_path_or_bytes)
        img_path = image_path_or_bytes if isinstance(image_path_or_bytes, str) else None

        inp = MultimodalInput(
            input_id=f"inp_{uuid.uuid4().hex[:8]}",
            learner_id=learner_id,
            primary_type=MultimodalInputType.IMAGE,
            text_content=accompanying_text or problem.problem_statement,
            image_path=img_path,
            extracted_problem=problem,
            metadata=metadata or {},
        )
        self._notify(inp)
        return inp

    def process_screen_query(
        self,
        learner_id: str,
        accompanying_question: str = "What am I looking at?",
        target_app: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MultimodalInput:
        """Process an on-demand screen awareness request."""
        screen_ctx = self.screen_engine.observe_screen(target_app=target_app)
        text = accompanying_question
        if screen_ctx.success:
            text = f"{accompanying_question} [Screen: {screen_ctx.pedagogical_summary}]"

        inp = MultimodalInput(
            input_id=f"inp_{uuid.uuid4().hex[:8]}",
            learner_id=learner_id,
            primary_type=MultimodalInputType.SCREEN,
            text_content=text,
            screen_context=screen_ctx,
            metadata=metadata or {},
        )
        self._notify(inp)
        return inp

    def process_document_input(
        self,
        learner_id: str,
        file_path: str,
        learning_goal: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MultimodalInput:
        """Process an educational document (PDF, TXT, MD, Code) with bounded chunking."""
        outline = self.document_engine.parse_document(file_path)
        summary_text = learning_goal or f"Teach me from {outline.file_path}: {outline.summary}"

        inp = MultimodalInput(
            input_id=f"inp_{uuid.uuid4().hex[:8]}",
            learner_id=learner_id,
            primary_type=MultimodalInputType.PDF if outline.file_type == "pdf" else MultimodalInputType.DOCUMENT,
            text_content=summary_text,
            document_path=file_path,
            document_outline=outline,
            metadata=metadata or {},
        )
        self._notify(inp)
        return inp

    def _notify(self, inp: MultimodalInput) -> None:
        if self.event_bus:
            self.event_bus.publish(
                TarkyaanEvent.MULTIMODAL_INPUT_RECEIVED,
                {
                    "input_id": inp.input_id,
                    "learner_id": inp.learner_id,
                    "modality": inp.primary_type.value,
                    "text_length": len(inp.text_content),
                },
            )
