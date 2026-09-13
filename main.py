#!/usr/bin/env python3
"""
Tarkyaan (तर्कयान) — One-Command Master Launcher.

Usage:
    python main.py              # Launches complete Tarkyaan interactive application
    python main.py --status     # Runs subsystem diagnostics
    python main.py --capabilities # Displays capability inventory
    python main.py --version    # Displays application version
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

# 1. Environment & Path Verification
PROJECT_ROOT = Path(__file__).resolve().parent

# Ensure project root is at the front of sys.path
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def verify_environment() -> None:
    """Validate that we are running from project root and dependencies exist."""
    # Check project structure
    if not (PROJECT_ROOT / "pyproject.toml").exists() or not (PROJECT_ROOT / "tarkyaan").is_dir():
        print(
            f"[-] Error: main.py must be run from the Tarkyaan project root.\n"
            f"    Current root: {PROJECT_ROOT}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Check Python version
    if sys.version_info < (3, 10):
        print(
            f"[-] Error: Tarkyaan requires Python 3.10+. Current version: {sys.version}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Check key dependencies
    try:
        import pydantic  # noqa: F401
    except ImportError:
        print(
            "[-] Error: Missing required dependencies.\n"
            "    Please activate your virtual environment:\n"
            "        source .venv/bin/activate\n"
            "    Or install dependencies with:\n"
            "        pip install -e .\n",
            file=sys.stderr,
        )
        sys.exit(1)


def main() -> int:
    verify_environment()

    # Parse command-line options
    from tarkyaan import __version__

    parser = argparse.ArgumentParser(
        prog="python main.py",
        description="Tarkyaan (तर्कयान) — Autonomous AI Learning Companion Master Launcher",
    )
    parser.add_argument(
        "-v", "--version", action="version", version=f"Tarkyaan {__version__}"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Run comprehensive Phase 1-7 subsystem health check",
    )
    parser.add_argument(
        "--capabilities",
        action="store_true",
        help="Display complete inventory of all 33 verified Tarkyaan capabilities",
    )

    args = parser.parse_args()

    # Handle diagnostic options
    if args.status:
        from tarkyaan.__main__ import check_runtime_health
        return check_runtime_health()

    if args.capabilities:
        from tarkyaan.capabilities import explain_capabilities
        print(explain_capabilities())
        return 0

    # Master Application Launch
    try:
        from tarkyaan.app import run_app
        return run_app()
    except KeyboardInterrupt:
        print("\n[Tarkyaan Master Launcher] Clean shutdown requested. Goodbye!")
        return 0
    except Exception as exc:
        print(f"\n[-] Tarkyaan runtime failed to start: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
