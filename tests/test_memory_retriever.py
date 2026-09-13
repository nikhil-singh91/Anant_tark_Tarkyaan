"""
Unit tests for MemoryRetriever and strict tenant/learner isolation.
"""

import pytest

from tarkyaan.memory.memory_manager import TarkyaanMemoryManager
from tarkyaan.memory.memory_models import MemoryItem
from tarkyaan.memory.memory_retriever import MemoryRetriever
from tarkyaan.memory.memory_store import TarkyaanMemoryStore
from tarkyaan.models.enums import EpistemicStatus, MasteryTier, MemorySource, MemoryType
from tarkyaan.models.gaps import KnowledgeGap
from tarkyaan.models.goals import LearningGoal
from tarkyaan.models.learner import LearnerProfile
from tarkyaan.models.mastery import Subject, Topic, TopicMastery


@pytest.fixture
def memory_system():
    store = TarkyaanMemoryStore(":memory:")
    mgr = TarkyaanMemoryManager(store=store)
    retriever = MemoryRetriever(mgr)
    yield mgr, retriever
    store.close()


class TestMemoryRetriever:
    def test_strict_learner_isolation(self, memory_system):
        """
        CRITICAL TEST: Verify that Learner A's memory can NEVER be returned for Learner B.
        """
        mgr, retriever = memory_system

        # Create Learner A
        learner_a = mgr.create_learner(LearnerProfile(
            display_name="Alice",
            primary_domain="Data Structures",
            preferred_language="Python"
        ))
        mgr.create_goal(LearningGoal(
            learner_id=learner_a.learner_id,
            title="Alice's Goal: Master Graphs",
            target_outcome="Graph DFS/BFS"
        ))
        mgr.store_memory_item(MemoryItem(
            learner_id=learner_a.learner_id,
            memory_type=MemoryType.SEMANTIC_LEARNER,
            key="secret_project",
            content="Alice is building a Python Graph Library",
            source=MemorySource.USER_EXPLICIT,
            epistemic_status=EpistemicStatus.FACT
        ))

        # Create Learner B
        learner_b = mgr.create_learner(LearnerProfile(
            display_name="Bob",
            primary_domain="Machine Learning",
            preferred_language="Julia"
        ))
        mgr.create_goal(LearningGoal(
            learner_id=learner_b.learner_id,
            title="Bob's Goal: Master Neural Nets",
            target_outcome="Backprop derivations"
        ))
        mgr.store_memory_item(MemoryItem(
            learner_id=learner_b.learner_id,
            memory_type=MemoryType.SEMANTIC_LEARNER,
            key="favorite_framework",
            content="Bob loves Flux.jl",
            source=MemorySource.USER_EXPLICIT,
            epistemic_status=EpistemicStatus.FACT
        ))

        # Retrieve context for Learner A
        context_a = retriever.retrieve_context(learner_a.learner_id)
        assert context_a.display_name == "Alice"
        assert "Alice's Goal: Master Graphs" in context_a.formatted_prompt_text
        assert "Alice is building a Python Graph Library" in context_a.formatted_prompt_text

        # Absolutely NO data from Bob should appear in Alice's context
        assert "Bob" not in context_a.formatted_prompt_text
        assert "Neural Nets" not in context_a.formatted_prompt_text
        assert "Flux.jl" not in context_a.formatted_prompt_text
        assert "Julia" not in context_a.formatted_prompt_text

        # Retrieve context for Learner B
        context_b = retriever.retrieve_context(learner_b.learner_id)
        assert context_b.display_name == "Bob"
        assert "Bob's Goal: Master Neural Nets" in context_b.formatted_prompt_text
        assert "Bob loves Flux.jl" in context_b.formatted_prompt_text

        # Absolutely NO data from Alice should appear in Bob's context
        assert "Alice" not in context_b.formatted_prompt_text
        assert "Master Graphs" not in context_b.formatted_prompt_text
        assert "Graph Library" not in context_b.formatted_prompt_text
        assert "Python" not in context_b.formatted_prompt_text

    def test_topic_focused_retrieval(self, memory_system):
        mgr, retriever = memory_system
        learner = mgr.create_learner(LearnerProfile(display_name="Charlie"))

        mgr.create_subject(Subject(subject_id="cs", name="Computer Science"))
        mgr.create_topic(Topic(topic_id="dp", subject_id="cs", name="Dynamic Programming"))
        mgr.update_topic_mastery(TopicMastery(
            learner_id=learner.learner_id,
            topic_id="dp",
            name="Dynamic Programming",
            mastery_score=0.72,
            tier=MasteryTier.COMPETENT
        ))
        mgr.create_knowledge_gap(KnowledgeGap(
            learner_id=learner.learner_id,
            concept_id="recursion_tree",
            blocking_topic_id="dp",
            severity="high",
            diagnostic_evidence="Cannot draw recursion tree for Fibonacci"
        ))

        context = retriever.retrieve_context(learner.learner_id, current_topic="dp")
        assert context.current_topic_mastery is not None
        assert context.current_topic_mastery["score"] == 0.72
        assert context.current_topic_mastery["tier"] == "competent"
        assert len(context.unresolved_gaps) == 1
        assert context.unresolved_gaps[0]["concept"] == "recursion_tree"

    def test_token_budget_truncation(self, memory_system):
        mgr, retriever = memory_system
        learner = mgr.create_learner(LearnerProfile(display_name="Dave"))

        # Add many memory items to exceed small budget
        for i in range(20):
            mgr.store_memory_item(MemoryItem(
                learner_id=learner.learner_id,
                memory_type=MemoryType.SEMANTIC_LEARNER,
                key=f"note_{i}",
                content=f"Detailed educational note {i} explaining complex compiler theory mechanics and memory optimization.",
                source=MemorySource.USER_EXPLICIT,
                epistemic_status=EpistemicStatus.FACT,
                importance=4
            ))

        # Retrieve with tiny budget of 50 tokens (~200 chars)
        context = retriever.retrieve_context(learner.learner_id, token_budget=50)
        assert len(context.formatted_prompt_text) <= 500  # small budget constraint honored
        assert "truncated" in context.formatted_prompt_text.lower()
