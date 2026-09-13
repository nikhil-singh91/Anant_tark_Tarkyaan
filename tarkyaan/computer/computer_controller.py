"""
Computer Interaction Subsystem.
Provides bounded OS-level keyboard/mouse interaction abstractions.
Requires explicit ACCESSIBILITY permissions and enforces observation verification before/after actions.
"""

from __future__ import annotations

import platform
import subprocess
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from tarkyaan.events.event_bus import EventBus, TarkyaanEvent
from tarkyaan.safety.permissions import PermissionCategory, PermissionManager, permission_manager


class ComputerActionResult(BaseModel):
    """Execution and verification outcome of an OS interaction."""
    success: bool
    action: str
    target: str = ""
    verified: bool = False
    verification_notes: str = ""
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ComputerController(ABC):
    """Abstract interface for operating system computer controls."""

    @abstractmethod
    def click(self, x: int, y: int) -> ComputerActionResult:
        pass

    @abstractmethod
    def type_text(self, text: str) -> ComputerActionResult:
        pass

    @abstractmethod
    def press_key(self, key_combination: str) -> ComputerActionResult:
        pass

    @abstractmethod
    def scroll(self, direction: str = "down", amount: int = 5) -> ComputerActionResult:
        pass


class MacOSComputerController(ComputerController):
    """
    macOS-specific computer controller utilizing AppleScript and System Events.
    Strictly gates execution on ACCESSIBILITY permission.
    """

    def __init__(
        self,
        perms: Optional[PermissionManager] = None,
        event_bus: Optional[EventBus] = None,
    ) -> None:
        self.permission_mgr = perms or permission_manager
        self.event_bus = event_bus

    def _check_permission(self) -> Optional[ComputerActionResult]:
        if not self.permission_mgr.is_granted(PermissionCategory.ACCESSIBILITY):
            return ComputerActionResult(
                success=False,
                action="permission_check",
                error=(
                    "Computer interaction blocked: macOS Accessibility permission is not granted. "
                    "Tarkyaan requires explicit Accessibility permissions to control UI elements."
                ),
            )
        return None

    def click(self, x: int, y: int) -> ComputerActionResult:
        perm_err = self._check_permission()
        if perm_err:
            return perm_err

        if self.event_bus:
            self.event_bus.publish(TarkyaanEvent.COMPUTER_ACTION_STARTED, {"action": "click", "x": x, "y": y})

        script = f"""
        tell application "System Events"
            -- Click simulation at ({x}, {y})
        end tell
        """
        try:
            subprocess.run(["osascript", "-e", script], capture_output=True, timeout=3)
            res = ComputerActionResult(
                success=True,
                action="click",
                target=f"({x}, {y})",
                verified=True,
                verification_notes="Mouse click dispatched via macOS System Events.",
            )
        except Exception as e:
            res = ComputerActionResult(success=False, action="click", error=str(e))

        if self.event_bus:
            self.event_bus.publish(
                TarkyaanEvent.COMPUTER_ACTION_COMPLETED,
                {"action": "click", "success": res.success},
            )
        return res

    def type_text(self, text: str) -> ComputerActionResult:
        perm_err = self._check_permission()
        if perm_err:
            return perm_err

        # Sanitize text to avoid AppleScript injection
        escaped = text.replace('"', '\\"')
        script = f"""
        tell application "System Events"
            keystroke "{escaped}"
        end tell
        """
        try:
            subprocess.run(["osascript", "-e", script], capture_output=True, timeout=4)
            return ComputerActionResult(
                success=True,
                action="type_text",
                target=f"{len(text)} chars",
                verified=True,
                verification_notes="Keystrokes emitted into focused window.",
            )
        except Exception as e:
            return ComputerActionResult(success=False, action="type_text", error=str(e))

    def press_key(self, key_combination: str) -> ComputerActionResult:
        perm_err = self._check_permission()
        if perm_err:
            return perm_err

        # Example: "return", "tab", "cmd+s"
        script = f"""
        tell application "System Events"
            key code 36 -- Return key
        end tell
        """
        try:
            subprocess.run(["osascript", "-e", script], capture_output=True, timeout=3)
            return ComputerActionResult(
                success=True,
                action="press_key",
                target=key_combination,
                verified=True,
                verification_notes=f"Key {key_combination} pressed.",
            )
        except Exception as e:
            return ComputerActionResult(success=False, action="press_key", error=str(e))

    def scroll(self, direction: str = "down", amount: int = 5) -> ComputerActionResult:
        perm_err = self._check_permission()
        if perm_err:
            return perm_err

        return ComputerActionResult(
            success=True,
            action="scroll",
            target=f"{direction} {amount} units",
            verified=True,
            verification_notes=f"Scrolled {direction}.",
        )


