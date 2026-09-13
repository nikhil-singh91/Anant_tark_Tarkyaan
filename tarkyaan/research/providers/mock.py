"""
Deterministic Mock Search Provider for Unit Tests and Offline Execution.
"""

from __future__ import annotations

from typing import Dict, List, Optional
from tarkyaan.models.research import SearchResultCandidate
from tarkyaan.research.providers.base import SearchOptions, SearchProvider, SearchResponse


class MockSearchProvider(SearchProvider):
    """
    Mock search provider with deterministic educational candidate responses.
    """

    DEFAULT_KNOWLEDGE_BANK: Dict[str, List[Dict[str, str]]] = {
        "recursion": [
            {
                "title": "Recursion in C++ and Algorithm Fundamentals",
                "url": "https://en.cppreference.com/w/cpp/language/recursion",
                "snippet": "Official documentation detailing function call stack, frame allocation, and base case invariants.",
                "domain": "en.cppreference.com",
            },
            {
                "title": "Visualizing Recursion and Call Stacks Tutorial",
                "url": "https://visualgo.net/en/recursion",
                "snippet": "Interactive step-by-step trace showing recursion tree branches, call stacks, and return values.",
                "domain": "visualgo.net",
            },
            {
                "title": "LeetCode Practice Problems: Recursion I & II",
                "url": "https://leetcode.com/explore/learn/card/recursion-i/",
                "snippet": "Curated problem set covering recursive divide-and-conquer, memoization, and tree traversal.",
                "domain": "leetcode.com",
            },
            {
                "title": "MIT OCW 6.006: Introduction to Algorithms - Recursion & Trees",
                "url": "https://ocw.mit.edu/courses/6-006-recursion-notes.pdf",
                "snippet": "Academic lecture notes analyzing recurrence relations, Master Theorem, and recursive tree structures.",
                "domain": "ocw.mit.edu",
            },
        ],
        "hashing": [
            {
                "title": "Hash Tables and Hash Functions - GeeksforGeeks",
                "url": "https://www.geeksforgeeks.org/hash-table-data-structure/",
                "snippet": "In-depth guide to collision resolution (chaining vs open addressing), time complexity, and hash maps.",
                "domain": "geeksforgeeks.org",
            },
            {
                "title": "C++ std::unordered_map Reference",
                "url": "https://en.cppreference.com/w/cpp/container/unordered_map",
                "snippet": "Standard Library documentation for hash map operations, buckets, load factor, and iterator safety.",
                "domain": "en.cppreference.com",
            },
            {
                "title": "Top 20 Hashing Problems for Technical Interviews",
                "url": "https://leetcode.com/tag/hash-table/",
                "snippet": "Coding interview practice problems focusing on frequency counting, two-sum, and subarray sums.",
                "domain": "leetcode.com",
            },
        ],
        "binary search": [
            {
                "title": "Binary Search Algorithm - Khan Academy",
                "url": "https://www.khanacademy.org/computing/computer-science/algorithms/binary-search",
                "snippet": "Clear conceptual introduction to dividing search space in half with interactive challenges.",
                "domain": "khanacademy.org",
            },
            {
                "title": "C++ std::binary_search and std::lower_bound",
                "url": "https://en.cppreference.com/w/cpp/algorithm/binary_search",
                "snippet": "Official algorithm reference for monotonic sequences and comparator functions.",
                "domain": "en.cppreference.com",
            },
        ],
    }

    def __init__(self, name: str = "mock_search") -> None:
        super().__init__(name=name)
        self.call_history: List[str] = []
        self.should_fail: bool = False
        self.failure_message: str = "Simulated search provider failure"

    def search(self, query: str, options: Optional[SearchOptions] = None) -> SearchResponse:
        self.call_history.append(query)

        if self.should_fail:
            return SearchResponse(
                query=query,
                candidates=[],
                provider_name=self.name,
                total_found=0,
                error=self.failure_message
            )

        opts = options or SearchOptions()
        query_lower = query.lower()

        # Find matching candidates or fallback to generic
        matched_entries = []
        for key, entries in self.DEFAULT_KNOWLEDGE_BANK.items():
            if key in query_lower:
                matched_entries.extend(entries)

        if not matched_entries:
            # Generate deterministic fallback candidates based on query
            clean_q = query.replace(" ", "_")
            matched_entries = [
                {
                    "title": f"Comprehensive Guide to {query.title()}",
                    "url": f"https://developer.mozilla.org/en-US/docs/Learn/{clean_q}",
                    "snippet": f"Authoritative reference and guide explaining {query} principles with code examples.",
                    "domain": "developer.mozilla.org",
                },
                {
                    "title": f"Practice Exercises for {query.title()}",
                    "url": f"https://exercism.org/tracks/python/exercises/{clean_q}",
                    "snippet": f"Hands-on coding exercises and mentor feedback for mastering {query}.",
                    "domain": "exercism.org",
                },
            ]

        candidates: List[SearchResultCandidate] = []
        for rank, entry in enumerate(matched_entries[:opts.max_results], start=1):
            candidates.append(
                SearchResultCandidate(
                    url=entry["url"],
                    title=entry["title"],
                    snippet=entry["snippet"],
                    source_domain=entry["domain"],
                    discovery_query=query,
                    provider=self.name,
                    rank_from_provider=rank,
                    metadata={"source": "mock_bank"}
                )
            )

        return SearchResponse(
            query=query,
            candidates=candidates,
            provider_name=self.name,
            total_found=len(candidates)
        )
