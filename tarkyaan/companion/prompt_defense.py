"""
Prompt Injection Defense Subsystem.
Strictly treats all external web pages, PDFs, documents, screenshots, and code comments
as untrusted external data. Prevents indirect prompt injection attacks from escalating privileges.
"""

from __future__ import annotations

import re
from typing import Tuple
from pydantic import BaseModel


class DefenseResult(BaseModel):
    """Result of prompt injection sanitization."""
    is_safe: bool
    injection_detected: bool
    matched_pattern: str = ""
    sanitized_text: str


class PromptInjectionDefender:
    """
    Sanitizes untrusted external content and defends against prompt injection.
    Neutralizes attempts to override system instructions or trigger unpermitted tools.
    """

    INJECTION_PATTERNS = [
        (r"ignore\s+(all\s+)?previous\s+instructions", "Instruction override attempt"),
        (r"disregard\s+(the\s+)?above", "Context override attempt"),
        (r"you\s+are\s+now\s+in\s+developer\s+mode", "Jailbreak attempt"),
        (r"system\s*:\s*you\s+must", "Role impersonation attempt"),
        (r"run\s+this\s+command\s*:", "Arbitrary command execution attempt"),
        (r"send\s+all\s+environment\s+variables", "Exfiltration attempt"),
        (r"disable\s+security", "Security bypass attempt"),
        (r"bypass\s+permissions?", "Permission bypass attempt"),
        (r"delete\s+(all\s+)?files", "Destructive file deletion attempt"),
    ]

    @classmethod
    def sanitize_untrusted_content(cls, raw_content: str, source_label: str = "EXTERNAL_SOURCE") -> DefenseResult:
        """
        Scan and sanitize untrusted text before it is presented to reasoning engines.
        Encloses content in strict untrusted data boundaries.
        """
        if not raw_content:
            return DefenseResult(is_safe=True, injection_detected=False, sanitized_text="")

        injection_detected = False
        matched = ""

        for pattern, label in cls.INJECTION_PATTERNS:
            if re.search(pattern, raw_content, re.IGNORECASE):
                injection_detected = True
                matched = label
                break

        # Delimit as untrusted external content
        sanitized = (
            f"--- BEGIN UNTRUSTED DATA ({source_label}) ---\n"
            f"{raw_content.strip()}\n"
            f"--- END UNTRUSTED DATA ({source_label}) ---"
        )

        return DefenseResult(
            is_safe=not injection_detected,
            injection_detected=injection_detected,
            matched_pattern=matched,
            sanitized_text=sanitized,
        )
