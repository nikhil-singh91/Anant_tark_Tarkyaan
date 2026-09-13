"""
Unit and Integration Tests for Tarkyaan Teaching Engine (Phase 5).
Verifies multi-tier adaptive explanations, Socratic inquiries,
misconception-aware remediation, and prerequisite blocker detours.
"""

import pytest
from tarkyaan.knowledge.prerequisite_graph import PrerequisiteDAG
from tarkyaan.learner.learner_model import LearnerModel
from tarkyaan.memory.memory_manager import TarkyaanMemoryManager
from tarkyaan.memory.memory_store import TarkyaanMemoryStore
from tarkyaan.models.enums import ExplanationStyle, MasteryTier
from tarkyaan.models.learner import LearnerProfile
from tarkyaan.models.teaching import ExplanationRequest
from tarkyaan.teaching.explanation_engine import ExplanationEngine
from tarkyaan.teaching.misconception_tutor import MisconceptionTutor
from tarkyaan.teaching.prerequisite_tutor import PrerequisiteTutor
from tarkyaan.teaching.socratic_engine import SocraticEngine
from tarkyaan.teaching.teaching_engine import TeachingEngine


@pytest.fixture
def clean_memory():
    store = TarkyaanMemoryStore(":memory:")
    manager = TarkyaanMemoryManager(store=store)
    return manager


@pytest.fixture
def learner_profile():
    return LearnerProfile(
        learner_id="test_learner_1",
        display_name="Nikhil",
        primary_domain="Computer Science"
    )


class TestExplanationEngine:
    def test_beginner_explanation_has_analogy_and_zero_jargon(self, learner_profile):
        engine = ExplanationEngine()
        req = ExplanationRequest(
            concept_id="binary_search",
            concept_name="Binary Search",
            learner_id=learner_profile.learner_id,
            target_tier=MasteryTier.INTRODUCED,
            preferred_style=ExplanationStyle.SIMPLE_ANALOGY
        )
        res = engine.explain(req)

        assert res.concept_id == "binary_search"
        assert res.target_tier == MasteryTier.INTRODUCED
        assert len(res.analogies) >= 1
        assert "dictionary" in res.analogies[0].lower() or "middle" in res.analogies[0].lower()
        assert res.verification_question is not None
        assert len(res.sections) >= 1

    def test_intermediate_explanation_includes_code_and_invariants(self, learner_profile):
        engine = ExplanationEngine()
        req = ExplanationRequest(
            concept_id="binary_search",
            concept_name="Binary Search",
            learner_id=learner_profile.learner_id,
            target_tier=MasteryTier.PRACTICING,
            preferred_style=ExplanationStyle.TECHNICAL
        )
        res = engine.explain(req)

        assert res.target_tier == MasteryTier.PRACTICING
        assert any(sec.code_snippet is not None for sec in res.sections)
        assert len(res.key_invariants) >= 1
        assert len(res.common_pitfalls) >= 1

    def test_advanced_explanation_includes_formal_theory_and_bounds(self, learner_profile):
        engine = ExplanationEngine()
        req = ExplanationRequest(
            concept_id="binary_search",
            concept_name="Binary Search",
            learner_id=learner_profile.learner_id,
            target_tier=MasteryTier.COMPETENT,
            preferred_style=ExplanationStyle.DEEP_FORMAL
        )
        res = engine.explain(req)

        assert res.style_applied == ExplanationStyle.DEEP_FORMAL
        assert any("monotonic" in sec.content.lower() or "cache" in sec.content.lower() for sec in res.sections)
        assert "log" in res.summary.lower()

    def test_recursion_explanations_adapt_cleanly(self, learner_profile):
        engine = ExplanationEngine()
        # Beginner
        b_res = engine.explain(ExplanationRequest(
            concept_id="recursion",
            concept_name="Recursion",
            learner_id=learner_profile.learner_id,
            target_tier=MasteryTier.INTRODUCED
        ))
        assert "nesting dolls" in b_res.analogies[0].lower() or "doll" in b_res.analogies[0].lower()

        # Advanced
        a_res = engine.explain(ExplanationRequest(
            concept_id="recursion",
            concept_name="Recursion",
            learner_id=learner_profile.learner_id,
            target_tier=MasteryTier.MASTERED,
            preferred_style=ExplanationStyle.DEEP_FORMAL
        ))
        assert any("induction" in sec.heading.lower() or "tail call" in sec.heading.lower() for sec in a_res.sections)


