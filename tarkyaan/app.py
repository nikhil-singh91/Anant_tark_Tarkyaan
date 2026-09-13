"""
Tarkyaan (तर्कयान) — Unified Application Runtime & Interactive Cockpit.

Bootstraps all Phase 1-7 subsystems, provides the continuous Interactive
Learning Cockpit (REPL), handles multimodal queries, commands, safety,
and graceful shutdown.
"""

from __future__ import annotations

import logging
import os
import readline  # Enable arrow keys, history, and line editing in terminal
import sys
from typing import Any, Dict, List, Optional

from tarkyaan import __version__
from tarkyaan.agent.autonomous_task_engine import AutonomousTaskEngine
from tarkyaan.browser.browser_capability import BrowserCapability
from tarkyaan.capabilities.registry import capability_registry
from tarkyaan.companion.router import CompanionResponse, UnifiedCompanionRouter
from tarkyaan.computer.application_adapter import ApplicationAdapter
from tarkyaan.config.settings import settings
from tarkyaan.context.multimodal_context import LearnerContextSnapshot
from tarkyaan.events.event_bus import event_bus
from tarkyaan.filesystem.filesystem_capability import FilesystemCapability
from tarkyaan.memory.memory_manager import TarkyaanMemoryManager
from tarkyaan.memory.memory_store import TarkyaanMemoryStore
from tarkyaan.models.enums import CompanionChannel, MultimodalInputType
from tarkyaan.multimodal.input_engine import MultimodalInput
from tarkyaan.planning import (
    AdaptiveLearningEngine,
    LearningDecisionEngine,
    ProgressReportEngine,
    ReplanningEngine,
    ReviewScheduler,
)
from tarkyaan.planning.planner import LearningPlanner
from tarkyaan.practice.practice_engine import PracticeEngine
from tarkyaan.research.research_engine import ResearchEngine
from tarkyaan.session.session_engine import LearningSessionEngine
from tarkyaan.teaching.teaching_engine import TeachingEngine
from tarkyaan.terminal.terminal_capability import TerminalCapability
from tarkyaan.vision.document_understanding import DocumentUnderstandingEngine
from tarkyaan.vision.image_understanding import ImageUnderstandingEngine
from tarkyaan.vision.screen_understanding import ScreenUnderstandingEngine
from tarkyaan.voice.conversation_controller import VoiceConversationController

logger = logging.getLogger("tarkyaan.app")


def print_startup_banner() -> None:
    """Print the exact clean startup banner."""
    print("============================================================")
    print("                 TARKYAAN / तर्कयान")
    print("          Your Autonomous Learning Companion")
    print("============================================================")
    print()


