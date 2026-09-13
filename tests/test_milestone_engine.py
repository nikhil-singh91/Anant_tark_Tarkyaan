"""
Unit tests for MilestoneEngine.
Tests milestone synthesis, task anchoring, and capstone goal verification.
"""

from tarkyaan.models.enums import MilestoneStatus
from tarkyaan.models.planning import LearningTask, StudyPhase
from tarkyaan.planning.milestone_engine import MilestoneEngine


class TestMilestoneEngine:
    def test_milestone_synthesis_anchored_to_phases(self):
        t1 = LearningTask(task_id="t1", title="Task 1", topic_id="arrays")
        t2 = LearningTask(task_id="t2", title="Task 2", topic_id="strings")
        phase1 = StudyPhase(
            phase_id="p1",
            title="Phase 1: Linear Structures",
            concepts=["arrays", "strings"],
            task_ids=["t1", "t2"],
            tasks=[t1, t2],
            estimated_minutes=75
        )

        t3 = LearningTask(task_id="t3", title="Task 3", topic_id="trees")
        phase2 = StudyPhase(
            phase_id="p2",
            title="Phase 2: Hierarchical Structures",
            concepts=["trees"],
            task_ids=["t3"],
            tasks=[t3],
            estimated_minutes=60
        )

        milestones = MilestoneEngine.generate_milestones(
            plan_id="plan_test",
            phases=[phase1, phase2]
        )

        # Should generate 2 phase milestones + 1 capstone milestone = 3 milestones
        assert len(milestones) == 3
        assert milestones[0].milestone_order == 1
        assert "Linear Structures" in milestones[0].title
        assert "t1" in milestones[0].required_task_ids
        assert "t2" in milestones[0].required_task_ids

        # Capstone milestone
        assert "Capstone" in milestones[2].title
        assert milestones[2].status == MilestoneStatus.PENDING
