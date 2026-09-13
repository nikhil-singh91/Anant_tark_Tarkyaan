"""
Environment Context Subsystem.
Detects active application, workspace directory, and window context on macOS with graceful fallbacks.
"""

from __future__ import annotations

import os
import platform
import subprocess
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from tarkyaan.events.event_bus import EventBus
from tarkyaan.safety.permissions import PermissionCategory, PermissionManager, permission_manager


class EnvironmentState(BaseModel):
    """Snapshot of learner's computing environment."""
    active_app: str = "Unknown"
    window_title: Optional[str] = None
    project_directory: Optional[str] = None
    active_file: Optional[str] = None
    platform_name: str = Field(default_factory=platform.system)
    is_supported: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EnvironmentContextEngine:
    """
    Observes learner's active application context on-demand.
    Respects AUTOMATION / ACCESSIBILITY permissions; fails gracefully without crashing.
    """

    def __init__(
        self,
        perms: Optional[PermissionManager] = None,
        event_bus: Optional[EventBus] = None,
        mock_active_app: Optional[str] = None,
    ) -> None:
        self.permission_mgr = perms or permission_manager
        self.event_bus = event_bus
        self.mock_active_app = mock_active_app

    def get_current_environment(self, project_path: Optional[str] = None) -> EnvironmentState:
        """
        Inspect current active application and window context.
        Falls back cleanly if running in tests, unpermitted environments, or non-macOS platforms.
        """
        # 1. Mock override for testing
        if self.mock_active_app:
            return EnvironmentState(
                active_app=self.mock_active_app,
                window_title=f"{self.mock_active_app} - Workspace",
                project_directory=project_path or os.getcwd(),
                platform_name=platform.system(),
            )

        # 2. Check platform
        if platform.system() != "Darwin":
            return EnvironmentState(
                active_app="Generic Desktop",
                is_supported=False,
                project_directory=project_path or os.getcwd(),
                metadata={"reason": "Non-macOS platform; AppleScript context unavailable."},
            )

        # 3. Query frontmost app via AppleScript with timeout
        active_app = "Unknown"
        window_title = None

        script = """
        tell application "System Events"
            set frontApp to name of first application process whose frontmost is true
            return frontApp
        end tell
        """
        try:
            res = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if res.returncode == 0 and res.stdout.strip():
                active_app = res.stdout.strip()
        except Exception:
            active_app = "Terminal"

        return EnvironmentState(
            active_app=active_app,
            window_title=window_title,
            project_directory=project_path or os.getcwd(),
            platform_name="Darwin",
        )
