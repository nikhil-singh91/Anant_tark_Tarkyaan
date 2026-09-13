"""
Tarkyaan Permission Management Subsystem.
Enforces macOS boundary awareness for hardware, OS automation, and system capabilities.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, Optional
from pydantic import BaseModel, Field


class PermissionCategory(str, Enum):
    """Hardware and OS boundary permissions."""
    MICROPHONE = "microphone"
    SCREEN_RECORDING = "screen_recording"
    ACCESSIBILITY = "accessibility"
    FILESYSTEM = "filesystem"
    TERMINAL = "terminal"
    AUTOMATION = "automation"
    NETWORK = "network"


class PermissionStatus(str, Enum):
    """Runtime status of a system permission."""
    GRANTED = "granted"
    DENIED = "denied"
    NOT_DETERMINED = "not_determined"
    RESTRICTED = "restricted"


class PermissionRecord(BaseModel):
    """State record for a specific permission category."""
    category: PermissionCategory
    status: PermissionStatus = Field(default=PermissionStatus.NOT_DETERMINED)
    rationale: str = Field(default="")
    last_verified: Optional[str] = None


class PermissionManager:
    """
    Manages and queries system permission boundaries.
    Prevents silent permission elevation and requires explicit user granting.
    """

    def __init__(self) -> None:
        self._states: Dict[PermissionCategory, PermissionRecord] = {
            PermissionCategory.NETWORK: PermissionRecord(
                category=PermissionCategory.NETWORK,
                status=PermissionStatus.GRANTED,
                rationale="Standard outgoing HTTP research requests permitted."
            ),
            PermissionCategory.FILESYSTEM: PermissionRecord(
                category=PermissionCategory.FILESYSTEM,
                status=PermissionStatus.GRANTED,
                rationale="Scoped local workspace storage for Tarkyaan independent database."
            ),
            PermissionCategory.MICROPHONE: PermissionRecord(
                category=PermissionCategory.MICROPHONE,
                status=PermissionStatus.NOT_DETERMINED,
                rationale="Requires macOS TCC permission for microphone audio capture."
            ),
            PermissionCategory.SCREEN_RECORDING: PermissionRecord(
                category=PermissionCategory.SCREEN_RECORDING,
                status=PermissionStatus.NOT_DETERMINED,
                rationale="Requires macOS Screen Recording permission."
            ),
            PermissionCategory.ACCESSIBILITY: PermissionRecord(
                category=PermissionCategory.ACCESSIBILITY,
                status=PermissionStatus.NOT_DETERMINED,
                rationale="Requires macOS Accessibility permissions for computer control."
            ),
            PermissionCategory.TERMINAL: PermissionRecord(
                category=PermissionCategory.TERMINAL,
                status=PermissionStatus.RESTRICTED,
                rationale="Terminal commands are strictly policy-checked and require confirmation."
            ),
            PermissionCategory.AUTOMATION: PermissionRecord(
                category=PermissionCategory.AUTOMATION,
                status=PermissionStatus.NOT_DETERMINED,
                rationale="Requires AppleEvents automation permissions for Finder/browser control."
            ),
        }

    def get_status(self, category: PermissionCategory) -> PermissionStatus:
        """Check the status of a specific permission."""
        record = self._states.get(category)
        return record.status if record else PermissionStatus.NOT_DETERMINED

    def is_granted(self, category: PermissionCategory) -> bool:
        """Verify whether a permission is explicitly granted."""
        return self.get_status(category) == PermissionStatus.GRANTED

    def set_status(self, category: PermissionCategory, status: PermissionStatus, rationale: str = "") -> None:
        """Update permission state (e.g. following user approval or macOS system verification)."""
        self._states[category] = PermissionRecord(
            category=category,
            status=status,
            rationale=rationale or self._states.get(category, PermissionRecord(category=category)).rationale
        )

    def grant(self, category: PermissionCategory, rationale: str = "") -> None:
        """Explicitly grant a permission."""
        self.set_status(category, PermissionStatus.GRANTED, rationale=rationale or f"Granted {category.value}")

    def revoke(self, category: PermissionCategory, rationale: str = "") -> None:
        """Revoke a previously granted permission."""
        self.set_status(category, PermissionStatus.DENIED, rationale=rationale or f"Revoked {category.value}")

    def list_permissions(self) -> Dict[str, str]:
        """Return human-readable mapping of all permission states."""
        return {cat.value: rec.status.value for cat, rec in self._states.items()}


# Global permission manager instance
permission_manager = PermissionManager()
