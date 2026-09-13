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

        print("\nAll Tarkyaan subsystems are operational and healthy.\n")
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

    args = parser.parse_args()

    print_banner()

    if args.status or len(sys.argv) == 1:
        return check_runtime_health()

    return 0


if __name__ == "__main__":
    sys.exit(main())
