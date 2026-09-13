"""
Agent Observability and Audit Subsystem.
Maintains structured logs and timelines of agent steps, decisions, and outcomes.
Enforces automatic secret redaction so sensitive credentials never appear in telemetry.
"""

from __future__ import annotations

import re
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AuditEntry(BaseModel):
    """An observable timeline entry for an autonomous task action."""
    entry_id: str
    task_id: str
    step_index: int
    capability_id: str
    action: str
    risk_level: str
    status: str
    details: str
    is_verified: bool = False
    timestamp: datetime = Field(default_factory=_utc_now)


class AgentObservabilityRecorder:
    """
    Thread-safe observability recorder for autonomous tasks.
    Masks passwords, API keys, and sensitive tokens from all logged entries.
    """

    SECRET_PATTERNS = [
        (r"(sk-[a-zA-Z0-9]{20,})", "[REDACTED_API_KEY]"),
        (r"(AIza[0-9A-Za-z-_]{35})", "[REDACTED_GOOGLE_KEY]"),
        (r"(ghp_[a-zA-Z0-9]{36})", "[REDACTED_GITHUB_TOKEN]"),
        (r"(Bearer\s+[a-zA-Z0-9_\-\.]{20,})", "Bearer [REDACTED_TOKEN]"),
        (r"(password\s*=\s*['\"][^'\"]+['\"])", "password=[REDACTED]"),
    ]

    def __init__(self) -> None:
        self._entries: List[AuditEntry] = []
        self._lock = threading.RLock()

    def record_step_event(
        self,
        task_id: str,
        step_index: int,
        capability_id: str,
        action: str,
        risk_level: str,
        status: str,
        details: str,
        is_verified: bool = False,
    ) -> AuditEntry:
        """Record a sanitized step event into the observable timeline."""
        sanitized_details = self.redact_secrets(details)
        entry = AuditEntry(
            entry_id=f"aud_{len(self._entries) + 1}",
            task_id=task_id,
            step_index=step_index,
            capability_id=capability_id,
            action=action,
            risk_level=risk_level,
            status=status,
            details=sanitized_details,
            is_verified=is_verified,
        )
        with self._lock:
            self._entries.append(entry)
        return entry

    def get_task_timeline(self, task_id: str) -> List[AuditEntry]:
        """Retrieve all audit entries for a specific task in chronological order."""
        with self._lock:
            return [e for e in self._entries if e.task_id == task_id]

    @classmethod
    def redact_secrets(cls, text: str) -> str:
        """Redact known secret patterns from a string."""
        if not text:
            return ""
        redacted = text
        for pattern, replacement in cls.SECRET_PATTERNS:
            redacted = re.sub(pattern, replacement, redacted)
        return redacted
