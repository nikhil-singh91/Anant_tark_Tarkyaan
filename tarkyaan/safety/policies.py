"""
Tarkyaan Safety Policies, Risk Tiers, and Prompt Injection Guards.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """Operational risk level associated with a capability or task step."""
    LOW = "low"            # Pure query, reading public resources, internal memory updates
    MEDIUM = "medium"      # Opening a browser tab, read-only file access, launching safe app
    HIGH = "high"          # File creation, script execution, network request with side-effects
    CRITICAL = "critical"  # File deletion, terminal execution, system settings modification


class ConfirmationStatus(str, Enum):
    """Status of user confirmation for sensitive or dangerous operations."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    TIMED_OUT = "timed_out"


import uuid
from datetime import datetime, timezone

def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ConfirmationRequest(BaseModel):
    """Structured confirmation prompt presented to the user before high-risk execution."""
    request_id: str = Field(default_factory=lambda: f"req_{uuid.uuid4().hex[:8]}")
    action_name: str
    risk_level: RiskLevel
    description: str = ""
    target_description: str = ""
    command_preview: Optional[str] = None
    affected_targets: List[str] = Field(default_factory=list)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    status: ConfirmationStatus = Field(default=ConfirmationStatus.PENDING)
    confirmed_at: Optional[datetime] = None

    def confirm(self) -> None:
        """Approve and confirm the requested high-risk operation."""
        self.status = ConfirmationStatus.CONFIRMED
        self.confirmed_at = _utc_now()

    def reject(self) -> None:
        """Reject and block the requested high-risk operation."""
        self.status = ConfirmationStatus.REJECTED


class PromptInjectionGuard:
    """
    Sanitizes and evaluates untrusted external content (web pages, search snippets, code examples)
    to prevent prompt injection and arbitrary instruction execution.
    """

    # Common injection patterns in untrusted web content
    INJECTION_PATTERNS = [
        r"ignore\s+(previous|prior|above|all)\s+instructions",
        r"disregard\s+(previous|prior|system)\s+prompts?",
        r"you\s+are\s+now\s+in\s+developer\s+mode",
        r"system\s+(prompt\s+)?override",
        r"execute\s+this\s+(command|code|terminal)",
        r"delete\s+all\s+files",
        r"rm\s+-rf",
        r"sudo\s+",
        r"reveal\s+all\s+(api\s*keys?|secrets?|passwords?)",
        r"output\s+your\s+api\s*keys?",
        r"bypass\s+safety\s+restrictions",
    ]

    _COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]

    @classmethod
    def analyze_content(cls, raw_text: str) -> Tuple[bool, List[str]]:
        """
        Analyze untrusted text for known prompt injection signatures.
        Returns (is_suspicious, matched_patterns).
        """
        matches = []
        for pattern in cls._COMPILED_PATTERNS:
            found = pattern.findall(raw_text)
            if found:
                matches.append(pattern.pattern)
        return len(matches) > 0, matches

    @classmethod
    def is_suspicious(cls, raw_text: str) -> bool:
        """Check if raw text contains any prompt injection signatures."""
        return cls.analyze_content(raw_text)[0]

    @classmethod
    def sanitize(cls, raw_text: str, max_length: int = 15000) -> str:
        """
        Sanitize untrusted content: truncates excessive length, strips control characters,
        and wraps content as strictly untrusted reference data.
        """
        if not raw_text:
            return ""

        # Remove null bytes and non-printable control chars except tabs/newlines
        clean = "".join(ch for ch in raw_text if ch in ("\n", "\r", "\t") or (32 <= ord(ch) <= 126) or ord(ch) > 127)

        if len(clean) > max_length:
            clean = clean[:max_length] + " ... [TRUNCATED_BY_SAFETY_GUARD]"

        return clean

    sanitize_text = sanitize



class SafetyPolicy:
    """
    Determines confirmation requirements and blocks dangerous actions.
    """

    DESTRUCTIVE_COMMANDS = {
        "rm", "rmdir", "del", "format", "mkfs", "dd", "shutdown", "reboot", "kill", "killall"
    }

    @classmethod
    def requires_confirmation(cls, action_name: str, risk_level: RiskLevel, params: Dict[str, Any]) -> bool:
        """Evaluate if an action requires explicit learner or user confirmation."""
        if risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            return True

        # Check for destructive targets
        if any(cmd in action_name.lower() for cmd in cls.DESTRUCTIVE_COMMANDS):
            return True

        # Check specific parameter danger
        cmd_str = str(params.get("command", "")).lower()
        if any(d in cmd_str for d in cls.DESTRUCTIVE_COMMANDS):
            return True

        return False


safety_policy = SafetyPolicy()

