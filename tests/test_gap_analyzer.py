"""
Unit tests for GapAnalyzer and root-cause deficit analysis.
"""

import pytest

from tarkyaan.knowledge.gap_analyzer import GapAnalyzer, GapSeverity
from tarkyaan.knowledge.prerequisite_graph import PrerequisiteDAG


class TestGapAnalyzer:
    @pytest.fixture
    def curriculum_dag(self):
        dag = PrerequisiteDAG()
        # stack_memory -> call_frames -> recursion -> recursion_trees -> divide_and_conquer
        dag.add_prerequisite("call_frames", "stack_memory")
        dag.add_prerequisite("recursion", "call_frames")
        dag.add_prerequisite("recursion_trees", "recursion")
        dag.add_prerequisite("divide_and_conquer", "recursion_trees")
        return dag

    def test_direct_concept_gap(self, curriculum_dag):
        mastery_map = {
            "stack_memory": 0.85,
            "call_frames": 0.80,
            "recursion": 0.35,  # Weak
            "recursion_trees": 0.20
        }
        gaps = GapAnalyzer.analyze_concept_gaps(
            learner_id="l1",
            target_concept="recursion",
            mastery_map=mastery_map,
            dag=curriculum_dag
        )
        assert len(gaps) >= 1
        assert gaps[0].concept_id == "recursion"
        assert gaps[0].severity in ("critical", "high")

    def test_root_cause_chain_traversal(self, curriculum_dag):
        """
        Learner struggles with recursion_trees.
        Upstream: recursion is 0.60, but primitive root stack_memory is 0.25.
        The root-cause analysis MUST identify stack_memory as the primitive root cause!
        """
        mastery_map = {
            "stack_memory": 0.25,     # Primitive root deficit
            "call_frames": 0.50,      # Intermediate deficit
            "recursion": 0.65,        # Intermediate deficit
            "recursion_trees": 0.30   # Symptom target
        }

        root_res = GapAnalyzer.find_root_cause(
            target_concept="recursion_trees",
            mastery_map=mastery_map,
            dag=curriculum_dag
        )

        assert root_res is not None
        assert root_res.target_concept == "recursion_trees"
        assert root_res.root_concept == "stack_memory"
        assert root_res.root_mastery == 0.25
        assert root_res.severity == GapSeverity.CRITICAL
        assert "stack_memory" in root_res.dependency_chain
        assert "recursion_trees" in root_res.dependency_chain

    def test_severity_calculation(self):
        # Very low score on root concept with multiple dependents -> CRITICAL
        sev_crit = GapAnalyzer.determine_severity(
            mastery_score=0.2,
            is_root=True,
            downstream_dependents_count=5
        )
        assert sev_crit == GapSeverity.CRITICAL

        # Moderate score (0.55) -> MEDIUM
        sev_med = GapAnalyzer.determine_severity(
            mastery_score=0.55,
            is_root=False,
            downstream_dependents_count=1
        )
        assert sev_med == GapSeverity.MEDIUM
