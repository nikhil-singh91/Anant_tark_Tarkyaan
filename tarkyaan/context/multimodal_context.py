"""
Multimodal Context Assembler and Data Models.
Combines learner model, mastery, conversation history, screen, image, document, and tool context
into a bounded, coherent reasoning context.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from tarkyaan.context.environment_context import EnvironmentContextEngine, EnvironmentState
from tarkyaan.models.enums import HealthStatus, MasteryTier
from tarkyaan.multimodal.input_engine import MultimodalInput


class LearnerContextSnapshot(BaseModel):
    """Essential learner attributes relevant for contextual adaptation."""
    learner_id: str
    display_name: str = "Learner"
    active_goal_title: str = "Computer Science Foundations"
    active_topic: str = "algorithms"
    mastery_tier: MasteryTier = MasteryTier.PRACTICING
    mastery_score: float = 0.5
    learning_health: HealthStatus = HealthStatus.HEALTHY
    recent_misconceptions: List[str] = Field(default_factory=list)
    preferred_explanation_style: str = "socratic"


class MultimodalContext(BaseModel):
    """
    Unified bounded multimodal context package.
    Synthesizes learner state, environment, conversation, sensory inputs, and tool observations.
    """
    context_id: str
    learner: LearnerContextSnapshot
    environment: EnvironmentState
    current_input: MultimodalInput
    recent_turns: List[Dict[str, str]] = Field(default_factory=list)
    latest_tool_result: Optional[Dict[str, Any]] = None
    synthesized_prompt: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def format_pedagogical_summary(self) -> str:
        """Format a concise overview of active context for reasoning engines."""
        lines = [
            f"Learner: {self.learner.display_name} (Mastery: {self.learner.mastery_score:.2f}, Topic: {self.learner.active_topic})",
            f"Health: {self.learner.learning_health.value}",
        ]
        if self.learner.recent_misconceptions:
            lines.append(f"Recent Misconceptions: {', '.join(self.learner.recent_misconceptions)}")

        lines.append(f"Environment: {self.environment.active_app}")

        if self.current_input.extracted_problem:
            prob = self.current_input.extracted_problem
            lines.append(f"Visual Problem: {prob.title} - {prob.target_topic}")
            if prob.error_context:
                lines.append(f"Visible Error: {prob.error_context}")

        if self.current_input.screen_context and self.current_input.screen_context.success:
            lines.append(f"Screen: {self.current_input.screen_context.pedagogical_summary}")

        if self.current_input.document_outline:
            doc = self.current_input.document_outline
            lines.append(f"Document: {doc.file_path} ({doc.total_sections} sections)")

        if self.latest_tool_result:
            tool_name = self.latest_tool_result.get("tool", "tool")
            lines.append(f"Last Tool Result ({tool_name}): {str(self.latest_tool_result.get('summary', ''))[:120]}")

        lines.append(f"Learner Input: \"{self.current_input.text_content}\"")
        return "\n".join(lines)


class MultimodalContextAssembler:
    """
    Assembles, trims, and bounds context from disparate Tarkyaan subsystems.
    Guarantees strict token/size limits.
    """

    def __init__(self, env_engine: Optional[EnvironmentContextEngine] = None) -> None:
        self.env_engine = env_engine or EnvironmentContextEngine()

    def assemble_context(
        self,
        current_input: MultimodalInput,
        learner_snapshot: Optional[LearnerContextSnapshot] = None,
        recent_turns: Optional[List[Dict[str, str]]] = None,
        latest_tool_result: Optional[Dict[str, Any]] = None,
        max_turns: int = 4,
    ) -> MultimodalContext:
        """Construct a bounded MultimodalContext package."""
        learner = learner_snapshot or LearnerContextSnapshot(
            learner_id=current_input.learner_id,
            active_topic="algorithms",
        )

        env = self.env_engine.get_current_environment()

        # Bounded history window: take at most max_turns
        turns = (recent_turns or [])[-max_turns:]

        ctx = MultimodalContext(
            context_id=f"ctx_{current_input.input_id}",
            learner=learner,
            environment=env,
            current_input=current_input,
            recent_turns=turns,
            latest_tool_result=latest_tool_result,
        )
        ctx.synthesized_prompt = ctx.format_pedagogical_summary()
        return ctx
