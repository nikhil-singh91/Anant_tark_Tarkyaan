"""
Tarkyaan Unified Companion Subsystem.
Multimodal companion router, prompt injection defense, and tool result normalization.
"""

from tarkyaan.companion.prompt_defense import (
    DefenseResult,
    PromptInjectionDefender,
)
from tarkyaan.companion.router import (
    CompanionResponse,
    UnifiedCompanionRouter,
)
from tarkyaan.companion.tool_result_normalizer import ToolResultNormalizer

__all__ = [
    "CompanionResponse",
    "DefenseResult",
    "PromptInjectionDefender",
    "ToolResultNormalizer",
    "UnifiedCompanionRouter",
]
