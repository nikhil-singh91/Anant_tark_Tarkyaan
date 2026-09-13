"""
Tarkyaan Browser Subsystem Architecture (Category B: Architecture & Interface Now).
Contracts for safe browser navigation and learning resource display.
"""

from __future__ import annotations

import webbrowser
from typing import Optional


class BrowserManager:
    """
    Interface for controlled browser navigation and learning resource exploration.
    """

    def __init__(self, browser_name: str = "default") -> None:
        self.browser_name = browser_name

    def open_url(self, url: str) -> bool:
        """Open a verified learning resource URL in the system browser."""
        try:
            return webbrowser.open(url)
        except Exception:  # noqa: BLE001
            return False
