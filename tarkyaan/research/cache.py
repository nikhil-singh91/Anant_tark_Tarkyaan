"""
Research Response Cache.
Provides TTL-bounded in-memory and persistence caching for web search queries.
"""

from __future__ import annotations

import hashlib
import json
import time
from typing import Dict, Optional
from tarkyaan.research.providers.base import SearchResponse


class CachedSearchItem:
    """In-memory cached search response container."""

    def __init__(self, response: SearchResponse, ttl_seconds: int = 3600) -> None:
        self.response = response
        self.cached_at = time.time()
        self.expires_at = self.cached_at + ttl_seconds

    def is_expired(self) -> bool:
        return time.time() > self.expires_at


class ResearchCache:
    """
    LRU/TTL cache preventing redundant search provider queries.
    """

    def __init__(self, default_ttl_seconds: int = 3600, max_items: int = 200) -> None:
        self.default_ttl = default_ttl_seconds
        self.max_items = max_items
        self._cache: Dict[str, CachedSearchItem] = {}

    @classmethod
    def generate_cache_key(cls, query: str, provider: str) -> str:
        """Create deterministic SHA256 key from normalized query and provider name."""
        norm_q = " ".join(query.strip().lower().split())
        raw = f"{provider}:{norm_q}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def get(self, query: str, provider: str) -> Optional[SearchResponse]:
        """Retrieve unexpired cached response or return None."""
        key = self.generate_cache_key(query, provider)
        item = self._cache.get(key)
        if not item:
            return None

        if item.is_expired():
            del self._cache[key]
            return None

        # Return copy with is_cached flag
        res = item.response.model_copy(deep=True)
        res.is_cached = True
        return res

    def set(self, query: str, provider: str, response: SearchResponse, ttl_seconds: Optional[int] = None) -> None:
        """Store search response in cache."""
        key = self.generate_cache_key(query, provider)
        ttl = ttl_seconds or self.default_ttl

        # Evict oldest if full
        if len(self._cache) >= self.max_items and key not in self._cache:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].cached_at)
            del self._cache[oldest_key]

        self._cache[key] = CachedSearchItem(response=response, ttl_seconds=ttl)

    def clear(self) -> None:
        """Flush cache."""
        self._cache.clear()
