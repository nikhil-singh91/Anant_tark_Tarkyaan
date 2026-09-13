"""
Tests for Tarkyaan Master Launcher (main.py) and Interactive Cockpit (app.py).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from tarkyaan.app import TarkyaanApp
from tarkyaan.models.enums import HealthStatus


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_main_cli_version():
    """Verify python main.py --version returns 0 and version string."""
    res = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "main.py"), "--version"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
    )
    assert res.returncode == 0
    assert "Tarkyaan" in res.stdout


def test_main_cli_status():
    """Verify python main.py --status runs diagnostics across all subsystems."""
    res = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "main.py"), "--status"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
    )
    assert res.returncode == 0
    assert "All Tarkyaan Phase 1-7 subsystems are operational and healthy." in res.stdout


def test_main_cli_capabilities():
    """Verify python main.py --capabilities outputs verified capability inventory."""
    res = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "main.py"), "--capabilities"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
    )
    assert res.returncode == 0
    assert "=== Tarkyaan Capability Inventory ===" in res.stdout
    assert "agent.orchestrate_task" in res.stdout


def test_app_bootstrap_and_components():
    """Verify TarkyaanApp bootstraps all Phase 1-7 subsystems properly."""
    app = TarkyaanApp(learner_id="test_learner_unit", active_topic="Algorithms")
    app.bootstrap(verbose=False)

    assert app.store is not None
    assert app.memory is not None
    assert app.planner is not None
    assert app.teaching is not None
    assert app.practice is not None
    assert app.session_engine is not None
    assert app.adaptive is not None
    assert app.replanning is not None
    assert app.research is not None
    assert app.vision is not None
    assert app.screen is not None
    assert app.browser is not None
    assert app.computer is not None
    assert app.filesystem is not None
    assert app.terminal is not None
    assert app.agent is not None
    assert app.voice is not None
    assert app.router is not None

    # Test snapshot generation
    snapshot = app._get_snapshot()
    assert snapshot.learner_id == "test_learner_unit"
    assert snapshot.active_topic == "Algorithms"

    # Test practice problem generation
    app._start_practice("Binary Search")
    assert app.active_practice_question is not None
    assert app.current_hint_level == 0

    # Test progressive hints
    app._provide_hint()
    assert app.current_hint_level == 1

    # Test solution reveal
    app._show_solution()
    assert app.active_practice_question is None

    # Test clean shutdown
    app.shutdown()


def test_app_interactive_session_execution():
    """Verify interactive loop processes input and exits cleanly."""
    input_cmds = "What should I do next?\n/help\n/progress\n/exit\n"
    res = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "main.py")],
        input=input_cmds,
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
    )
    assert res.returncode == 0
    assert "TARKYAAN / तर्कयान" in res.stdout
    assert "[TARKYAAN READY]" in res.stdout
    assert "Recommended Next Step" in res.stdout
    assert "TARKYAAN INTERACTIVE COCKPIT COMMANDS" in res.stdout
    assert "All Tarkyaan resources released cleanly." in res.stdout
