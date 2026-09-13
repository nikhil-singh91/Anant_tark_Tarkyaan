"""
Unified Companion Router.
Central hub that receives multimodal inputs (Voice, Text, Vision, Screen, Documents),
assembles multimodal context, resolves educational and autonomous intents,
coordinates capabilities, and generates unified voice/text pedagogical responses.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from tarkyaan.agent.autonomous_task_engine import AutonomousTaskEngine
from tarkyaan.browser.browser_capability import BrowserCapability
from tarkyaan.companion.prompt_defense import PromptInjectionDefender
from tarkyaan.companion.tool_result_normalizer import ToolResultNormalizer
from tarkyaan.computer.application_adapter import ApplicationAdapter
from tarkyaan.context.multimodal_context import (
    LearnerContextSnapshot,
    MultimodalContext,
    MultimodalContextAssembler,
)
from tarkyaan.events.event_bus import EventBus, TarkyaanEvent
from tarkyaan.filesystem.filesystem_capability import FilesystemCapability
from tarkyaan.models.enums import CompanionChannel, CompanionIntentDomain, MultimodalInputType
from tarkyaan.multimodal.input_engine import MultimodalInput, MultimodalInputEngine
from tarkyaan.planning.decision_engine import LearningDecisionEngine
from tarkyaan.teaching import TeachingEngine
from tarkyaan.vision.image_understanding import ImageUnderstandingEngine
from tarkyaan.vision.screen_understanding import ScreenUnderstandingEngine


class CompanionResponse(BaseModel):
    """Unified response package ready for voice TTS, text chat, and UI updates."""
    response_id: str
    learner_id: str
    channel: CompanionChannel
    text_response: str
    voice_script: str
    intent_domain: CompanionIntentDomain
    recommended_next_action: Optional[str] = None
    autonomous_task_id: Optional[str] = None
    context_summary: str = ""
    is_cancelled: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UnifiedCompanionRouter:
    """
    Unified router for all companion interactions.
    Bridges sensory input, context assembly, capability dispatch, and teaching synthesis.
    """

    def __init__(
        self,
        multimodal_engine: Optional[MultimodalInputEngine] = None,
        context_assembler: Optional[MultimodalContextAssembler] = None,
        agent_engine: Optional[AutonomousTaskEngine] = None,
        decision_engine: Optional[LearningDecisionEngine] = None,
        teaching_engine: Optional[TeachingEngine] = None,
        browser_capability: Optional[BrowserCapability] = None,
        app_adapter: Optional[ApplicationAdapter] = None,
        fs_capability: Optional[FilesystemCapability] = None,
        event_bus: Optional[EventBus] = None,
    ) -> None:
        self.multimodal_engine = multimodal_engine or MultimodalInputEngine()
        self.context_assembler = context_assembler or MultimodalContextAssembler()
        self.agent_engine = agent_engine or AutonomousTaskEngine(event_bus=event_bus)
        self.decision_engine = decision_engine
        self.teaching_engine = teaching_engine
        self.browser_capability = browser_capability or BrowserCapability()
        self.app_adapter = app_adapter or ApplicationAdapter(mock_mode=True)
        self.fs_capability = fs_capability or FilesystemCapability()
        self.event_bus = event_bus

    def route_interaction(
        self,
        input_payload: MultimodalInput,
        learner_snapshot: Optional[LearnerContextSnapshot] = None,
        recent_turns: Optional[List[Dict[str, str]]] = None,
        confirmed_by_user: bool = False,
    ) -> CompanionResponse:
        """
        Main entry point:
        Input -> Context -> Intent -> Routing -> Capability -> Normalized Response.
        """
        text = input_payload.text_content.strip()

        # 1. Check Cancellation Intent immediately (§98 Acceptance Test)
        if self.agent_engine.is_cancellation_intent(text):
            return self._handle_cancellation(input_payload.learner_id)

        # 2. Assemble Multimodal Context
        ctx: MultimodalContext = self.context_assembler.assemble_context(
            current_input=input_payload,
            learner_snapshot=learner_snapshot,
            recent_turns=recent_turns,
        )

        # 3. Classify Companion Intent Domain
        intent_domain = self._classify_intent(text, input_payload)

        # 4. Dispatch by Intent Domain
        # A. Next Action Query ("What should I do next?") (§97 Acceptance Test)
        if self._is_next_action_query(text):
            return self._handle_next_action_recommendation(ctx)

        # B. Multimodal Problem Solving with Screen/Image (§94 Acceptance Test)
        if input_payload.primary_type in [MultimodalInputType.IMAGE, MultimodalInputType.SCREEN] or input_payload.extracted_problem:
            return self._handle_visual_problem_interaction(ctx)

        # C. Project Debugging or Codebase Exploration (§95 Acceptance Test)
        if intent_domain in [CompanionIntentDomain.DEBUGGING, CompanionIntentDomain.PROJECT_STUDY]:
            return self._handle_project_interaction(ctx, confirmed_by_user=confirmed_by_user)

        # D. Research & Resource Finding (§96 Acceptance Test)
        if intent_domain == CompanionIntentDomain.RESEARCH:
            return self._handle_research_interaction(ctx)

        # E. General Autonomous Learning Task
        if any(w in text.lower() for w in ["help me prepare", "study session", "exam", "prepare"]):
            task = self.agent_engine.run_task(
                learner_id=ctx.learner.learner_id,
                goal_text=text,
                context=ctx,
                confirmed_by_user=confirmed_by_user,
            )
            resp_text = (
                f"I've planned and prepared your study session for {ctx.learner.active_topic}. "
                f"{task.result_summary}"
            )
            return CompanionResponse(
                response_id=f"resp_{task.task_id}",
                learner_id=ctx.learner.learner_id,
                channel=CompanionChannel.VOICE if input_payload.primary_type == MultimodalInputType.VOICE else CompanionChannel.TEXT,
                text_response=resp_text,
                voice_script=resp_text,
                intent_domain=CompanionIntentDomain.LEARNING,
                autonomous_task_id=task.task_id,
                context_summary=ctx.format_pedagogical_summary(),
            )

        # F. Fallback Conversational / Socratic Companion response
        resp_text = (
            f"I hear you. Let's focus on {ctx.learner.active_topic}. "
            "What specific question or code problem would you like to explore?"
        )
        return CompanionResponse(
            response_id=f"resp_{input_payload.input_id}",
            learner_id=ctx.learner.learner_id,
            channel=CompanionChannel.VOICE if input_payload.primary_type == MultimodalInputType.VOICE else CompanionChannel.TEXT,
            text_response=resp_text,
            voice_script=resp_text,
            intent_domain=CompanionIntentDomain.COMPANION,
            context_summary=ctx.format_pedagogical_summary(),
        )

    # --------------------------------------------------------------------------
    # Specialized Intent Handlers
    # --------------------------------------------------------------------------

    def _handle_cancellation(self, learner_id: str) -> CompanionResponse:
        """Cancel all active background capabilities and tasks (§98)."""
        cancelled_tasks = self.agent_engine.cancel_all_active_tasks(reason="Learner requested stop.")
        cancelled_sessions = self.browser_capability.session_mgr.cancel_all(reason="Learner requested stop.")

        ack_text = "I've stopped all active tasks and background operations. Whenever you're ready, let me know."
        return CompanionResponse(
            response_id=f"cancel_{learner_id}",
            learner_id=learner_id,
            channel=CompanionChannel.VOICE,
            text_response=ack_text,
            voice_script=ack_text,
            intent_domain=CompanionIntentDomain.COMPANION,
            is_cancelled=True,
            metadata={
                "cancelled_tasks": cancelled_tasks,
                "cancelled_browser_sessions": cancelled_sessions,
            },
        )

    def _handle_next_action_recommendation(self, ctx: MultimodalContext) -> CompanionResponse:
        """Provide optimal next step combining mastery, retention, and adaptive state (§97)."""
        topic = ctx.learner.active_topic
        mastery = ctx.learner.mastery_score
        health = ctx.learner.learning_health

        if mastery < 0.4 or health.value in ["stalled", "regressing"]:
            rec = f"Review prerequisite concepts for {topic} with a Socratic walkthrough."
        elif mastery < 0.7:
            rec = f"Practice 2 boundary-condition coding problems on {topic}."
        else:
            rec = f"Advance to the next curriculum milestone or conduct an advanced challenge on {topic}."

        msg = (
            f"Based on your current progress in {topic} (mastery {mastery:.2f}, health: {health.value}), "
            f"the highest-value next step is: {rec}"
        )
        return CompanionResponse(
            response_id=f"next_{ctx.learner.learner_id}",
            learner_id=ctx.learner.learner_id,
            channel=CompanionChannel.VOICE if ctx.current_input.primary_type == MultimodalInputType.VOICE else CompanionChannel.TEXT,
            text_response=msg,
            voice_script=msg,
            intent_domain=CompanionIntentDomain.LEARNING,
            recommended_next_action=rec,
            context_summary=ctx.format_pedagogical_summary(),
        )

    def _handle_visual_problem_interaction(self, ctx: MultimodalContext) -> CompanionResponse:
        """Handle coding problem image/screenshot (§94)."""
        prob = ctx.current_input.extracted_problem
        if not prob and ctx.current_input.image_path:
            prob = self.multimodal_engine.image_engine.extract_problem_from_image(ctx.current_input.image_path)

        topic = prob.target_topic if prob else ctx.learner.active_topic
        socratic_q = prob.recommended_socratic_prompt if prob else "What is the termination condition for your loop?"

        explanation = (
            f"I analyzed the problem on {topic}. "
            f"{socratic_q}"
        )

        return CompanionResponse(
            response_id=f"vis_{ctx.current_input.input_id}",
            learner_id=ctx.learner.learner_id,
            channel=CompanionChannel.VOICE if ctx.current_input.primary_type == MultimodalInputType.VOICE else CompanionChannel.TEXT,
            text_response=explanation,
            voice_script=explanation,
            intent_domain=CompanionIntentDomain.LEARNING,
            recommended_next_action="Answer the Socratic question or test boundary cases.",
            context_summary=ctx.format_pedagogical_summary(),
        )

    def _handle_project_interaction(self, ctx: MultimodalContext, confirmed_by_user: bool = False) -> CompanionResponse:
        """Handle opening a project, inspecting code, and diagnosing bugs (§95)."""
        task = self.agent_engine.run_task(
            learner_id=ctx.learner.learner_id,
            goal_text=ctx.current_input.text_content,
            context=ctx,
            confirmed_by_user=confirmed_by_user,
        )

        resp = (
            f"I inspected your project in Visual Studio Code. "
            f"{task.result_summary}"
        )
        return CompanionResponse(
            response_id=f"proj_{task.task_id}",
            learner_id=ctx.learner.learner_id,
            channel=CompanionChannel.VOICE if ctx.current_input.primary_type == MultimodalInputType.VOICE else CompanionChannel.TEXT,
            text_response=resp,
            voice_script=resp,
            intent_domain=CompanionIntentDomain.PROJECT_STUDY,
            autonomous_task_id=task.task_id,
            context_summary=ctx.format_pedagogical_summary(),
        )

    def _handle_research_interaction(self, ctx: MultimodalContext) -> CompanionResponse:
        """Handle searching the web for educational resources (§96)."""
        query = ctx.current_input.text_content
        search_res = self.browser_capability.search_web(query)
        clean_content = ToolResultNormalizer.normalize_result("browser", search_res.model_dump())

        resp_text = (
            f"I researched the best explanations of {ctx.learner.active_topic}. "
            f"{clean_content} Would you like to walk through the top resource together?"
        )

        return CompanionResponse(
            response_id=f"res_{ctx.current_input.input_id}",
            learner_id=ctx.learner.learner_id,
            channel=CompanionChannel.VOICE if ctx.current_input.primary_type == MultimodalInputType.VOICE else CompanionChannel.TEXT,
            text_response=resp_text,
            voice_script=resp_text,
            intent_domain=CompanionIntentDomain.RESEARCH,
            context_summary=ctx.format_pedagogical_summary(),
        )

    def _classify_intent(self, text: str, inp: MultimodalInput) -> CompanionIntentDomain:
        t = text.lower()
        if any(w in t for w in ["open my", "vscode", "project", "codebase", "architecture"]):
            return CompanionIntentDomain.PROJECT_STUDY
        if any(w in t for w in ["why isn't", "bug", "fix", "failing", "error", "debug"]):
            return CompanionIntentDomain.DEBUGGING
        if any(w in t for w in ["find", "search", "best explanation", "resource", "curate"]):
            return CompanionIntentDomain.RESEARCH
        if inp.primary_type in [MultimodalInputType.IMAGE, MultimodalInputType.SCREEN]:
            return CompanionIntentDomain.LEARNING
        if any(w in t for w in ["teach", "quiz", "practice", "explain", "dsa", "exam"]):
            return CompanionIntentDomain.LEARNING
        return CompanionIntentDomain.COMPANION

    def _is_next_action_query(self, text: str) -> bool:
        t = text.lower().strip()
        patterns = [
            r"what\s+(should|can)\s+i\s+do\s+next",
            r"what('s| is)\s+next",
            r"where\s+(should|do)\s+i\s+go\s+from\s+here",
            r"next\s+step",
            r"agla\s+kadam",
            r"ab\s+kya\s+karein",
        ]
        return any(re.search(pat, t) for pat in patterns)
