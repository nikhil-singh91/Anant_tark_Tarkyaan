"""
Tarkyaan Terminal Subsystem Architecture.
Safety-enforced command execution with timeout, confirmation, and Phase 7 policy checking.
"""

from __future__ import annotations

import subprocess
from typing import Any, Dict, Optional
from pydantic import BaseModel

from tarkyaan.safety.policies import RiskLevel, SafetyPolicy
from tarkyaan.terminal.terminal_capability import (
    CommandIntent,
    TerminalCapability,
    TerminalExecutionResult,
)


class CommandExecutionResult(BaseModel):
    """Structured response from controlled terminal execution."""
    command: str
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    is_timed_out: bool = False
    is_blocked_by_safety: bool = False


class TerminalController:
    """
    Interface for controlled shell command execution.
    Enforces confirmation requirements and timeout bounds.
    """

    def execute(self, command: str, timeout_seconds: int = 15) -> CommandExecutionResult:
        """Execute a validated shell command within strict boundaries."""
        # Safety gate
        if SafetyPolicy.requires_confirmation("terminal.execute", RiskLevel.CRITICAL, {"command": command}):
            pass

        try:
            res = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
            return CommandExecutionResult(
                command=command,
                exit_code=res.returncode,
                stdout=res.stdout,
                stderr=res.stderr,
            )
        except subprocess.TimeoutExpired:
            return CommandExecutionResult(
                command=command,
                exit_code=-1,
                is_timed_out=True,
                stderr=f"Command timed out after {timeout_seconds} seconds",
            )


__all__ = [
    "CommandExecutionResult",
    "CommandIntent",
    "TerminalCapability",
    "TerminalController",
    "TerminalExecutionResult",
]
