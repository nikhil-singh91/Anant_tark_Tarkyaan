"""
Unit tests for DependencyScheduler.
Tests DAG-respecting topological ordering, mastered prerequisite skipping,
weak prerequisite reinforcement, and uncertain verification.
"""

import pytest

from tarkyaan.knowledge.prerequisite_graph import PrerequisiteDAG
from tarkyaan.models.enums import TaskType
from tarkyaan.models.mastery import TopicMastery
from tarkyaan.planning.dependency_scheduler import DependencyScheduler


class TestDependencyScheduler:
    @pytest.fixture
    def chain_dag(self):
        dag = PrerequisiteDAG()
        dag.add_concept("functions", "Functions", "cs")
        dag.add_concept("call_stack", "Call Stack", "cs")
        dag.add_concept("recursion", "Recursion", "cs")
        dag.add_concept("trees", "Trees", "cs")
        dag.add_prerequisite("call_stack", "functions")
        dag.add_prerequisite("recursion", "call_stack")
        dag.add_prerequisite("trees", "recursion")
        return dag

    def test_topological_ordering_guaranteed(self, chain_dag):
        scheduled = DependencyScheduler.schedule(
            candidate_concept_ids=["trees"],
            dag=chain_dag,
            include_unmastered_ancestors=True
        )

        cids = [s.concept_id for s in scheduled]
        assert "functions" in cids
        assert "call_stack" in cids
        assert "recursion" in cids
        assert "trees" in cids

        # Prerequisite positions must precede downstream positions
        assert cids.index("functions") < cids.index("call_stack")
        assert cids.index("call_stack") < cids.index("recursion")
        assert cids.index("recursion") < cids.index("trees")

    def test_mastered_concept_flags_skip_instruction(self, chain_dag):
        masteries = {
            "functions": TopicMastery(learner_id="l1", topic_id="functions", mastery_score=0.90, uncertainty=0.15),
            "call_stack": TopicMastery(learner_id="l1", topic_id="call_stack", mastery_score=0.80, uncertainty=0.20),
            "recursion": TopicMastery(learner_id="l1", topic_id="recursion", mastery_score=0.25, uncertainty=0.75),
            "trees": TopicMastery(learner_id="l1", topic_id="trees", mastery_score=0.10, uncertainty=0.90),
        }

        scheduled = DependencyScheduler.schedule(
            candidate_concept_ids=["functions", "call_stack", "recursion", "trees"],
            mastery_map=masteries,
            dag=chain_dag
        )

        func_item = next(s for s in scheduled if s.concept_id == "functions")
        rec_item = next(s for s in scheduled if s.concept_id == "recursion")

        assert func_item.skip_instruction is True
        assert func_item.status_category == "mastered"
        assert TaskType.REVIEW in func_item.recommended_task_types

        assert rec_item.skip_instruction is False
        assert rec_item.status_category == "missing"
        assert TaskType.UNDERSTAND in rec_item.recommended_task_types

    def test_weak_concept_receives_practice(self, chain_dag):
        masteries = {
            "recursion": TopicMastery(learner_id="l1", topic_id="recursion", mastery_score=0.55, uncertainty=0.35)
        }
        scheduled = DependencyScheduler.schedule(
            candidate_concept_ids=["recursion"],
            mastery_map=masteries,
            dag=chain_dag
        )
        rec_item = next(s for s in scheduled if s.concept_id == "recursion")
        assert rec_item.status_category == "weak"
        assert TaskType.PRACTICE in rec_item.recommended_task_types
