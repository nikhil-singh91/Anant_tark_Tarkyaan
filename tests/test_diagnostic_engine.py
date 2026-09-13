"""
Unit tests for DiagnosticEngine master orchestrator.
Tests end-to-end diagnostic session lifecycle, Socratic progression,
Bayesian mastery updates, gap discovery, and strict learner isolation.
"""

import pytest

from tarkyaan.assessment.diagnostic_engine import DiagnosticEngine
from tarkyaan.knowledge.prerequisite_graph import PrerequisiteDAG
from tarkyaan.memory.memory_manager import TarkyaanMemoryManager
from tarkyaan.memory.memory_store import TarkyaanMemoryStore
from tarkyaan.models.diagnostic import DiagnosticSessionStatus
from tarkyaan.models.enums import MasteryTier
from tarkyaan.models.learner import LearnerProfile


@pytest.fixture
def diagnostic_system():
    store = TarkyaanMemoryStore(":memory:")
    mgr = TarkyaanMemoryManager(store=store)

    # Build standard prerequisite graph
    dag = PrerequisiteDAG()
    dag.add_prerequisite("stack_memory", "functions")
    dag.add_prerequisite("recursion", "stack_memory")
    dag.add_prerequisite("trees", "recursion")

    engine = DiagnosticEngine(memory_manager=mgr, dag=dag)
    yield mgr, dag, engine
    store.close()


class TestDiagnosticEngine:
    def test_session_lifecycle(self, diagnostic_system):
        mgr, dag, engine = diagnostic_system
        learner = mgr.create_learner(LearnerProfile(display_name="Kavya", preferred_language="Python"))

        # Start session
        session = engine.start_session(
            learner_id=learner.learner_id,
            target_concepts=["trees"],
            max_questions=3
        )
        assert session.status == DiagnosticSessionStatus.IN_PROGRESS
        assert session.session_id.startswith("ds_")

        # Pause and resume
        engine.pause_session(session.session_id)
        assert session.status == DiagnosticSessionStatus.PAUSED
        engine.resume_session(session.session_id)
        assert session.status == DiagnosticSessionStatus.IN_PROGRESS

        # Cancel
        engine.cancel_session(session.session_id)
        assert session.status == DiagnosticSessionStatus.CANCELLED

    def test_socratic_diagnostic_progression_and_mastery(self, diagnostic_system):
        mgr, dag, engine = diagnostic_system
        learner = mgr.create_learner(LearnerProfile(display_name="Kavya", preferred_language="Python"))

        session = engine.start_session(
            learner_id=learner.learner_id,
            target_concepts=["trees"],
            max_questions=4
        )

        # 1. Fetch first probe (should probe root prerequisite 'functions' or 'stack_memory' first)
        q1 = engine.next_probe(session.session_id)
        assert q1 is not None
        assert q1.concept_id in ("functions", "stack_memory", "trees")

        # 2. Submit strong answer
        evidence1 = engine.submit_answer(
            session_id=session.session_id,
            question_id=q1.question_id,
            response_text="Functions allocate local variables on the call stack and pop them on return, maintaining strict LIFO execution order."
        )
        assert evidence1.composite_score >= 0.70

        # Verify mastery in Tarkyaan Memory was updated via MasteryEngine
        mastery1 = mgr.get_topic_mastery(learner.learner_id, q1.concept_id)
        assert mastery1 is not None
        assert mastery1.mastery_score > 0.0
        assert mastery1.uncertainty < 1.0

        # 3. Next probe
        q2 = engine.next_probe(session.session_id)
        assert q2 is not None
        assert q2.question_id != q1.question_id

        # 4. Submit weak answer with misconception
        evidence2 = engine.submit_answer(
            session_id=session.session_id,
            question_id=q2.question_id,
            response_text="Binary search works on unsorted lists."
        )
        assert evidence2.composite_score < 0.40

        # Check gap was discovered and stored in memory
        gaps = mgr.get_active_gaps(learner.learner_id)
        assert len(gaps) >= 1

        # 5. Complete session and verify report
        report = engine.complete_session(session.session_id)
        assert report.learner_id == learner.learner_id
        assert report.session_id == session.session_id
        assert len(report.concept_mastery_map) >= 1
        assert len(report.knowledge_gaps) >= 1
        assert report.summary_narrative != ""

    def test_strict_learner_isolation_in_diagnostics(self, diagnostic_system):
        """
        CRITICAL TEST: Verify that Learner A's diagnostic session, answers,
        and report can NEVER appear in Learner B's memory.
        """
        mgr, dag, engine = diagnostic_system

        # Learner A (Ananya)
        learner_a = mgr.create_learner(LearnerProfile(display_name="Ananya"))
        session_a = engine.start_session(learner_id=learner_a.learner_id, target_concepts=["recursion"])
        q_a = engine.next_probe(session_a.session_id)
        engine.submit_answer(
            session_id=session_a.session_id,
            question_id=q_a.question_id,
            response_text="Ananya's detailed recursion answer explaining the base case."
        )
        report_a = engine.complete_session(session_a.session_id)

        # Learner B (Bhavin)
        learner_b = mgr.create_learner(LearnerProfile(display_name="Bhavin"))
        session_b = engine.start_session(learner_id=learner_b.learner_id, target_concepts=["trees"])
        q_b = engine.next_probe(session_b.session_id)
        engine.submit_answer(
            session_id=session_b.session_id,
            question_id=q_b.question_id,
            response_text="Bhavin's answer on tree traversal."
        )
        report_b = engine.complete_session(session_b.session_id)

        # Cross-isolation checks
        gaps_a = mgr.get_active_gaps(learner_a.learner_id)
        gaps_b = mgr.get_active_gaps(learner_b.learner_id)

        # None of Ananya's data in Bhavin's state
        for g in gaps_b:
            assert g.learner_id == learner_b.learner_id
            assert g.learner_id != learner_a.learner_id

        # Reports are isolated
        assert report_a.learner_id == learner_a.learner_id
        assert report_b.learner_id == learner_b.learner_id
        assert "Ananya" not in report_b.summary_narrative
        assert "Bhavin" not in report_a.summary_narrative