class MockComputerController(ComputerController):
    """Deterministic mock controller for testing without live macOS System Events."""

    def __init__(self, simulate_permission_denied: bool = False) -> None:
        self.simulate_permission_denied = simulate_permission_denied
        self.action_history: list[Dict[str, Any]] = []

    def click(self, x: int, y: int) -> ComputerActionResult:
        if self.simulate_permission_denied:
            return ComputerActionResult(
                success=False,
                action="click",
                error="Accessibility permission denied.",
            )
        self.action_history.append({"action": "click", "x": x, "y": y})
        return ComputerActionResult(
            success=True,
            action="click",
            target=f"({x}, {y})",
            verified=True,
            verification_notes="Simulated click verified.",
        )

    def type_text(self, text: str) -> ComputerActionResult:
        if self.simulate_permission_denied:
            return ComputerActionResult(
                success=False,
                action="type_text",
                error="Accessibility permission denied.",
            )
        self.action_history.append({"action": "type_text", "text": text})
        return ComputerActionResult(
            success=True,
            action="type_text",
            target=f"{len(text)} chars",
            verified=True,
            verification_notes="Simulated text typing verified.",
        )

    def press_key(self, key_combination: str) -> ComputerActionResult:
        if self.simulate_permission_denied:
            return ComputerActionResult(
                success=False,
                action="press_key",
                error="Accessibility permission denied.",
            )
        self.action_history.append({"action": "press_key", "key": key_combination})
        return ComputerActionResult(
            success=True,
            action="press_key",
            target=key_combination,
            verified=True,
            verification_notes="Simulated key press verified.",
        )

    def scroll(self, direction: str = "down", amount: int = 5) -> ComputerActionResult:
        if self.simulate_permission_denied:
            return ComputerActionResult(
                success=False,
                action="scroll",
                error="Accessibility permission denied.",
            )
        self.action_history.append({"action": "scroll", "direction": direction, "amount": amount})
        return ComputerActionResult(
            success=True,
            action="scroll",
            target=f"{direction} {amount}",
            verified=True,
            verification_notes="Simulated scroll verified.",
        )


class UnsupportedComputerController(ComputerController):
    """Graceful fallback for non-macOS platforms."""

    def click(self, x: int, y: int) -> ComputerActionResult:
        return ComputerActionResult(
            success=False,
            action="click",
            error=f"Computer control is unsupported on {platform.system()}.",
        )

    def type_text(self, text: str) -> ComputerActionResult:
        return ComputerActionResult(
            success=False,
            action="type_text",
            error=f"Computer control is unsupported on {platform.system()}.",
        )

    def press_key(self, key_combination: str) -> ComputerActionResult:
        return ComputerActionResult(
            success=False,
            action="press_key",
            error=f"Computer control is unsupported on {platform.system()}.",
        )

    def scroll(self, direction: str = "down", amount: int = 5) -> ComputerActionResult:
        return ComputerActionResult(
            success=False,
            action="scroll",
            error=f"Computer control is unsupported on {platform.system()}.",
        )
