"""Tests for Tarkyaan Voice, Browser, Terminal, Mac, and Environment Subsystems."""

import pytest

from tarkyaan.browser import BrowserManager
from tarkyaan.environment import EnvironmentContext, EnvironmentObserver
from tarkyaan.mac import MacAppController, MacAppInfo
from tarkyaan.terminal import CommandExecutionResult, TerminalController
from tarkyaan.voice import VoiceDialogueTurn, VoiceManager, VoiceState


def test_voice_manager_lifecycle_and_interrupt():
    """Verify voice state transitions, dialogue model, and speech interruption."""
    vm = VoiceManager()
    assert vm.state == VoiceState.IDLE
    assert vm.is_listening() is False
    assert vm.is_speaking() is False

    vm.state = VoiceState.SPEAKING
    assert vm.is_speaking() is True

    vm.interrupt()
    assert vm.state == VoiceState.INTERRUPTED
    assert vm.is_speaking() is False

    turn = VoiceDialogueTurn(
        user_transcript="How does binary search maintain its invariant?",
        companion_response="Binary search maintains the invariant that if the target exists, it is within [low, high].",
        detected_language="en",
        duration_seconds=3.2,
    )
    assert turn.duration_seconds == 3.2
    assert "invariant" in turn.user_transcript


def test_browser_manager_interface():
    """Verify browser manager can be instantiated and exposes navigation interface."""
    bm = BrowserManager(browser_name="chrome")
    assert bm.browser_name == "chrome"
    # Should not crash even without opening window in headless test runner
    assert hasattr(bm, "open_url")


def test_terminal_controller_controlled_execution():
    """Verify terminal controller executes bounded commands and captures stdout/stderr."""
    tc = TerminalController()
    # Execute a safe, deterministic echo command
    res = tc.execute("echo 'Tarkyaan Terminal Control'", timeout_seconds=5)

    assert isinstance(res, CommandExecutionResult)
    assert res.exit_code == 0
    assert "Tarkyaan Terminal Control" in res.stdout.strip()
    assert res.is_timed_out is False


def test_mac_app_controller_interface():
    """Verify macOS application discovery and interface."""
    mac = MacAppController()
    assert mac.is_available() is True
    apps = mac.list_running_apps()
    assert isinstance(apps, list)
    assert len(apps) > 0

    info = MacAppInfo(
        name="Visual Studio Code",
        bundle_id="com.microsoft.VSCode",
        is_running=True,
    )
    assert info.is_running is True
    assert info.bundle_id == "com.microsoft.VSCode"


def test_environment_observer_context_tracking():
    """Verify environment observer produces and updates desktop and learning context snapshots."""
    observer = EnvironmentObserver()
    ctx = observer.get_current_context()
    assert isinstance(ctx, EnvironmentContext)

    # Update educational context
    observer.update_learning_context(
        learner_id="learner_99",
        goal_id="goal_algorithms",
        plan_id="plan_dsa",
        task_id="task_001",
        concept_id="recursion",
    )
    updated_ctx = observer.get_current_context()
    assert updated_ctx.active_goal_id == "goal_algorithms"
    assert updated_ctx.active_concept_id == "recursion"

    # Update workspace context
    observer.update_workspace_context(
        active_app="Visual Studio Code",
        file_path="/workspace/tarkyaan/research/evaluator.py",
        selected_text="def evaluate(...) -> ResourceDimensionScores:",
    )
    ws_ctx = observer.get_current_context()
    assert ws_ctx.active_application == "Visual Studio Code"
    assert ws_ctx.active_file_path == "/workspace/tarkyaan/research/evaluator.py"
    assert ws_ctx.selected_text is not None
    assert "def evaluate" in ws_ctx.selected_text
