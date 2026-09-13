"""
Resource Metadata Extractor and Content Sanitizer.
Extracts structural properties and defends against untrusted prompt injection.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional
from urllib.parse import urlparse
from pydantic import BaseModel, Field

from tarkyaan.safety.policies import PromptInjectionGuard


class ExtractedMetadata(BaseModel):
    """Normalized metadata extracted from a search candidate."""
    title: str
    description: str
    clean_snippet: str
    domain: str
    estimated_duration_minutes: float = Field(default=15.0)
    has_code_examples: bool = False
    is_suspicious: bool = False
    detected_injections: list[str] = Field(default_factory=list)


class ResourceExtractor:
    """
    Extracts structured educational metadata from snippet and title.
    Safely enforces prompt-injection boundaries.
    """

    CODE_INDICATORS = ("def ", "class ", "int main", "void ", "#include", "import ", "const ", "function", "=>")

    @classmethod
    def extract(cls, title: str, snippet: str, url: str) -> ExtractedMetadata:
        """Extract sanitized metadata and perform safety inspection."""
        domain = urlparse(url).netloc.lower() if url else ""

        # Safety Inspection: Untrusted Web Text
        combined_text = f"{title} {snippet}"
        is_suspicious, injection_patterns = PromptInjectionGuard.analyze_content(combined_text)

        # Sanitize text
        clean_title = PromptInjectionGuard.sanitize(title, max_length=200).strip()
        clean_snippet = PromptInjectionGuard.sanitize(snippet, max_length=1000).strip()

        # Check for code examples
        has_code = any(ind in clean_snippet for ind in cls.CODE_INDICATORS)

        # Estimate duration (approx 200 words/min + buffer for code)
        word_count = len(clean_snippet.split())
        estimated_duration = max(5.0, round(word_count / 30.0 + (10.0 if has_code else 5.0), 1))

        return ExtractedMetadata(
            title=clean_title,
            description=clean_snippet,
            clean_snippet=clean_snippet,
            domain=domain,
            estimated_duration_minutes=estimated_duration,
            has_code_examples=has_code,
            is_suspicious=is_suspicious,
            detected_injections=injection_patterns
        )
