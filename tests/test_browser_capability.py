"""Tests for Browser Intelligence, Session Manager, and Prompt Injection Defense."""

from __future__ import annotations

import pytest

from tarkyaan.browser.browser_capability import BrowserActionResult, BrowserCapability
from tarkyaan.browser.session_manager import BrowserSession, BrowserSessionManager
from tarkyaan.models.enums import BrowserActionType


def test_browser_session_lifecycle_and_budget():
    """Verify BrowserSessionManager tracks action count and enforces budget limits."""
    mgr = BrowserSessionManager(default_timeout_seconds=60, default_max_actions=3)
    session: BrowserSession = mgr.create_session(initial_url="https://mit.edu/algorithms")

    assert session.is_active is True
    assert session.actions_performed == 0

    # 1st action
    ok1 = mgr.record_action(session.session_id, BrowserActionType.OPEN_URL, target="https://mit.edu/algorithms")
    assert ok1 is True
    assert session.actions_performed == 1

    # 2nd action
    ok2 = mgr.record_action(session.session_id, BrowserActionType.SCROLL)
    assert ok2 is True

    # 3rd action (hits budget of 3)
    ok3 = mgr.record_action(session.session_id, BrowserActionType.EXTRACT_CONTENT)
    assert ok3 is True
    assert session.is_active is False

    # 4th action exceeds budget
    ok4 = mgr.record_action(session.session_id, BrowserActionType.CLICK)
    assert ok4 is False


def test_browser_session_cancellation():
    """Verify instant cancellation terminates session and blocks further actions."""
    mgr = BrowserSessionManager()
    session = mgr.create_session()
    assert session.is_active is True

    mgr.cancel_session(session.session_id, reason="Learner stopped")
    assert session.cancelled is True
    assert session.is_active is False

    # Actions fail after cancellation
    assert mgr.record_action(session.session_id, BrowserActionType.SCROLL) is False


def test_browser_capability_web_search():
    """Verify browser capability search returns curated educational results."""
    cap = BrowserCapability(mock_mode=True)
    res: BrowserActionResult = cap.search_web("dynamic programming memoization")
    assert res.success is True
    assert "Search Results" in res.extracted_content
    assert "MIT OpenCourseWare" in res.extracted_content


def test_browser_capability_prompt_injection_defense():
    """Verify adversarial webpages with prompt injection are sanitized and flagged."""
    cap = BrowserCapability(mock_mode=True)
    res: BrowserActionResult = cap.open_url("https://malicious-exploit-site.com")
    assert res.success is True
    assert res.prompt_injection_detected is True
    # The content must be wrapped in untrusted data boundaries
    assert "BEGIN UNTRUSTED EXTERNAL WEB DATA" in res.extracted_content
    assert "END UNTRUSTED EXTERNAL WEB DATA" in res.extracted_content
