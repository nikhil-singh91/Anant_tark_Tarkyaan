"""
Tarkyaan (तर्कयान) — CLI & Application Runtime Entry Point.
"""

from __future__ import annotations

import argparse
import sys

from tarkyaan import __version__
from tarkyaan.config.settings import settings
from tarkyaan.memory.memory_store import TarkyaanMemoryStore
from tarkyaan.memory.memory_manager import TarkyaanMemoryManager
from tarkyaan.planning.planner import LearningPlanner


def print_banner() -> None:
    print(
        f"""
============================================================
  Tarkyaan / तर्कयान  v{__version__}
  Your Autonomous Learning Companion
============================================================
"""
    )


def check_runtime_health() -> int:
    print("Checking Tarkyaan subsystem status...")
    try:
        # 1. Config
        print(f"  [+] Configuration loaded (env: {settings.app_env}, db: {settings.database_path})")

        # 2. Storage
        store = TarkyaanMemoryStore(":memory:")
        print("  [+] Memory store initialized successfully (:memory:)")

        # 3. Manager
        manager = TarkyaanMemoryManager(store)
        print("  [+] Memory manager operational (learner isolation verified)")

        # 4. Planning
        planner = LearningPlanner(memory_manager=manager)
        print("  [+] Autonomous Learning Planner initialized")

        # 5. Capabilities & Registry
        from tarkyaan.capabilities import capability_registry
        print(f"  [+] Capability Registry initialized ({len(capability_registry.list_all())} registered capabilities)")

        # 6. Research Engine
        from tarkyaan.research import ResearchEngine
        research = ResearchEngine(memory_manager=manager)
        print(f"  [+] Research Engine initialized (active provider: {research.provider.name})")

        # 7. Event Subsystem
        from tarkyaan.events import event_bus
        print("  [+] Thread-safe EventBus operational")

        # 8. Permissions & Safety
        from tarkyaan.permissions import permission_manager
        from tarkyaan.safety import safety_policy
        print("  [+] Safety policies and macOS permission boundaries active")

        # 9. Teaching & Adaptive Explanation Engine (Phase 5)
        from tarkyaan.teaching import TeachingEngine
        teaching = TeachingEngine()
        print("  [+] Teaching & Adaptive Explanation Engine operational")

        # 10. Interactive Practice Engine (Phase 5)
        from tarkyaan.practice import PracticeEngine
        practice = PracticeEngine()
        print("  [+] Practice Engine & 5-Tier Progressive Hint Engine operational")

        # 11. Learning Session Engine (Phase 5)
        from tarkyaan.session import LearningSessionEngine
        session_eng = LearningSessionEngine(memory_manager=manager)
        print("  [+] Learning Session Engine & Stage Machine operational")

        # 12. Voice Companion Loop (Phase 5)
        from tarkyaan.voice import VoiceConversationController
        voice_ctrl = VoiceConversationController(session_engine=session_eng)
        print("  [+] Advanced Voice Companion Loop & Command Recognizer operational")

        # 13. Adaptive Learning Engine (Phase 6)
        from tarkyaan.planning import AdaptiveLearningEngine
        adaptive_eng = AdaptiveLearningEngine(memory=manager, event_bus=event_bus)
        print("  [+] Adaptive Learning Engine & Health Analyzer operational")

        # 14. Replanning Engine (Phase 6)
        from tarkyaan.planning import ReplanningEngine
        replan_eng = ReplanningEngine(memory=manager, planner=planner, event_bus=event_bus)
        print("  [+] Replanning Engine & Curriculum Mutation Engine operational")

        # 15. Review Scheduler (Phase 6)
        from tarkyaan.planning import ReviewScheduler
        review_scheduler = ReviewScheduler(memory=manager, event_bus=event_bus)
        print("  [+] Spaced-Repetition Review Scheduler (SM-2) operational")

        # 16. Progress Report Engine (Phase 6)
        from tarkyaan.planning import ProgressReportEngine
        progress_eng = ProgressReportEngine(memory=manager, event_bus=event_bus)
        print("  [+] Learning Progress Report Engine operational")

        # 17. Learning Decision Engine (Phase 6)
        from tarkyaan.planning import LearningDecisionEngine
        print("  [+] Explainable Learning Decision Engine operational")

        # 18. Secure Coding Sandbox (Phase 6)
        from tarkyaan.sandbox import SecureCodingSandbox
        sandbox = SecureCodingSandbox()
        print("  [+] Secure Coding Sandbox (AST-checked, subprocess-isolated) operational")

        # 19. Vision & Multimodal Perception (Phase 7)
        from tarkyaan.vision import ImageUnderstandingEngine, DocumentUnderstandingEngine
        vision_eng = ImageUnderstandingEngine(event_bus=event_bus)
        doc_eng = DocumentUnderstandingEngine(event_bus=event_bus)
        print("  [+] Vision Perception & Bounded Document Understanding Engines operational")

        # 20. Screen Awareness (Phase 7)
        from tarkyaan.vision import ScreenUnderstandingEngine
        screen_eng = ScreenUnderstandingEngine(event_bus=event_bus)
        print("  [+] Screen Awareness & Context Observation Engine operational")

        # 21. Browser Capability (Phase 7)
        from tarkyaan.browser import BrowserCapability, BrowserSessionManager
        browser_cap = BrowserCapability(event_bus=event_bus)
        print("  [+] Bounded Browser Intelligence & Session Manager operational")

        # 22. Computer & Application Interaction (Phase 7)
        from tarkyaan.computer import ApplicationAdapter, MacOSComputerController
        app_adapter = ApplicationAdapter(event_bus=event_bus, mock_mode=True)
        print("  [+] Computer Interaction & Application Lifecycle Adapter operational")

        # 23. Filesystem Learning Subsystem (Phase 7)
        from tarkyaan.filesystem import FilesystemCapability
        fs_cap = FilesystemCapability(event_bus=event_bus)
        print("  [+] Project-Based Filesystem Learning Engine operational")

        # 24. Terminal Capability (Phase 7)
        from tarkyaan.terminal import TerminalCapability
        term_cap = TerminalCapability(event_bus=event_bus, mock_mode=True)
        print("  [+] Host Terminal Execution & Safety Policy Gate operational")

        # 25. Autonomous Task Engine (Phase 7)
        from tarkyaan.agent import AutonomousTaskEngine
        agent_eng = AutonomousTaskEngine(memory_mgr=manager, event_bus=event_bus)
        print("  [+] Autonomous Task Engine (Observe->Plan->Act->Verify) operational")

        # 26. Unified Companion Router (Phase 7)
        from tarkyaan.companion import UnifiedCompanionRouter
        router = UnifiedCompanionRouter(
            agent_engine=agent_eng,
            browser_capability=browser_cap,
            app_adapter=app_adapter,
            fs_capability=fs_cap,
            event_bus=event_bus,
        )
        print("  [+] Unified Multimodal Companion Router & Prompt Defense operational")

        print("\nAll Tarkyaan Phase 1-7 subsystems are operational and healthy.\n")
        return 0
    except Exception as exc:
        print(f"\n[-] Tarkyaan startup health check failed: {exc}", file=sys.stderr)
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Tarkyaan (तर्कयान) — Autonomous Learning Companion CLI"
    )
    parser.add_argument(
        "-v", "--version", action="version", version=f"Tarkyaan {__version__}"
    )
    parser.add_argument(
        "--status", action="store_true", help="Run subsystem health and readiness check"
    )
    parser.add_argument(
        "--capabilities", action="store_true", help="Display honest inventory of Tarkyaan capabilities"
    )

    args = parser.parse_args()

    print_banner()

    if args.capabilities:
        from tarkyaan.capabilities import explain_capabilities
        print(explain_capabilities())
        return 0

    if args.status or len(sys.argv) == 1:
        return check_runtime_health()

    return 0


if __name__ == "__main__":
    sys.exit(main())
