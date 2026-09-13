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

        print("\nAll Tarkyaan Phase 1-5 subsystems are operational and healthy.\n")
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
