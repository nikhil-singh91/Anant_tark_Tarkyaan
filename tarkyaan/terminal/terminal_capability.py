"""
Terminal Capability Subsystem.
Safe host terminal execution pipeline:
CommandIntent -> SafetyPolicy -> RiskClassification -> Permission -> Execution -> Verification.
Strictly distinct from SecureCodingSandbox.
"""

from __future__ import annotations

import os
import re
import shlex
import subprocess
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from tarkyaan.events.event_bus import EventBus, TarkyaanEvent
from tarkyaan.models.enums import AgentRiskLevel
from tarkyaan.safety.permissions import PermissionCategory, PermissionManager, permission_manager


class CommandIntent(BaseModel):
    """Structured representation of a desired terminal shell command."""
    command: str
    purpose: str = "Learning verification or build check"
    working_directory: Optional[str] = None
    timeout_seconds: int = 15


class TerminalExecutionResult(BaseModel):
    """Outcome and safety verification of a shell command execution."""
    success: bool
    command: str
    risk_level: AgentRiskLevel
    exit_code: int = 0
    stdout: str = ""
    stderr: str = ""
    blocked_by_safety: bool = False
    requires_confirmation: bool = False
    error: Optional[str] = None
    execution_time_seconds: float = 0.0


class TerminalCapability:
    """
    Host terminal execution controller.
    Validates command safety, blocks destructive shell operations,
    and enforces explicit permission and confirmation gates.
    """

    # Destructive or unsafe commands that are unconditionally blocked
    BLOCKED_PATTERNS = [
        r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*\s+)?(\/|~|\.\.)",  # rm -rf / or ~ or ..
        r"\bmkfs\b",
        r"\bdd\s+if=",
        r"\bshutdown\b",
        r"\breboot\b",
        r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;",          # Fork bomb
        r"\|\s*(bash|sh|zsh)\b",                          # curl ... | bash
        r">\s*\/dev\/sd[a-z]",
        r">\s*\/dev\/null",
        r"\bchmod\s+-R\s+777\s+\/",
    ]

    ALLOWED_SAFE_COMMANDS = {
        "python", "python3", "pytest", "node", "npm", "git",
        "ls", "dir", "cat", "echo", "pwd", "which", "whoami",
        "grep", "find", "cargo", "go", "gcc", "g++", "javac", "java"
    }

    def __init__(
        self,
        perms: Optional[PermissionManager] = None,
        event_bus: Optional[EventBus] = None,
        mock_mode: bool = False,
    ) -> None:
        self.permission_mgr = perms or permission_manager
        self.event_bus = event_bus
        self.mock_mode = mock_mode

    def classify_risk(self, command: str) -> AgentRiskLevel:
        """Classify command into safety risk tier."""
        cmd_clean = command.strip()
        # 1. Check critical blocks
        for pat in self.BLOCKED_PATTERNS:
            if re.search(pat, cmd_clean, re.IGNORECASE):
                return AgentRiskLevel.CRITICAL

        tokens = cmd_clean.split()
        base_cmd = os.path.basename(tokens[0]) if tokens else ""

        # Read-only or inspection
        if base_cmd in {"ls", "pwd", "which", "echo", "cat", "whoami"} and ">" not in cmd_clean:
            return AgentRiskLevel.LOW

        # Safe testing / compilation
        if base_cmd in {"pytest", "python", "python3", "git", "node", "npm"} and "rm" not in cmd_clean:
            return AgentRiskLevel.MEDIUM

        return AgentRiskLevel.HIGH

    def execute_command(
        self,
        intent: CommandIntent,
        confirmed_by_user: bool = False,
    ) -> TerminalExecutionResult:
        """
        Execute command following the safety pipeline:
        Intent -> Policy Check -> Risk Classification -> Permission Gate -> Subprocess Execution.
        """
        cmd = intent.command.strip()
        risk = self.classify_risk(cmd)

        # 1. Unconditional block for critical risk
        if risk == AgentRiskLevel.CRITICAL:
            return TerminalExecutionResult(
                success=False,
                command=cmd,
                risk_level=risk,
                blocked_by_safety=True,
                error="Security block: Critical destructive command detected and prohibited.",
            )

        # 2. Confirmation gate for HIGH risk commands
        if risk == AgentRiskLevel.HIGH and not confirmed_by_user:
            return TerminalExecutionResult(
                success=False,
                command=cmd,
                risk_level=risk,
                requires_confirmation=True,
                error="Action requires explicit user confirmation before host execution.",
            )

        # 3. Permission check
        if not self.permission_mgr.is_granted(PermissionCategory.TERMINAL):
            # Check if restricted or denied
            status = self.permission_mgr.get_status(PermissionCategory.TERMINAL)
            if status != "granted":
                return TerminalExecutionResult(
                    success=False,
                    command=cmd,
                    risk_level=risk,
                    error=f"Terminal permission not granted (Status: {status.value if hasattr(status, 'value') else status}). Explicit permission required.",
                )

        if self.event_bus:
            self.event_bus.publish(
                TarkyaanEvent.TERMINAL_ACTION_STARTED,
                {"command": cmd, "risk": risk.value},
            )

        # 4. Mock mode for testing
        if self.mock_mode:
            res = TerminalExecutionResult(
                success=True,
                command=cmd,
                risk_level=risk,
                exit_code=0,
                stdout=f"Simulated execution output for `{cmd}`: Tests passed (100%).\n",
            )
            self._notify_completed(res)
            return res

        # 5. Bounded Subprocess Execution
        import time
        start_t = time.time()
        cwd = intent.working_directory or os.getcwd()

        try:
            proc = subprocess.run(
                cmd,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=intent.timeout_seconds,
            )
            duration = time.time() - start_t
            res = TerminalExecutionResult(
                success=proc.returncode == 0,
                command=cmd,
                risk_level=risk,
                exit_code=proc.returncode,
                stdout=proc.stdout[:4000],  # Bounded output
                stderr=proc.stderr[:4000],
                execution_time_seconds=duration,
            )
        except subprocess.TimeoutExpired:
            res = TerminalExecutionResult(
                success=False,
                command=cmd,
                risk_level=risk,
                exit_code=-1,
                error=f"Command timed out after {intent.timeout_seconds} seconds.",
            )
        except Exception as e:
            res = TerminalExecutionResult(
                success=False,
                command=cmd,
                risk_level=risk,
                exit_code=-1,
                error=f"Execution error: {str(e)}",
            )

        self._notify_completed(res)
        return res

    def _notify_completed(self, res: TerminalExecutionResult) -> None:
        if self.event_bus:
            self.event_bus.publish(
                TarkyaanEvent.TERMINAL_ACTION_COMPLETED,
                {"command": res.command, "exit_code": res.exit_code, "success": res.success},
            )
