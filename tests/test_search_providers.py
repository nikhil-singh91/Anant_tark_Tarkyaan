"""Tests for Tarkyaan Search Providers (Mock and Tavily REST)."""

import io
import json
import urllib.error
from unittest.mock import MagicMock, patch
import pytest

from tarkyaan.research.providers.base import (
    ProviderAuthError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    SearchOptions,
    SearchResponse,
)
from tarkyaan.research.providers.mock import MockSearchProvider
from tarkyaan.research.providers.tavily import TavilySearchProvider


def test_mock_search_provider_knowledge_bank():
    """Verify mock provider returns curated candidates for known educational topics."""
    provider = MockSearchProvider()
    response = provider.search("mastering recursion and stack frames", SearchOptions(max_results=3))

    assert response.total_found == 3
    assert len(response.candidates) == 3
    assert any("recursion" in c.url.lower() for c in response.candidates)
    assert any("cppreference" in c.domain for c in response.candidates)


def test_mock_search_provider_fallback_and_limit():
    """Verify mock provider handles novel queries and limits result counts."""
    provider = MockSearchProvider()
    response = provider.search("quantum computing quantum teleportation", SearchOptions(max_results=1))

    assert len(response.candidates) == 1
    cand = response.candidates[0]
    assert cand.provider == "mock_search"
    assert "developer.mozilla.org" in cand.domain


def test_mock_search_provider_failure_mode():
    """Verify mock provider simulates API failure cleanly."""
    provider = MockSearchProvider()
    provider.should_fail = True
    provider.failure_message = "Mock upstream connection dropped"

    response = provider.search("binary search")
    assert response.total_found == 0
    assert response.error == "Mock upstream connection dropped"


def test_tavily_provider_missing_api_key():
    """Verify Tavily provider fails gracefully when API key is missing."""
    provider = TavilySearchProvider(api_key="")
    response = provider.search("python data structures")
    assert response.error is not None
    assert "api key" in response.error.lower()


def test_tavily_provider_mocked_success():
    """Verify Tavily parses valid JSON search responses correctly."""
    provider = TavilySearchProvider(api_key="tvly-mock-test-key")

    mock_json_response = {
        "results": [
            {
                "title": "Python AsyncIO Tutorial",
                "url": "https://realpython.com/async-io-python/",
                "content": "A complete walk-through of cooperative multitasking in Python.",
                "score": 0.95,
            },
            {
                "title": "Official asyncio Documentation",
                "url": "https://docs.python.org/3/library/asyncio.html",
                "content": "Asynchronous I/O, event loop, coroutines and tasks.",
                "score": 0.99,
            },
        ]
    }

    mock_response = MagicMock()
    mock_response.getcode.return_value = 200
    mock_response.read.return_value = json.dumps(mock_json_response).encode("utf-8")
    mock_response.__enter__.return_value = mock_response

    with patch("urllib.request.urlopen", return_value=mock_response):
        res = provider.search("python asyncio tutorial", SearchOptions(max_results=2))

    assert res.error is None
    assert len(res.candidates) == 2
    assert res.candidates[0].title == "Python AsyncIO Tutorial"
    assert res.candidates[0].domain == "realpython.com"
    assert res.candidates[1].domain == "docs.python.org"


def test_tavily_provider_auth_error():
    """Verify Tavily raises ProviderAuthError on HTTP 401."""
    provider = TavilySearchProvider(api_key="tvly-invalid-key")

    from email.message import Message

    http_error = urllib.error.HTTPError(
        url="https://api.tavily.com/search",
        code=401,
        msg="Unauthorized",
        hdrs=Message(),
        fp=io.BytesIO(b"Invalid API key"),
    )

    with patch("urllib.request.urlopen", side_effect=http_error):
        with pytest.raises(ProviderAuthError):
            provider.search("python")


def test_tavily_provider_rate_limit_error():
    """Verify Tavily raises ProviderRateLimitError on HTTP 429."""
    from email.message import Message
    provider = TavilySearchProvider(api_key="tvly-valid-key")

    http_error = urllib.error.HTTPError(
        url="https://api.tavily.com/search",
        code=429,
        msg="Too Many Requests",
        hdrs=Message(),
        fp=io.BytesIO(b"Rate limit exceeded"),
    )

    with patch("urllib.request.urlopen", side_effect=http_error):
        with pytest.raises(ProviderRateLimitError):
            provider.search("python")


def test_tavily_provider_timeout_error():
    """Verify Tavily raises ProviderTimeoutError on network timeouts."""
    provider = TavilySearchProvider(api_key="tvly-valid-key")

    url_error = urllib.error.URLError("Connection timed out")

    with patch("urllib.request.urlopen", side_effect=url_error):
        with pytest.raises(ProviderTimeoutError):
            provider.search("python")
