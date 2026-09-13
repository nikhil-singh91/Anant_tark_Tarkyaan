"""
Unit tests for PriorityEngine.
Tests severity weighting, prerequisite impact, downstream dependency count,
and transparent rationale generation.
"""

import pytest

from tarkyaan.knowledge.prerequisite_graph import PrerequisiteDAG
from tarkyaan.models.gaps import KnowledgeGap
from tarkyaan.models.goals import LearningGoal
from tarkyaan.models.mastery import TopicMastery
from tarkyaan.planning.priority_engine import PriorityEngine


class TestPriorityEngine:
    @pytest.fixture
    def goal(self):
        return LearningGoal(
            learner_id="l1",
            title="Master Tree Algorithms",
            target_outcome="Implement DFS/BFS and tree traversals"
        )

    def test_severity_affects_priority_score(self, goal):
        # Gap 1: Critical severity
        gap_critical = KnowledgeGap(
            learner_id="l1",
            concept_id="recursion",
            blocking_topic_id="trees",
            severity="critical",
            diagnostic_evidence="Failed base case"
        )
        # Gap 2: Low severity
        gap_low = KnowledgeGap(
            learner_id="l1",
            concept_id="io_formatting",
            blocking_topic_id="general",
            severity="low",
            diagnostic_evidence="Minor typo"
        )

        ranked = PriorityEngine.rank_concepts(
            candidate_concept_ids=["recursion", "io_formatting"],
            goal=goal,
            gaps=[gap_critical, gap_low]
        )

        scores = {r.concept_id: r.final_score for r in ranked}
        assert scores["recursion"] > scores["io_formatting"]
        assert ranked[0].concept_id == "recursion"

    def test_prerequisite_centrality_and_downstream_impact(self, goal):
        dag = PrerequisiteDAG()
        dag.add_concept("recursion", "Recursion", "cs")
        dag.add_concept("trees", "Trees", "cs")
        dag.add_concept("trie", "Trie", "cs")
        dag.add_concept("dp_trees", "Tree DP", "cs")
        dag.add_prerequisite("trees", "recursion")
        dag.add_prerequisite("trie", "trees")
        dag.add_prerequisite("dp_trees", "trees")

        # 'recursion' has multiple downstream dependents (trees, trie, dp_trees)
        # 'random_topic' has 0 dependents
        dag.add_concept("random_topic", "Random", "cs")

        ranked = PriorityEngine.rank_concepts(
            candidate_concept_ids=["recursion", "random_topic"],
            goal=goal,
            dag=dag,
            target_concept_ids=["trees"]
        )

        score_rec = next(r for r in ranked if r.concept_id == "recursion")
        score_rand = next(r for r in ranked if r.concept_id == "random_topic")

        assert score_rec.prerequisite_impact > score_rand.prerequisite_impact
        assert score_rec.downstream_dependents_count >= 1
        assert score_rec.final_score > score_rand.final_score

    def test_transparent_rationale_produced(self, goal):
        gap = KnowledgeGap(
            learner_id="l1",
            concept_id="hashing",
            blocking_topic_id="two_sum",
            severity="high",
            diagnostic_evidence="Missed collision handling"
        )
        ranked = PriorityEngine.rank_concepts(
            candidate_concept_ids=["hashing"],
            goal=goal,
            gaps=[gap]
        )

        rationale = ranked[0].rationale.lower()
        assert "hashing" in rationale
        assert "prioritized" in rationale
        assert "gap" in rationale or "score" in rationale