class TestSocraticEngine:
    def test_socratic_probe_generation(self):
        engine = SocraticEngine()
        probe = engine.generate_probe("binary_search", "Binary Search", probe_index=0)

        assert probe.concept_id == "binary_search"
        assert len(probe.probe_question) > 10
        assert len(probe.expected_keywords) >= 1

    def test_socratic_evaluation_identifies_insight(self):
        engine = SocraticEngine()
        probe = engine.generate_probe("binary_search", "Binary Search", probe_index=0)

        # Correct insightful answer
        eval_correct = engine.evaluate_probe_response(probe, "The array must be sorted so that the elements are in monotonic order.")
        assert eval_correct["achieved_insight"] is True
        assert eval_correct["confidence"] >= 0.80

        # Struggling short answer
        eval_struggling = engine.evaluate_probe_response(probe, "idk maybe numbers")
        assert eval_struggling["achieved_insight"] is False


class TestMisconceptionTutor:
    def test_misconception_intervention_structure(self):
        tutor = MisconceptionTutor()
        intervention = tutor.generate_intervention("binary_search", "unsorted array")

        assert intervention.concept_id == "binary_search"
        assert len(intervention.why_tempting) > 10
        assert len(intervention.flawed_mental_model) > 10
        assert len(intervention.correct_mental_model) > 10
        assert len(intervention.counterexample) > 10
        assert intervention.corrective_check_question is not None


class TestPrerequisiteTutor:
    def test_prerequisite_blocker_detection_and_remediation(self, clean_memory, learner_profile):
        clean_memory.create_learner(learner_profile)
        model = LearnerModel(learner_id=learner_profile.learner_id, memory_manager=clean_memory)

        # Register prerequisite topic first, then target topic
        model.register_topic("monotonicity_and_sorting", "Monotonicity & Sorting")
        model.register_topic("binary_search", "Binary Search", prerequisites=["monotonicity_and_sorting"])

        dag = PrerequisiteDAG()
        dag.add_concept("monotonicity_and_sorting", "Monotonicity & Sorting")
        dag.add_concept("binary_search", "Binary Search")
        dag.add_prerequisite("binary_search", "monotonicity_and_sorting")

        tutor = PrerequisiteTutor(dag=dag, learner_model=model)
        weak_p = tutor.find_weak_prerequisite("binary_search", learner_model=model)

        assert weak_p == "monotonicity_and_sorting"

        remediation = tutor.build_remediation("binary_search", "Binary Search", weak_p)
        assert remediation.target_concept_id == "binary_search"
        assert remediation.prerequisite_concept_id == "monotonicity_and_sorting"
        assert len(remediation.remediation_summary) > 10
        assert len(remediation.return_bridge) > 10


class TestTeachingEngineOrchestration:
    def test_adaptive_teaching_flow(self, clean_memory, learner_profile):
        clean_memory.create_learner(learner_profile)
        model = LearnerModel(learner_id=learner_profile.learner_id, memory_manager=clean_memory)
        engine = TeachingEngine(learner_model=model)

        # Low mastery -> beginner explanation
        exp_low = engine.explain_concept("binary_search", current_mastery=0.10, learner=learner_profile)
        assert exp_low.style_applied == ExplanationStyle.SIMPLE_ANALOGY

        # High mastery -> formal explanation
        exp_high = engine.explain_concept("binary_search", current_mastery=0.85, learner=learner_profile)
        assert exp_high.style_applied == ExplanationStyle.DEEP_FORMAL

        # Socratic probe
        probe = engine.probe_understanding("recursion", "Recursion")
        assert probe.concept_id == "recursion"
        assert "base case" in probe.target_insight.lower() or "stack" in probe.target_insight.lower()
