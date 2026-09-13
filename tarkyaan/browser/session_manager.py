"""
Browser Session Management Subsystem.
Tracks browser sessions with bounded lifetimes, action budgets, cancellation tokens, and audit logs.
"""

from __future__ import annotations

import threading
import time
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from tarkyaan.models.enums import BrowserActionType


class BrowserSession(BaseModel):
    """Encapsulates an isolated, bounded browser interaction session."""
    session_id: str
    current_url: str = "about:blank"
    is_active: bool = True
    created_at: float = Field(default_factory=time.time)
    timeout_seconds: int = 120
    max_actions: int = 15
    actions_performed: int = 0
    history: List[Dict[str, Any]] = Field(default_factory=list)
    cancelled: bool = False
    cancellation_reason: Optional[str] = None

    def is_expired(self) -> bool:
        """Check if session exceeded its maximum allotted lifetime."""
        return (time.time() - self.created_at) > self.timeout_seconds

    def has_remaining_budget(self) -> bool:
        """Check if session is still within its action count budget."""
        return self.actions_performed < self.max_actions and not self.cancelled and self.is_active


class BrowserSessionManager:
    """
    Manages active browser sessions.
    Guarantees bounded lifetimes, prevents leaked background sessions, and handles instant cancellation.
    """

    def __init__(self, default_timeout_seconds: int = 120, default_max_actions: int = 15) -> None:
        self.default_timeout = default_timeout_seconds
        self.default_max_actions = default_max_actions
        self._sessions: Dict[str, BrowserSession] = {}
        self._lock = threading.RLock()

    def create_session(
        self,
        initial_url: str = "about:blank",
        timeout_seconds: Optional[int] = None,
        max_actions: Optional[int] = None,
    ) -> BrowserSession:
        """Create a new bounded browser session."""
        session_id = f"brows_{uuid.uuid4().hex[:8]}"
        session = BrowserSession(
            session_id=session_id,
            current_url=initial_url,
            timeout_seconds=timeout_seconds or self.default_timeout,
            max_actions=max_actions or self.default_max_actions,
        )
        with self._lock:
            self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[BrowserSession]:
        """Retrieve a session by ID."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session and session.is_expired():
                session.is_active = False
            return session

    def record_action(
        self,
        session_id: str,
        action_type: BrowserActionType,
        target: str = "",
        result_status: str = "success",
    ) -> bool:
        """
        Record an action against the session budget.
        Returns False if budget exceeded or session cancelled.
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if not session or not session.has_remaining_budget() or session.is_expired():
                return False

            session.actions_performed += 1
            session.history.append({
                "action": action_type.value,
                "target": target,
                "status": result_status,
                "timestamp": time.time(),
            })
            if session.actions_performed >= session.max_actions:
                session.is_active = False
            return True

    def cancel_session(self, session_id: str, reason: str = "User requested cancellation") -> bool:
        """Immediately cancel and terminate a browser session."""
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return False
            session.cancelled = True
            session.cancellation_reason = reason
            session.is_active = False
            return True

    def cancel_all(self, reason: str = "Global stop requested") -> int:
        """Cancel all active browser sessions."""
        cancelled_count = 0
        with self._lock:
            for session in self._sessions.values():
                if session.is_active and not session.cancelled:
                    session.cancelled = True
                    session.cancellation_reason = reason
                    session.is_active = False
                    cancelled_count += 1
        return cancelled_count

    def close_session(self, session_id: str) -> bool:
        """Cleanly close a session upon completion."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session:
                session.is_active = False
                return True
            return False
