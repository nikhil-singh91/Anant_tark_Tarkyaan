"""
End-to-End Acceptance Tests for Phase 7 (§94–§98 in Phase 7 Mission Specification).
Demonstrates all 5 mandatory multimodal, companion, and autonomous capability flows.
"""

from __future__ import annotations

import pytest

from tarkyaan.companion.router import CompanionResponse, UnifiedCompanionRouter
from tarkyaan.context.multimodal_context import LearnerContextSnapshot
from tarkyaan.models.enums import (
    CompanionChannel,
    CompanionIntentDomain,
    HealthStatus,
    MasteryTier,
    MultimodalInputType,
)
from tarkyaan.multimodal.input_engine import MultimodalInput, MultimodalInputEngine
from tarkyaan.vision.mock_provider import MockVisionProvider


@pytest.fixture
def companion_router() -> UnifiedCompanionRouter:
    """Fixture providing an initialized UnifiedCompanionRouter with mock providers."""
    return UnifiedCompanionRouter()


def test_acceptance_test_1_voice_and_coding_screenshot(companion_router: UnifiedCompanionRouter):
    """
    Acceptance Test 1 (§94):
    User says: 'Hey Tarkyaan, I'm learning DSA. Look at this coding problem and help me solve it.'
    Input: Voice + problem screenshot
    Expected: Multimodal Context -> Vision -> Problem Understanding -> Socratic Question -> Voice Response.
    """
    # 1. Simulate learner input: Voice transcript + screenshot
    problem_code = (
        "def binary_search(arr, target):\n"
        "    low = 0\n"
        "    high = len(arr) - 1\n"
        "    while low <= high:\n"
        "        mid = (low + high) // 2\n"
        "        # Boundary bug: infinite loop without low = mid + 1\n"
    )
    mm_engine = MultimodalInputEngine()
    mm_engine.image_engine.provider = MockVisionProvider(default_text=problem_code)

    inp = mm_engine.process_image_input(
        learner_id="learner_dsa_01",
        image_path_or_bytes=b"fake_dsa_problem_image",
        accompanying_text="Hey Tarkyaan, I'm learning DSA. Look at this coding problem and help me solve it.",
    )

    learner_snap = LearnerContextSnapshot(
        learner_id="learner_dsa_01",
        display_name="Dev",
        active_topic="binary_search",
        mastery_score=0.45,
        mastery_tier=MasteryTier.PRACTICING,
        recent_misconceptions=["boundary_off_by_one"],
    )

    # 2. Route interaction
    resp: CompanionResponse = companion_router.route_interaction(
        input_payload=inp,
        learner_snapshot=learner_snap,
    )

    # 3. Assertions
    assert resp.intent_domain == CompanionIntentDomain.LEARNING
    assert "binary_search" in resp.text_response
    # Contains pedagogical Socratic inquiry
    assert "?" in resp.voice_script or "condition" in resp.voice_script.lower()
    assert resp.recommended_next_action is not None


def test_acceptance_test_2_project_debugging_companion(companion_router: UnifiedCompanionRouter):
    """
    Acceptance Test 2 (§95):
    User says: 'Open my DSA project and explain why this code isn't working.'
    Expected: Intent -> App / Filesystem -> Project Context -> Code Analysis ->
              Error understanding -> Safe Verification -> Voice Response.
    """
    mm_engine = MultimodalInputEngine()
    inp = mm_engine.process_voice_input(
        learner_id="learner_dsa_02",
        transcript="Open my DSA project and explain why this code isn't working.",
    )

    learner_snap = LearnerContextSnapshot(
        learner_id="learner_dsa_02",
        display_name="Ananya",
        active_topic="binary_search",
        mastery_score=0.52,
    )

    resp: CompanionResponse = companion_router.route_interaction(
        input_payload=inp,
        learner_snapshot=learner_snap,
        confirmed_by_user=True,
    )

    assert resp.intent_domain == CompanionIntentDomain.PROJECT_STUDY
    assert "Visual Studio Code" in resp.text_response
    assert resp.autonomous_task_id is not None
    assert "completed" in resp.text_response.lower()


