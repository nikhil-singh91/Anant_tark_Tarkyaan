"""
Tavily Search Provider Integration.
Connects to Tavily Search API using HTTP REST endpoint.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from tarkyaan.models.enums import ResearchDepth
from tarkyaan.models.research import SearchResultCandidate
from tarkyaan.research.providers.base import (
    ProviderAuthError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    SearchOptions,
    SearchProvider,
    SearchResponse,
)


class TavilySearchProvider(SearchProvider):
    """
    Search provider integrating with Tavily's deep research API.
    """

    TAVILY_API_ENDPOINT = "https://api.tavily.com/search"

    def __init__(self, api_key: Optional[str] = None, name: str = "tavily") -> None:
        super().__init__(name=name)
        self.api_key = api_key or os.getenv("TAVILY_API_KEY", "")

    def is_configured(self) -> bool:
        """Verify whether an API key is available."""
        return bool(self.api_key and len(self.api_key.strip()) > 5)

    def search(self, query: str, options: Optional[SearchOptions] = None) -> SearchResponse:
        if not self.is_configured():
            return SearchResponse(
                query=query,
                candidates=[],
                provider_name=self.name,
                total_found=0,
                error="Tavily API key is not configured in environment (TAVILY_API_KEY)."
            )

        opts = options or SearchOptions()
        depth_str = "advanced" if opts.depth == ResearchDepth.DEEP else "basic"

        payload: Dict[str, Any] = {
            "api_key": self.api_key,
            "query": query,
            "search_depth": depth_str,
            "max_results": opts.max_results,
            "include_answer": False,
            "include_raw_content": False,
        }
        if opts.include_domains:
            payload["include_domains"] = opts.include_domains
        if opts.exclude_domains:
            payload["exclude_domains"] = opts.exclude_domains

        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.TAVILY_API_ENDPOINT,
            data=req_data,
            headers={"Content-Type": "application/json", "User-Agent": "Tarkyaan-Learning-Companion/1.0"}
        )

        try:
            with urllib.request.urlopen(req, timeout=opts.timeout_seconds) as resp:
                status_code = resp.getcode()
                if status_code != 200:
                    return SearchResponse(
                        query=query,
                        candidates=[],
                        provider_name=self.name,
                        error=f"Tavily returned HTTP status {status_code}"
                    )
                data = json.loads(resp.read().decode("utf-8"))

        except urllib.error.HTTPError as err:
            if err.code in (401, 403):
                raise ProviderAuthError(f"Tavily authentication failed: {err}") from err
            if err.code == 429:
                raise ProviderRateLimitError("Tavily rate limit exceeded.") from err
            return SearchResponse(query=query, candidates=[], provider_name=self.name, error=f"Tavily HTTP error {err.code}")
        except urllib.error.URLError as err:
            if "timed out" in str(err).lower():
                raise ProviderTimeoutError(f"Tavily search request timed out: {err}") from err
            raise ProviderUnavailableError(f"Tavily network error: {err}") from err
        except Exception as exc:  # noqa: BLE001
            return SearchResponse(query=query, candidates=[], provider_name=self.name, error=f"Unexpected error: {exc}")

        # Parse Tavily results into normalized candidates
        results = data.get("results", [])
        candidates: List[SearchResultCandidate] = []
        for rank, res in enumerate(results, start=1):
            url = res.get("url", "")
            domain = urlparse(url).netloc if url else ""
            candidates.append(
                SearchResultCandidate(
                    url=url,
                    title=res.get("title", ""),
                    snippet=res.get("content", ""),
                    source_domain=domain,
                    discovery_query=query,
                    provider=self.name,
                    rank_from_provider=rank,
                    metadata={"tavily_score": res.get("score", 0.0)}
                )
            )

        return SearchResponse(
            query=query,
            candidates=candidates,
            provider_name=self.name,
            total_found=len(candidates)
        )
