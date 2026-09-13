"""
Milestone Engine for Tarkyaan Planning Brain.
Synthesizes measurable curriculum checkpoints anchored to tasks, concepts, and phases.
"""

from __future__ import annotations

import uuid
from typing import List

from tarkyaan.models.enums import MilestoneStatus
from tarkyaan.models.planning import Milestone, StudyPhase


class MilestoneEngine:
    """
    Generates measurable milestones that delineate progress toward goal readiness.
    """

    @classmethod
    def generate_milestones(
        cls,
        plan_id: str,
        phases: List[StudyPhase]
    ) -> List[Milestone]:
        """
        Create measurable milestones tied to phase achievements and concept groupings.
        """
        milestones: List[Milestone] = []

        for idx, phase in enumerate(phases, start=1):
            title = f"Milestone {idx}: {phase.title} Competency"
            objective = f"Achieve verified competence across {', '.join(phase.concepts[:3])}."
            criteria = [
                f"Complete all {len(phase.task_ids)} assigned tasks in {phase.title}",
                f"Demonstrate mastery tier >= Competent for concepts: {', '.join(phase.concepts[:2])}"
            ]
            if phase.completion_criteria:
                criteria.extend(phase.completion_criteria)

            milestones.append(Milestone(
                milestone_id=f"ms_{uuid.uuid4().hex[:8]}",
                plan_id=plan_id,
                title=title,
                objective=objective,
                required_task_ids=list(phase.task_ids),
                required_concepts=list(phase.concepts),
                completion_criteria=criteria,
                status=MilestoneStatus.PENDING,
                milestone_order=idx
            ))

        # Add a capstone goal milestone if multiple phases exist
        if len(phases) > 1:
            all_task_ids = [tid for p in phases for tid in p.task_ids]
            all_concepts = list(dict.fromkeys([c for p in phases for c in p.concepts]))
            milestones.append(Milestone(
                milestone_id=f"ms_{uuid.uuid4().hex[:8]}",
                plan_id=plan_id,
                title="Capstone Milestone: Full Goal Readiness",
                objective="Synthesize across all learned concepts and demonstrate applied problem-solving mastery.",
                required_task_ids=all_task_ids[-3:] if len(all_task_ids) >= 3 else all_task_ids,
                required_concepts=all_concepts[-2:] if len(all_concepts) >= 2 else all_concepts,
                completion_criteria=[
                    "Successfully solve complex synthesis problem under time constraints",
                    "No unresolved critical knowledge gaps remaining"
                ],
                status=MilestoneStatus.PENDING,
                milestone_order=len(phases) + 1
            ))

        return milestones
