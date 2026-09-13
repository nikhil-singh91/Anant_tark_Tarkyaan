"""Tests for Computer Interaction, Application Adapters, and Verification."""

from __future__ import annotations

import pytest

from tarkyaan.computer.application_adapter import AppActionResult, ApplicationAdapter
from tarkyaan.computer.computer_controller import (
    ComputerActionResult,
    MacOSComputerController,
    MockComputerController,
    UnsupportedComputerController,
)
from tarkyaan.safety.permissions import PermissionCategory, PermissionManager


def test_mock_computer_controller_actions():
    """Verify mock computer controller records and verifies atomic mouse/keyboard actions."""
    controller = MockComputerController()
    click_res: ComputerActionResult = controller.click(100, 250)
    assert click_res.success is True
    assert click_res.verified is True
    assert click_res.target == "(100, 250)"

    type_res: ComputerActionResult = controller.type_text("python3 -m unittest")
    assert type_res.success is True
    assert type_res.verified is True

    key_res: ComputerActionResult = controller.press_key("return")
    assert key_res.success is True
    assert key_res.verified is True

    assert len(controller.action_history) == 3


def test_macos_computer_controller_accessibility_gate():
    """Verify macOS computer controller blocks actions when Accessibility permission is denied."""
    perms = PermissionManager()
    perms.revoke(PermissionCategory.ACCESSIBILITY)

    mac_ctrl = MacOSComputerController(perms=perms)
    res = mac_ctrl.click(50, 50)
    assert res.success is False
    assert "Accessibility permission is not granted" in str(res.error)


def test_unsupported_computer_controller_fallback():
    """Verify non-macOS controller reports unsupported status gracefully."""
    ctrl = UnsupportedComputerController()
    res = ctrl.click(10, 10)
    assert res.success is False
    assert "unsupported" in str(res.error).lower()


def test_application_adapter_lifecycle():
    """Verify application adapter launches, focuses, and verifies running state."""
    adapter = ApplicationAdapter(mock_mode=True)

    # Check initially running in mock mode
    assert adapter.is_running("Visual Studio Code") is True

    # Open app
    open_res: AppActionResult = adapter.open_app("Visual Studio Code", path="/path/to/dsa_project")
    assert open_res.success is True
    assert open_res.verified is True
    assert open_res.app_name == "Visual Studio Code"

    # Focus app
    focus_res: AppActionResult = adapter.focus_app("Terminal")
    assert focus_res.success is True
    assert focus_res.verified is True
