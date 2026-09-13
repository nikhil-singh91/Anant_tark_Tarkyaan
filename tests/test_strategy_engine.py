"""
Unit tests for StrategyEngine.
Tests strategy selection across prerequisite-heavy, gap-heavy, practice-heavy,
and timeline-constrained learning scenarios.
"""

from datetime import datetime, timedelta, timezone
import pytest

from tarkyaan.knowledge.prerequisite_graph import PrerequisiteDAG
from tarkyaan.models.enums import LearningStrategy, MasteryTier
from tarkyaan.models.gaps import KnowledgeGap
from tarkyaan.models.goals import LearningGoal
from tarkyaan.models.mastery import TopicMastery
from tarkyaan.planning.strategy_engine import StrategyEngine


class TestStrategyEngine:
    def test_exam_focused_strategy_on_tight_deadline(self):
        now = datetime.now(timezone.utc)
        goal = LearningGoal(
            learner_id="l1",
            title="Interview Prep",
            target_outcome="Pass Google interview",
            deadline=now + timedelta(days=7)  # 7 days left
        )
        decision = StrategyEngine.select_strategy(goal=goal)
        assert decision.strategy == LearningStrategy.EXAM_FOCUSED
        assert "deadline" in decision.rationale.lower()

    def test_prerequisite_first_strategy_when_roots_blocked(self):
        goal = LearningGoal(
            learner_id="l1",
            title="Advanced Tree Algorithms",
            target_outcome="Solve Tree DP"
        )
        dag = PrerequisiteDAG()
        dag.add_concept("functions", "Functions", "cs")
        dag.add_concept("recursion", "Recursion", "cs")
        dag.add_concept("trees", "Trees", "cs")
        dag.add_prerequisite("recursion", "functions")
        dag.add_prerequisite("trees", "recursion")

        # Learner has very low mastery in both prerequisites
        masteries = {
            "functions": TopicMastery(learner_id="l1", topic_id="functions", mastery_score=0.2, uncertainty=0.6),
            "recursion": TopicMastery(learner_id="l1", topic_id="recursion", mastery_score=0.1, uncertainty=0.8),
            "trees": TopicMastery(learner_id="l1", topic_id="trees", mastery_score=0.0, uncertainty=1.0),
        }

        decision = StrategyEngine.select_strategy(
            goal=goal,
            mastery_map=masteries,
            dag=dag,
            target_concept_ids=["trees"]
        )
        assert decision.strategy == LearningStrategy.PREREQUISITE_FIRST
        assert "prerequisite" in decision.rationale.lower()

    def test_gap_first_strategy_when_prereqs_stable(self):
        goal = LearningGoal(
            learner_id="l1",
            title="Graph Algorithms",
            target_outcome="Shortest path"
        )
        dag = PrerequisiteDAG()
        dag.add_concept("queues", "Queues", "cs")
        dag.add_concept("graphs", "Graphs", "cs")
        dag.add_prerequisite("graphs", "queues")

        # Prerequisite 'queues' is solidly mastered
        masteries = {
            "queues": TopicMastery(learner_id="l1", topic_id="queues", mastery_score=0.85, uncertainty=0.2),
            "graphs": TopicMastery(learner_id="l1", topic_id="graphs", mastery_score=0.3, uncertainty=0.5),
        }
        gap = KnowledgeGap(
            learner_id="l1",
            concept_id="graphs",
            blocking_topic_id="dijkstra",
            severity="critical",
            diagnostic_evidence="Cycle detection failure"
        )

        decision = StrategyEngine.select_strategy(
            goal=goal,
            mastery_map=masteries,
            gaps=[gap],
            dag=dag,
            target_concept_ids=["graphs"]
        )
        assert decision.strategy == LearningStrategy.GAP_FIRST
        assert "gap" in decision.rationale.lower()

    def test_practice_heavy_strategy_when_concepts_understood(self):
        goal = LearningGoal(
            learner_id="l1",
            title="Binary Search Practice",
            target_outcome="Speed and precision"
        )
        masteries = {
            "binary_search": TopicMastery(
                learner_id="l1",
                topic_id="binary_search",
                mastery_score=0.65,
                uncertainty=0.25,
                tier=MasteryTier.COMPETENT
            ),
            "two_pointers": TopicMastery(
                learner_id="l1",
                topic_id="two_pointers",
                mastery_score=0.68,
                uncertainty=0.25,
                tier=MasteryTier.COMPETENT
            ),
        }
        decision = StrategyEngine.select_strategy(
            goal=goal,
            mastery_map=masteries,
            target_concept_ids=["binary_search", "two_pointers"]
        )
        assert decision.strategy == LearningStrategy.PRACTICE_HEAVY
