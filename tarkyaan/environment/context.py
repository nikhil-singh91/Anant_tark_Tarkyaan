"""
Environment Context Model for Tarkyaan.
Represents the user's desktop, application, and active learning environment.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class EnvironmentContext(BaseModel):
    """
    Snapshot of the user's active workspace and OS environment (Tarkyaan EYES).
    Used to resolve references like 'this code', 'that error', or 'the current page'.
    """
    timestamp: datetime = Field(default_factory=_utc_now)

    # Active Workspace & Application State
    active_application: Optional[str] = None
    active_window_title: Optional[str] = None
    active_browser: Optional[str] = None
    active_url: Optional[str] = None
    active_domain: Optional[str] = None
    page_title: Optional[str] = None

    # Filesystem & Editor Context
    current_workspace_dir: Optional[str] = None
    active_file_path: Optional[str] = None
    selected_text: Optional[str] = None

    # Active Learning & Companion State
    active_goal_id: Optional[str] = None
    active_plan_id: Optional[str] = None
    active_task_id: Optional[str] = None
    active_concept_id: Optional[str] = None

    # Action Tracking & History
    last_action_name: Optional[str] = None
    last_action_result: Dict[str, Any] = Field(default_factory=dict)
    pending_confirmation_id: Optional[str] = None