class TarkyaanApp:
    """
    Tarkyaan Master Application.
    Orchestrates configuration, subsystem bootstrapping, safety policies,
    and the user-facing Interactive Learning Cockpit.
    """

    def __init__(self, learner_id: str = "default_learner", active_topic: str = "Data Structures & Algorithms") -> None:
        self.learner_id = learner_id
        self.active_topic = active_topic
        self.running: bool = False

        # Subsystems to be initialized in bootstrap()
        self.store: Optional[TarkyaanMemoryStore] = None
        self.memory: Optional[TarkyaanMemoryManager] = None
        self.planner: Optional[LearningPlanner] = None
        self.teaching: Optional[TeachingEngine] = None
        self.practice: Optional[PracticeEngine] = None
        self.session_engine: Optional[LearningSessionEngine] = None
        self.adaptive: Optional[AdaptiveLearningEngine] = None
        self.replanning: Optional[ReplanningEngine] = None
        self.review_scheduler: Optional[ReviewScheduler] = None
        self.progress_reporter: Optional[ProgressReportEngine] = None
        self.research: Optional[ResearchEngine] = None
        self.vision: Optional[ImageUnderstandingEngine] = None
        self.screen: Optional[ScreenUnderstandingEngine] = None
        self.document: Optional[DocumentUnderstandingEngine] = None
        self.browser: Optional[BrowserCapability] = None
        self.computer: Optional[ApplicationAdapter] = None
        self.filesystem: Optional[FilesystemCapability] = None
        self.terminal: Optional[TerminalCapability] = None
        self.agent: Optional[AutonomousTaskEngine] = None
        self.voice: Optional[VoiceConversationController] = None
        self.router: Optional[UnifiedCompanionRouter] = None

        # Active session state
        self.active_practice_question: Optional[Any] = None
        self.current_hint_level: int = 0
        self.recent_turns: List[Dict[str, str]] = []

    def bootstrap(self, verbose: bool = True) -> None:
        """
        Initialize all Phase 1-7 subsystems in the required order.
        Displays clean startup progress.
        """
        if verbose:
            print_startup_banner()

        # 1. Config
        # settings is loaded via import
        if verbose:
            print("[+] Configuration loaded")

        # 2. Memory
        db_path = settings.database_path or ":memory:"
        self.store = TarkyaanMemoryStore(db_path)
        self.memory = TarkyaanMemoryManager(self.store)
        if verbose:
            print("[+] Memory initialized")

        # 3. Learner Model
        # Initialize or retrieve learner profile and mastery record
        profile = self.memory.get_learner(self.learner_id)
        if not profile:
            from tarkyaan.models.learner import LearnerProfile
            profile = LearnerProfile(learner_id=self.learner_id, display_name="Learner")
            self.memory.create_learner(profile)
        if verbose:
            print("[+] Learner model initialized")

        # 4. Learning Planner
        self.planner = LearningPlanner(memory_manager=self.memory)
        if verbose:
            print("[+] Learning planner initialized")

        # 5. Teaching Engine
        self.teaching = TeachingEngine()
        if verbose:
            print("[+] Teaching engine initialized")

        # 6. Practice Engine
        self.practice = PracticeEngine()
        self.session_engine = LearningSessionEngine(memory_manager=self.memory)
        if verbose:
            print("[+] Practice engine initialized")

        # 7. Adaptive Learning
        self.adaptive = AdaptiveLearningEngine(memory=self.memory, event_bus=event_bus)
        self.replanning = ReplanningEngine(memory=self.memory, planner=self.planner, event_bus=event_bus)
        self.review_scheduler = ReviewScheduler(memory=self.memory, event_bus=event_bus)
        self.progress_reporter = ProgressReportEngine(memory=self.memory, event_bus=event_bus)
        if verbose:
            print("[+] Adaptive learning initialized")

        # 8. Research Engine
        self.research = ResearchEngine(memory_manager=self.memory)
        if verbose:
            print("[+] Research engine initialized")

        # 9. Vision & Multimodal Perception
        self.vision = ImageUnderstandingEngine(event_bus=event_bus)
        self.screen = ScreenUnderstandingEngine(event_bus=event_bus)
        self.document = DocumentUnderstandingEngine(event_bus=event_bus)
        if verbose:
            print("[+] Vision initialized")

        # 10. Browser
        self.browser = BrowserCapability(event_bus=event_bus)
        if verbose:
            print("[+] Browser initialized")

        # 11. Computer Interaction
        self.computer = ApplicationAdapter(event_bus=event_bus, mock_mode=True)
        if verbose:
            print("[+] Computer interaction initialized")

        # 12. Filesystem
        self.filesystem = FilesystemCapability(event_bus=event_bus)
        if verbose:
            print("[+] Filesystem initialized")

        # 13. Terminal Safety
        self.terminal = TerminalCapability(event_bus=event_bus, mock_mode=True)
        if verbose:
            print("[+] Terminal safety initialized")

        # 14. Autonomous Task Engine
        self.agent = AutonomousTaskEngine(memory_mgr=self.memory, event_bus=event_bus)
        if verbose:
            print("[+] Autonomous task engine initialized")

        # 15. Voice Subsystem
        self.voice = VoiceConversationController(
            session_engine=self.session_engine,
            capability_registry=capability_registry,
            learner_id=self.learner_id,
        )
        if verbose:
            print("[+] Voice subsystem initialized")

        # 16. Unified Companion Router
        self.router = UnifiedCompanionRouter(
            agent_engine=self.agent,
            teaching_engine=self.teaching,
            browser_capability=self.browser,
            app_adapter=self.computer,
            fs_capability=self.filesystem,
            event_bus=event_bus,
        )
        if verbose:
            print("[+] Unified companion initialized")
            print()
            print("[TARKYAAN READY]")
            print()

    def _get_snapshot(self) -> LearnerContextSnapshot:
        """Construct current learner snapshot for context-aware reasoning."""
        mastery = 0.5
        health_str = "healthy"
        if self.adaptive:
            try:
                report = self.adaptive.evaluate_learner_health(self.learner_id)
                health_str = report.overall_health.value
            except Exception:
                pass

        return LearnerContextSnapshot(
            learner_id=self.learner_id,
            active_topic=self.active_topic,
            mastery_score=mastery,
            learning_health=health_str,  # type: ignore[arg-type]
        )

    def run_interactive_cockpit(self) -> int:
        """
        Start the continuous user-facing Interactive Learning Cockpit (REPL).
        Keeps running until user enters /exit, /quit, or sends Ctrl+C.
        """
        self.running = True
        print("Tarkyaan Interactive Learning Cockpit is live.")
        print("Type your questions or study goals naturally, or type '/help' for commands.")
        print("Press Ctrl+C or type '/exit' anytime to safely quit.\n")

        while self.running:
            try:
                prompt = f"Tarkyaan [{self.active_topic}] > "
                user_input = input(prompt).strip()

                if not user_input:
                    continue

                # Handle slash commands
                if user_input.startswith("/"):
                    self._handle_command(user_input)
                    continue

                # Handle natural cancellation keywords
                if user_input.lower() in ["stop", "cancel", "रुको", "रहने दो", "ruk jao"]:
                    if self.router:
                        resp = self.router._handle_cancellation(self.learner_id)
                        print(f"\n[Tarkyaan] {resp.text_response}\n")
                    else:
                        print("\n[Tarkyaan] Stopped all active tasks.\n")
                    continue

                # Process natural language interaction through Unified Companion Router
                self._handle_query(user_input)

            except KeyboardInterrupt:
                print("\n\n[Interrupted] Shutting down Tarkyaan cleanly...")
                self.shutdown()
                return 0
            except EOFError:
                print("\n\n[EOF] Exiting Tarkyaan.")
                self.shutdown()
                return 0
            except Exception as exc:
                print(f"\n[Notice] Tarkyaan handled unexpected condition: {exc}\n")

        self.shutdown()
        return 0

    def _handle_query(self, text: str) -> None:
        """Route conversational query through UnifiedCompanionRouter."""
        if not self.router:
            print("[!] Router not initialized.")
            return

        payload = self.router.multimodal_engine.process_text_input(
            learner_id=self.learner_id,
            text=text,
        )

        snapshot = self._get_snapshot()
        resp: CompanionResponse = self.router.route_interaction(
            input_payload=payload,
            learner_snapshot=snapshot,
            recent_turns=self.recent_turns,
        )

        # Print output
        print(f"\n[Tarkyaan] {resp.text_response}")
        if resp.recommended_next_action:
            print(f"  -> Recommended Next Step: {resp.recommended_next_action}")
        if resp.autonomous_task_id:
            print(f"  -> Task Run ID: {resp.autonomous_task_id}")
        print()

        # Update conversation turns
        self.recent_turns.append({"user": text, "companion": resp.text_response})
        if len(self.recent_turns) > 10:
            self.recent_turns = self.recent_turns[-10:]

    def _handle_command(self, cmd_line: str) -> None:
        """Execute built-in slash command."""
        parts = cmd_line.strip().split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if cmd in ["/exit", "/quit", "/q"]:
            print("\nThank you for learning with Tarkyaan. Have a great session!")
            self.running = False

        elif cmd in ["/help", "/h", "/?"]:
            self._print_help()

        elif cmd in ["/status"]:
            from tarkyaan.__main__ import check_runtime_health
            print()
            check_runtime_health()

        elif cmd in ["/capabilities", "/caps"]:
            from tarkyaan.capabilities import explain_capabilities
            print()
            print(explain_capabilities())

        elif cmd in ["/topic", "/set-topic"]:
            if arg:
                self.active_topic = arg
                print(f"\n[+] Active learning topic changed to: {self.active_topic}\n")
            else:
                print(f"\nCurrent topic: {self.active_topic}. Usage: /topic <topic_name>\n")

        elif cmd in ["/plan", "/roadmap"]:
            self._show_plan()

        elif cmd in ["/progress", "/health"]:
            self._show_progress()

        elif cmd in ["/practice"]:
            self._start_practice(arg or self.active_topic)

        elif cmd in ["/hint"]:
            self._provide_hint()

        elif cmd in ["/solution", "/answer"]:
            self._show_solution()

        elif cmd in ["/research"]:
            topic = arg or self.active_topic
            print(f"\n[Research] Researching resources for '{topic}'...")
            if self.browser:
                res = self.browser.search_web(topic)
                print(f"\n{res.extracted_content}\n")
            else:
                print("Browser capability unavailable.")

        elif cmd in ["/task"]:
            if not arg:
                print("\nUsage: /task <goal description>\nExample: /task Prepare a 30-minute study roadmap for Graph algorithms\n")
                return
            print(f"\n[Agent] Initiating autonomous task: {arg}")
            if self.agent and self.router:
                task_input = self.router.multimodal_engine.process_text_input(
                    learner_id=self.learner_id,
                    text=arg,
                )
                ctx = self.router.context_assembler.assemble_context(
                    current_input=task_input,
                    learner_snapshot=self._get_snapshot(),
                )
                task = self.agent.run_task(
                    learner_id=self.learner_id,
                    goal_text=arg,
                    context=ctx,
                    confirmed_by_user=True,
                )
                print(f"[Agent Status: {task.status.value.upper()}] {task.result_summary}")
                print(f"Steps executed: {len(task.steps)}\n")
            else:
                print("Autonomous task engine unavailable.")

        elif cmd in ["/screen"]:
            print("\n[Vision] Inspecting current screen context...")
            if self.screen:
                obs = self.screen.observe_screen()
                print(f"Detected App: {obs.detected_app}")
                print(f"Active File:  {obs.active_file or 'None'}")
                print(f"Summary:      {obs.pedagogical_summary}\n")
            else:
                print("Screen awareness engine unavailable.")

        else:
            print(f"\nUnknown command '{cmd}'. Type '/help' for a list of commands.\n")

    def _print_help(self) -> None:
        """Display interactive commands reference."""
        print("""
============================================================
              TARKYAAN INTERACTIVE COCKPIT COMMANDS
============================================================

Natural Interaction:
  - Ask questions: "Explain dynamic programming with an analogy"
  - Inquire direction: "What should I do next?"
  - Socratic problem solving: "Why is my binary search loop infinite?"
  - Immediate stop: "stop", "cancel", "रुको"

Slash Commands:
  /help                  Show this cheat sheet
  /topic <name>          Change active learning topic
  /plan                  View curriculum roadmap and upcoming tasks
  /progress              Display learning health and mastery report
  /practice [topic]      Generate a practice challenge
  /hint                  Get a progressive hint for current problem
  /solution              Reveal problem solution and walkthrough
  /research <query>      Curate high-quality learning resources
  /task <goal>           Execute multi-step autonomous task
  /screen                Observe active screen context
  /status                Run subsystem diagnostics
  /capabilities          Display complete capability inventory
  /exit or /quit         Safely shutdown Tarkyaan
============================================================
""")

    def _show_plan(self) -> None:
        """Show active learning roadmap."""
        print(f"\n--- Tarkyaan Learning Roadmap: {self.active_topic} ---")
        if self.memory:
            plan = self.memory.get_active_learning_plan(self.learner_id)
            if plan:
                print(f"Plan ID:   {plan.plan_id}")
                print(f"Goal:      {plan.title}")
                print(f"Status:    {plan.status.value.upper()}")
                print(f"Phases ({len(plan.phases)}):")
                for idx, phase in enumerate(plan.phases, 1):
                    print(f"  {idx}. {phase.name} ({phase.estimated_hours} hrs, status: {phase.status.value})")
            else:
                goals = self.memory.get_goals(self.learner_id)
                print(f"Active Goals: {len(goals)}")
                print(f"To generate a new curriculum plan, ask: 'Help me prepare for {self.active_topic}'")
            print()
        else:
            print("Learning planner unavailable.\n")

    def _show_progress(self) -> None:
        """Show learning health and mastery."""
        print(f"\n--- Tarkyaan Learning Progress Report ---")
        if self.adaptive:
            health = self.adaptive.evaluate_learner_health(self.learner_id)
            print(f"Learner ID:     {self.learner_id}")
            print(f"Active Topic:   {self.active_topic}")
            print(f"Overall Health: {health.health_status.value.upper()}")
            signals = health.signals if hasattr(health, "signals") else []
            print(f"Signals:        {', '.join(signals) if signals else 'Nominal'}")
            print()
        else:
            print("Adaptive engine unavailable.\n")

    def _start_practice(self, topic: str) -> None:
        """Generate and present a practice problem."""
        print(f"\n[Practice] Preparing a problem for: {topic}...")
        if self.practice:
            prob = self.practice.generate_practice(
                concept_id=topic.lower().replace(" ", "_"),
                concept_name=topic,
                difficulty=2,
                learner_id=self.learner_id,
            )
            self.active_practice_question = prob
            self.current_hint_level = 0
            print(f"Question ID: {prob.question_id}")
            print(f"Prompt:      {prob.prompt}")
            print("\nType your answer, or type '/hint' if you get stuck.\n")
        else:
            print("Practice engine unavailable.\n")

    def _provide_hint(self) -> None:
        """Give the next progressive hint."""
        if not self.active_practice_question:
            print("\nNo active practice problem. Type '/practice' to start one.\n")
            return

        from tarkyaan.models.enums import HintLevel
        levels = [
            HintLevel.NUDGE,
            HintLevel.PRINCIPLE,
            HintLevel.DIRECTION,
            HintLevel.STRONG_GUIDANCE,
            HintLevel.NEAR_SOLUTION,
        ]
        if self.current_hint_level < len(levels):
            lvl = levels[self.current_hint_level]
            self.current_hint_level += 1
            if self.practice:
                hint_resp = self.practice.request_hint(
                    question=self.active_practice_question,
                    requested_level=lvl,
                )
                print(f"\n[Hint Tier {self.current_hint_level}: {lvl.name}] {hint_resp.hint_text}\n")
            else:
                print("\nPractice hint engine unavailable.\n")
        else:
            print("\n[Notice] All 5 progressive hint tiers exhausted. Type '/solution' to view answer.\n")

    def _show_solution(self) -> None:
        """Reveal solution for the active problem."""
        if not self.active_practice_question:
            print("\nNo active practice problem. Type '/practice' to start one.\n")
            return
        if self.practice:
            from tarkyaan.models.enums import HintLevel
            hint_resp = self.practice.request_hint(
                question=self.active_practice_question,
                requested_level=HintLevel.FULL_SOLUTION,
                allow_full_solution=True,
            )
            print(f"\n[Solution / Worked Example] {hint_resp.hint_text}\n")
        self.active_practice_question = None
        self.current_hint_level = 0

    def shutdown(self) -> None:
        """Clean shutdown of all child tasks, processes, and memory connections."""
        if self.agent:
            self.agent.cancel_all_active_tasks("Application shutdown")
        if self.browser:
            self.browser.session_mgr.cancel_all("Application shutdown")
        if self.store:
            self.store.close()
        print("[+] All Tarkyaan resources released cleanly.")


def run_app(learner_id: str = "default_learner") -> int:
    """Entry point for running the Tarkyaan application."""
    app = TarkyaanApp(learner_id=learner_id)
    app.bootstrap(verbose=True)
    return app.run_interactive_cockpit()
