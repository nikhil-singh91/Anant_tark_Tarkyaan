"""Tarkyaan permissions module. Re-exports permission management from safety subsystem."""

from tarkyaan.safety.permissions import (
    PermissionCategory,
    PermissionManager,
    PermissionRecord,
    PermissionStatus,
    permission_manager,
)

__all__ = [
    "PermissionCategory",
    "PermissionManager",
    "PermissionRecord",
    "PermissionStatus",
    "permission_manager",
]
