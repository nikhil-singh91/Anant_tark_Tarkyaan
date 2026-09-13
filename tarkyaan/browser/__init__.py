"""
Tarkyaan Browser Capability Subsystem.
Contracts for safe browser navigation, bounded sessions, and learning resource display.
"""

from __future__ import annotations

import webbrowser
from typing import Optional

from tarkyaan.browser.browser_capability import (
    BrowserActionResult,
    BrowserCapability,
)
from tarkyaan.browser.session_manager import (
    BrowserSession,
    BrowserSessionManager,
)


class BrowserManager:
    """
    Interface for controlled browser navigation and learning resource exploration.
    Maintains backwards compatibility with Phase 4 tests while integrating with Phase 7.
    """

    def __init__(self, browser_name: str = "default") -> None:
        self.browser_name = browser_name
        self.capability = BrowserCapability()

    def open_url(self, url: str) -> bool:
        """Open a verified learning resource URL in the system browser."""
        try:
            return webbrowser.open(url)
        except Exception:
            return False


__all__ = [
    "BrowserActionResult",
    "BrowserCapability",
    "BrowserManager",
    "BrowserSession",
    "BrowserSessionManager",
]