def test_acceptance_test_3_voice_research_and_browser(companion_router: UnifiedCompanionRouter):
    """
    Acceptance Test 3 (§96):
    User says: 'Find me a better explanation of dynamic programming.'
    Expected: Voice -> Intent -> Learner State -> Research -> Browser Search ->
              Resource Evaluation -> Teaching Synthesis -> Voice.
    """
    mm_engine = MultimodalInputEngine()
    inp = mm_engine.process_voice_input(
        learner_id="learner_dsa_03",
        transcript="Find me a better explanation of dynamic programming.",
    )

    learner_snap = LearnerContextSnapshot(
        learner_id="learner_dsa_03",
        display_name="Rohan",
        active_topic="dynamic_programming",
        mastery_score=0.35,
    )

    resp: CompanionResponse = companion_router.route_interaction(
        input_payload=inp,
        learner_snapshot=learner_snap,
    )

    assert resp.intent_domain == CompanionIntentDomain.RESEARCH
    assert "dynamic_programming" in resp.text_response.lower() or "researched" in resp.text_response.lower()
    assert len(resp.voice_script) > 0


def test_acceptance_test_4_what_should_i_do_next(companion_router: UnifiedCompanionRouter):
    """
    Acceptance Test 4 (§97):
    User asks: 'What should I do next?'
    Expected: Combines learner state, mastery, gaps, retention, and returns the highest-value action.
    """
    mm_engine = MultimodalInputEngine()
    inp = mm_engine.process_text_input(
        learner_id="learner_dsa_04",
        text="What should I do next?",
    )

    # Case A: At-risk / low mastery learner -> Prerequisite review
    at_risk_snap = LearnerContextSnapshot(
        learner_id="learner_dsa_04",
        active_topic="graph_traversal",
        mastery_score=0.3,
        learning_health=HealthStatus.AT_RISK,
    )
    resp_a = companion_router.route_interaction(inp, learner_snapshot=at_risk_snap)
    assert "prerequisite" in resp_a.recommended_next_action.lower() or "review" in resp_a.recommended_next_action.lower()

    # Case B: Intermediate learner -> Boundary practice
    inter_snap = LearnerContextSnapshot(
        learner_id="learner_dsa_04",
        active_topic="graph_traversal",
        mastery_score=0.6,
        learning_health=HealthStatus.HEALTHY,
    )
    resp_b = companion_router.route_interaction(inp, learner_snapshot=inter_snap)
    assert "practice" in resp_b.recommended_next_action.lower()


def test_acceptance_test_5_instant_cancellation(companion_router: UnifiedCompanionRouter):
    """
    Acceptance Test 5 (§98):
    User says: 'Stop.' / 'Cancel' / 'रुको' / 'रहने दो'
    Expected: All active tasks, browser sessions, and background operations are immediately cancelled.
    """
    mm_engine = MultimodalInputEngine()

    # English cancellation: "Stop"
    inp_stop = mm_engine.process_voice_input(learner_id="lrn_05", transcript="Stop.")
    resp_stop = companion_router.route_interaction(inp_stop)
    assert resp_stop.is_cancelled is True
    assert "stopped all active tasks" in resp_stop.text_response

    # Hindi cancellation: "रुको"
    inp_ruko = mm_engine.process_voice_input(learner_id="lrn_05", transcript="रुको")
    resp_ruko = companion_router.route_interaction(inp_ruko)
    assert resp_ruko.is_cancelled is True
    assert "stopped all active tasks" in resp_ruko.text_response

    # Hindi cancellation: "रहने दो"
    inp_rahne = mm_engine.process_voice_input(learner_id="lrn_05", transcript="रहने दो")
    resp_rahne = companion_router.route_interaction(inp_rahne)
    assert resp_rahne.is_cancelled is True
