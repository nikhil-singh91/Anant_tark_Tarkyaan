"""
Goal Decomposer for Tarkyaan Planning Brain.
Decomposes high-level learning goals into target competencies, core concepts,
supporting concepts, and required prerequisite foundations across any domain.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field

from tarkyaan.knowledge.prerequisite_graph import PrerequisiteDAG
from tarkyaan.models.gaps import KnowledgeGap
from tarkyaan.models.goals import LearningGoal
from tarkyaan.models.learner import LearnerProfile
from tarkyaan.models.mastery import TopicMastery


class DecomposedGoal(BaseModel):
    """Structured decomposition of a high-level learning goal."""
    goal_id: str
    domain: str
    target_outcome: str
    target_concepts: List[str] = Field(default_factory=list)
    required_competencies: List[str] = Field(default_factory=list)
    supporting_concepts: List[str] = Field(default_factory=list)
    prerequisite_concepts: List[str] = Field(default_factory=list)
    practice_requirements: List[str] = Field(default_factory=list)
    verification_requirements: List[str] = Field(default_factory=list)


class GoalDecomposer:
    """
    Analyzes learning goals across multiple domains (Computer Science, Mathematics,
    Physics, Machine Learning, Languages, Professional Skills) and decomposes
    them into constituent concepts and competencies.
    """

    # Multi-domain concept ontologies as deterministic fallback anchors
    DOMAIN_ONTOLOGIES: Dict[str, Dict[str, List[str]]] = {
        "dsa": {
            "core": ["arrays", "strings", "hashing", "recursion", "trees", "graphs", "dynamic_programming"],
            "competencies": ["Time and space complexity analysis", "Recursive decomposition", "Graph traversal", "Dynamic programming state transition"],
            "prerequisites": ["functions", "pointers", "stack_memory"]
        },
        "computer science": {
            "core": ["boolean_logic", "memory_hierarchy", "operating_systems", "concurrency", "networking"],
            "competencies": ["Systems-level reasoning", "Concurrency safety", "Network protocol comprehension"],
            "prerequisites": ["binary_math", "hardware_basics"]
        },
        "machine learning": {
            "core": ["linear_algebra", "multivariate_calculus", "gradient_descent", "linear_regression", "neural_networks"],
            "competencies": ["Loss function formulation", "Optimization convergence", "Model generalization"],
            "prerequisites": ["vectors_matrices", "derivatives"]
        },
        "mathematics": {
            "core": ["algebra", "trigonometry", "calculus", "linear_algebra", "probability"],
            "competencies": ["Formal mathematical proof", "Algebraic manipulation", "Analytical differentiation"],
            "prerequisites": ["arithmetic", "set_theory"]
        },
        "physics": {
            "core": ["classical_mechanics", "thermodynamics", "electromagnetism", "optics", "quantum_mechanics"],
            "competencies": ["Free-body diagram modeling", "Energy conservation formulation", "Field equations"],
            "prerequisites": ["differential_equations", "vector_analysis"]
        }
    }

    @classmethod
    def decompose(
        cls,
        goal: LearningGoal,
        learner: Optional[LearnerProfile] = None,
        mastery_map: Optional[Dict[str, TopicMastery]] = None,
        gaps: Optional[List[KnowledgeGap]] = None,
        dag: Optional[PrerequisiteDAG] = None
    ) -> DecomposedGoal:
        """
        Decompose a goal into constituent concepts, prerequisites, and competencies.
        """
        masteries = mastery_map or {}
        active_gaps = gaps or []

        # 1. Identify domain
        domain = cls._detect_domain(goal, learner)

        # 2. Extract concepts
        target_concepts: List[str] = []
        competencies: List[str] = []
        supporting_concepts: List[str] = []
        prerequisites: List[str] = []

        # If DAG is provided, discover graph concepts matching goal text or leaves
        if dag:
            all_dag_concepts = dag.all_concepts()
            # Match tokens from title and target_outcome
            goal_text = f"{goal.title} {goal.target_outcome}".lower()
            for cid in all_dag_concepts:
                node = dag.get_concept(cid)
                if cid.lower() in goal_text or (node.name and node.name.lower() in goal_text):
                    target_concepts.append(cid)

            # If no direct matches, use terminal leaves or all concepts from DAG
            if not target_concepts and all_dag_concepts:
                leaves = dag.get_leaves()
                target_concepts = leaves if leaves else all_dag_concepts[:5]

            # Collect prerequisite concepts from ancestors in DAG
            for tc in target_concepts:
                ancestors = dag.get_ancestors(tc)
                for anc in ancestors:
                    if anc not in target_concepts and anc not in prerequisites:
                        prerequisites.append(anc)
        else:
            # Fallback to domain ontology
            ontology = cls.DOMAIN_ONTOLOGIES.get(domain, cls.DOMAIN_ONTOLOGIES["dsa"])
            target_concepts.extend(ontology["core"])
            prerequisites.extend(ontology["prerequisites"])
            competencies.extend(ontology["competencies"])

        # Also incorporate concepts from goal milestones if specified
        if goal.milestones:
            for ms in goal.milestones:
                token = cls._sanitize_concept_id(ms)
                if token and token not in target_concepts:
                    target_concepts.append(token)

        # Incorporate active gaps relevant to target concepts
        gap_concept_ids = {g.concept_id for g in active_gaps if not g.resolved}
        for g_cid in gap_concept_ids:
            if g_cid not in target_concepts and g_cid not in prerequisites:
                supporting_concepts.append(g_cid)

        # Generate competencies if empty
        if not competencies:
            competencies = [
                f"Demonstrate applied competency in {c.replace('_', ' ').title()}"
                for c in target_concepts[:4]
            ]
            competencies.append(f"Solve realistic problems aligned with outcome: {goal.target_outcome}")

        # Practice requirements
        practice_reqs = [
            f"Targeted practice problems on core concepts: {', '.join(target_concepts[:3])}",
            "Synthesis problem requiring integration of multiple concepts"
        ]

        # Verification requirements
        verification_reqs = [
            f"Achieve mastery score >= 0.70 across all target concepts",
            "Resolve all blocking prerequisite gaps"
        ]

        return DecomposedGoal(
            goal_id=goal.goal_id,
            domain=domain,
            target_outcome=goal.target_outcome,
            target_concepts=target_concepts,
            required_competencies=competencies,
            supporting_concepts=supporting_concepts,
            prerequisite_concepts=prerequisites,
            practice_requirements=practice_reqs,
            verification_requirements=verification_reqs
        )

    @classmethod
    def _detect_domain(cls, goal: LearningGoal, learner: Optional[LearnerProfile]) -> str:
        """Infer academic or professional domain from goal and profile."""
        combined_text = f"{goal.title} {goal.target_outcome}".lower()
        if learner:
            combined_text += f" {learner.primary_domain}".lower()

        if any(w in combined_text for w in ["dsa", "data structures", "algorithm", "competitive programming", "leetcode"]):
            return "dsa"
        elif any(w in combined_text for w in ["machine learning", "neural", "deep learning", "ai", "model"]):
            return "machine learning"
        elif any(w in combined_text for w in ["physics", "mechanics", "thermodynamics", "optics"]):
            return "physics"
        elif any(w in combined_text for w in ["math", "calculus", "algebra", "probability", "statistics"]):
            return "mathematics"
        elif any(w in combined_text for w in ["operating system", "concurrency", "network", "computer science"]):
            return "computer science"
        else:
            return "dsa"

    @classmethod
    def _sanitize_concept_id(cls, text: str) -> str:
        """Convert a milestone phrase into a canonical concept ID."""
        cleaned = re.sub(r"[^a-zA-Z0-9\s_]", "", text).strip().lower()
        return re.sub(r"\s+", "_", cleaned)
