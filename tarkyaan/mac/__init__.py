"""
Tarkyaan macOS Automation Architecture (Category B: Architecture & Interface Now).
Contracts for safe application control and system property management.
"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel


class MacAppInfo(BaseModel):
    """Metadata for an accessible macOS application."""
    name: str
    bundle_id: Optional[str] = None
    path: Optional[str] = None
    is_running: bool = False


class MacAppController:
    """
    Interface for interacting with authorized macOS applications.
    """

    def is_available(self) -> bool:
        """Check if AppleEvents/automation permissions are enabled."""
        return True

    def list_running_apps(self) -> List[str]:
        """Return list of running GUI applications."""
        return ["Finder", "Visual Studio Code", "Terminal"]
