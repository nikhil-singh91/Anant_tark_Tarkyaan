"""
URL Normalization and Candidate Deduplication.
Preserves discovery provenance while stripping tracking parameters and fragments.
"""

from __future__ import annotations

import urllib.parse
from typing import Dict, List, Set, Tuple
from tarkyaan.models.research import SearchResultCandidate


class URLNormalizer:
    """
    Standardizes web URLs and deduplicates search candidate streams.
    """

    TRACKING_PARAM_PREFIXES = ("utm_", "fbclid", "gclid", "ref", "source", "feature", "ved", "ei")

    @classmethod
    def normalize_url(cls, raw_url: str) -> str:
        """
        Normalize URL:
        - Downcases protocol and hostname
        - Strips URL fragments (#hash)
        - Removes tracking and analytics query parameters
        - Normalizes trailing slashes (except root)
        """
        if not raw_url:
            return ""

        parsed = urllib.parse.urlparse(raw_url.strip())
        scheme = parsed.scheme.lower() or "https"
        netloc = parsed.netloc.lower()

        # Filter query params
        query_pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=False)
        clean_pairs = [
            (k, v) for k, v in query_pairs
            if not any(k.lower().startswith(p) for p in cls.TRACKING_PARAM_PREFIXES)
        ]
        clean_query = urllib.parse.urlencode(clean_pairs)

        # Normalize path
        path = parsed.path
        if path.endswith("/") and len(path) > 1:
            path = path[:-1]

        normalized = urllib.parse.urlunparse((scheme, netloc, path, "", clean_query, ""))
        return normalized

    @classmethod
    def deduplicate(
        cls,
        candidates: List[SearchResultCandidate]
    ) -> List[SearchResultCandidate]:
        """
        Deduplicate candidates by normalized URL.
        Aggregates multiple discovery queries into metadata['discovery_queries'].
        """
        seen_urls: Dict[str, SearchResultCandidate] = {}

        for cand in candidates:
            norm_url = cls.normalize_url(cand.url)
            if not norm_url:
                continue

            if norm_url in seen_urls:
                existing = seen_urls[norm_url]
                # Aggregate queries
                queries = existing.metadata.setdefault("discovery_queries", [existing.discovery_query])
                if cand.discovery_query not in queries:
                    queries.append(cand.discovery_query)
            else:
                cand.url = norm_url
                cand.metadata.setdefault("discovery_queries", [cand.discovery_query])
                seen_urls[norm_url] = cand

        return list(seen_urls.values())
