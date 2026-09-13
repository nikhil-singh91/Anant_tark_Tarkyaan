"""
Tarkyaan Computer & Application Interaction Subsystem.
"""

from tarkyaan.computer.application_adapter import (
    AppActionResult,
    ApplicationAdapter,
)
from tarkyaan.computer.computer_controller import (
    ComputerActionResult,
    ComputerController,
    MacOSComputerController,
    MockComputerController,
    UnsupportedComputerController,
)

__all__ = [
    "AppActionResult",
    "ApplicationAdapter",
    "ComputerActionResult",
    "ComputerController",
    "MacOSComputerController",
    "MockComputerController",
    "UnsupportedComputerController",
]
