"""
Dependency Scheduler for Tarkyaan Planning Brain.
Orders concepts according to strict DAG topological constraints and categorizes
prerequisites by learner mastery (mastered, weak, missing, uncertain).
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field

from tarkyaan.knowledge.prerequisite_graph import PrerequisiteDAG
from tarkyaan.models.enums import MasteryTier, TaskType
from tarkyaan.models.mastery import TopicMastery


class ScheduledConcept(BaseModel):
    """A concept scheduled in strict prerequisite order with tailored task requirements."""
    concept_id: str
    status_category: str = Field(..., description="mastered, weak, missing, uncertain")
    mastery_score: float = Field(default=0.0, ge=0.0, le=1.0)
    uncertainty: float = Field(default=1.0, ge=0.0, le=1.0)
    tier: MasteryTier = Field(default=MasteryTier.UNEXPLORED)
    prerequisites: List[str] = Field(default_factory=list)
    recommended_task_types: List[TaskType] = Field(default_factory=list)
    schedule_order: int = Field(default=1, ge=1)
    skip_instruction: bool = Field(default=False, description="True if already demonstrated high mastery")


class DependencyScheduler:
    """
    Computes a pedagogically sound linear curriculum sequence respecting DAG relationships
    and learner mastery bounds.
    """

    @classmethod
    def schedule(
        cls,
        candidate_concept_ids: List[str],
        mastery_map: Optional[Dict[str, TopicMastery]] = None,
        dag: Optional[PrerequisiteDAG] = None,
        include_unmastered_ancestors: bool = True
    ) -> List[ScheduledConcept]:
        """
        Produce a topologically sorted, prerequisite-aware sequence of concepts.
        """
        masteries = mastery_map or {}
        active_concepts: Set[str] = set(candidate_concept_ids)

        # 1. Expand with ancestor prerequisites from DAG if needed
        if dag and include_unmastered_ancestors:
            for cid in list(active_concepts):
                if dag.has_concept(cid):
                    ancestors = dag.get_ancestors(cid)
                    for anc in ancestors:
                        # Include ancestor if not already mastered
                        m = masteries.get(anc)
                        is_mastered = m is not None and m.mastery_score >= 0.75 and m.uncertainty <= 0.35
                        if not is_mastered:
                            active_concepts.add(anc)

        # 2. Topological order via DAG
        ordered_cids: List[str] = []
        if dag:
            # Filter topological sort of DAG to active concepts
            try:
                full_topo = dag.topological_sort()
                ordered_cids = [cid for cid in full_topo if cid in active_concepts]
                # Include any candidate concepts not registered in DAG
                for cid in active_concepts:
                    if cid not in ordered_cids:
                        ordered_cids.append(cid)
            except Exception:
                # Fallback to candidate list order
                ordered_cids = list(active_concepts)
        else:
            ordered_cids = list(active_concepts)

        # 3. Categorize mastery and assign task styles
        scheduled: List[ScheduledConcept] = []
        for idx, cid in enumerate(ordered_cids, start=1):
            m_obj = masteries.get(cid)
            mastery_score = m_obj.mastery_score if m_obj else 0.0
            uncertainty = m_obj.uncertainty if m_obj else 0.85
            tier = m_obj.tier if m_obj else MasteryTier.UNEXPLORED

            # Determine prerequisites for this node
            prereqs: List[str] = []
            if dag and dag.has_concept(cid):
                prereqs = [p for p in dag.get_prerequisites(cid) if p in active_concepts]

            # Categorize status
            skip_instruction = False
            task_types: List[TaskType] = []

            if mastery_score >= 0.75 and uncertainty <= 0.35:
                status_category = "mastered"
                skip_instruction = True
                # Mastered concepts require at most a quick application or comparison benchmark
                task_types = [TaskType.REVIEW]
            elif mastery_score < 0.35 and m_obj is not None:
                status_category = "missing"
                task_types = [TaskType.UNDERSTAND, TaskType.PRACTICE]
            elif uncertainty >= 0.70 and m_obj is None:
                status_category = "uncertain"
                task_types = [TaskType.ASSESSMENT, TaskType.LEARN]
            elif mastery_score >= 0.40:
                status_category = "weak"
                task_types = [TaskType.PRACTICE, TaskType.APPLY]
            else:
                status_category = "missing"
                task_types = [TaskType.UNDERSTAND, TaskType.PRACTICE]

            scheduled.append(ScheduledConcept(
                concept_id=cid,
                status_category=status_category,
                mastery_score=round(mastery_score, 2),
                uncertainty=round(uncertainty, 2),
                tier=tier,
                prerequisites=prereqs,
                recommended_task_types=task_types,
                schedule_order=idx,
                skip_instruction=skip_instruction
            ))

        return scheduled
