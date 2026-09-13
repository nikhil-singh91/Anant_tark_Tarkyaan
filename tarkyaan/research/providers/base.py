"""
Search Provider Interfaces and Result Models.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from tarkyaan.models.enums import ResearchDepth
from tarkyaan.models.research import SearchResultCandidate


class SearchOptions(BaseModel):
    """Configuration options passed to a search provider."""
    max_results: int = Field(default=5, ge=1, le=20)
    timeout_seconds: int = Field(default=15, ge=2, le=60)
    include_domains: List[str] = Field(default_factory=list)
    exclude_domains: List[str] = Field(default_factory=list)
    depth: ResearchDepth = Field(default=ResearchDepth.STANDARD)


class SearchResponse(BaseModel):
    """Normalized response returned by a search provider."""
    query: str
    candidates: List[SearchResultCandidate] = Field(default_factory=list)
    provider_name: str
    total_found: int = 0
    is_cached: bool = False
    error: Optional[str] = None


class SearchProviderError(Exception):
    """Base exception for search provider failures."""
    pass


class ProviderUnavailableError(SearchProviderError):
    """Raised when search API or network is unreachable."""
    pass


class ProviderAuthError(SearchProviderError):
    """Raised when API key or credentials are invalid."""
    pass


class ProviderRateLimitError(SearchProviderError):
    """Raised when provider rate limits or quotas are exceeded."""
    pass


class ProviderTimeoutError(SearchProviderError):
    """Raised when a search request times out."""
    pass



class SearchProvider(ABC):
    """Abstract search provider interface."""

    def __init__(self, name: str) -> None:
        self.name = name

    @abstractmethod
    def search(self, query: str, options: Optional[SearchOptions] = None) -> SearchResponse:
        """Execute a web search query and return normalized candidate resources."""
        pass
