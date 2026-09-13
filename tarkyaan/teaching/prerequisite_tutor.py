"""
Prerequisite Blocker Tutor for Tarkyaan Phase 5.
Identifies weak prerequisite concepts blocking mastery of the target topic
and generates focused pedagogical remediation mini-lessons.
"""

from __future__ import annotations

from typing import Dict, List, Optional
from tarkyaan.knowledge.prerequisite_graph import PrerequisiteDAG
from tarkyaan.learner.learner_model import LearnerModel
from tarkyaan.models.enums import MasteryTier
from tarkyaan.models.teaching import PrerequisiteRemediation


class PrerequisiteTutor:
    """
    Prerequisite remediation controller.
    If evidence indicates the learner is struggling because an underlying foundation
    is unmastered, the tutor pivots cleanly to remediate the prerequisite first.
    """

    PREREQUISITE_MINI_LESSONS: Dict[str, Dict[str, str]] = {
        "arrays_and_indexing": {
            "name": "Arrays & Zero-Based Indexing",
            "summary": "An array stores items contiguously in memory. In zero-based indexing, the first item is at index 0, and the last is at index len - 1. Midpoint is calculated via index arithmetic: mid = low + (high - low) // 2.",
            "check": "In an array of length 5, what are the starting and ending indices?",
            "bridge": "Now that array indices are crystal clear, we can use these boundary pointers (low and high) to navigate binary search!"
        },
        "monotonicity_and_sorting": {
            "name": "Monotonicity & Sorted Arrays",
            "summary": "Monotonicity means values only change in one direction: either non-decreasing (arr[i] <= arr[i+1]) or non-increasing. This directional guarantee is what makes eliminating half the search space valid.",
            "check": "If an array is sorted in ascending order and arr[mid] is 10, can any number to the left of mid be 15?",
            "bridge": "Because order is guaranteed, we can safely discard entire halves during binary search."
        },
        "call_stack_basics": {
            "name": "Call Stack & Activation Frames",
            "summary": "When a function is invoked, a stack frame containing its parameters and local variables is pushed onto the call stack. When it returns, that frame is popped. The stack grows with each nested call.",
            "check": "Which stack frame finishes and gets removed first: the very first call, or the most recent call?",
            "bridge": "With this call stack mental model, we can trace recursive functions without getting lost!"
        },
        "time_complexity_log_n": {
            "name": "Logarithmic Time Complexity O(log n)",
            "summary": "Logarithmic time O(log n) arises whenever an algorithm repeatedly divides the problem size by a constant factor (like 2). Halving 1,000,000 items takes only 20 steps.",
            "check": "How many times can you divide 16 by 2 before reaching 1?",
            "bridge": "Now we understand why binary search scales so effortlessly even to billions of items!"
        }
    }

    def __init__(
        self,
        dag: Optional[PrerequisiteDAG] = None,
        learner_model: Optional[LearnerModel] = None
    ) -> None:
        self.dag = dag
        self.learner_model = learner_model

    def find_weak_prerequisite(
        self,
        target_concept_id: str,
        learner_model: Optional[LearnerModel] = None
    ) -> Optional[str]:
        """
        Check whether any direct prerequisite of target concept is weak (< 0.50 mastery or unexplored).
        """
        model = learner_model or self.learner_model
        if not model:
            return None

        prereqs: List[str] = []
        if self.dag and self.dag.has_concept(target_concept_id):
            prereqs = self.dag.get_prerequisites(target_concept_id)
        else:
            # Fallback heuristic mapping
            if "binary_search" in target_concept_id.lower() or "binary search" in target_concept_id.lower():
                prereqs = ["monotonicity_and_sorting", "arrays_and_indexing"]
            elif "recursion" in target_concept_id.lower():
                prereqs = ["call_stack_basics"]

        for p_id in prereqs:
            mastery = model.get_topic_mastery(p_id)
            if not mastery:
                return p_id
            if mastery.mastery_score < 0.50 or mastery.tier in (MasteryTier.UNEXPLORED, MasteryTier.INTRODUCED):
                return p_id

        return None

    def build_remediation(
        self,
        target_concept_id: str,
        target_concept_name: str,
        prerequisite_id: str
    ) -> PrerequisiteRemediation:
        """Construct a structured remediation mini-lesson for the weak prerequisite."""
        p_data = self.PREREQUISITE_MINI_LESSONS.get(prerequisite_id, {
            "name": prerequisite_id.replace("_", " ").title(),
            "summary": f"Foundational review of {prerequisite_id.replace('_', ' ')} required for mastering {target_concept_name}.",
            "check": f"What is the key principle behind {prerequisite_id.replace('_', ' ')}?",
            "bridge": f"Now that {prerequisite_id.replace('_', ' ')} is solid, let's return to {target_concept_name}!"
        })

        return PrerequisiteRemediation(
            target_concept_id=target_concept_id,
            target_concept_name=target_concept_name,
            prerequisite_concept_id=prerequisite_id,
            prerequisite_concept_name=p_data["name"],
            reason_for_detour=f"Learner requires foundational strengthening in {p_data['name']} to unlock complete understanding of {target_concept_name}.",
            remediation_summary=p_data["summary"],
            mini_check_question=p_data["check"],
            return_bridge=p_data["bridge"]
        )
