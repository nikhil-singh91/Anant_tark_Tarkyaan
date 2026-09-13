"""
Knowledge Gap Analyzer & Root-Cause Analysis Engine.
Identifies conceptual and prerequisite deficits by traversing the DAG backwards
from symptom concepts to primitive root deficits.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Set

from tarkyaan.knowledge.prerequisite_graph import PrerequisiteDAG
from tarkyaan.models.gaps import KnowledgeGap


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class GapType(str, Enum):
    """Specific nature of an identified knowledge gap."""
    MISSING_PREREQUISITE = "missing_prerequisite"
    WEAK_FOUNDATION = "weak_foundation"
    CONCEPTUAL_DEFICIT = "conceptual_deficit"
    APPLICATION_GAP = "application_gap"
    RECALL_GAP = "recall_gap"


class GapSeverity(str, Enum):
    """Urgency of resolving a knowledge gap."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class RootCauseResult:
    """
    Detailed explanation of the root primitive deficit underlying a high-level struggle.
    """
    target_concept: str
    root_concept: str
    dependency_chain: List[str]  # e.g. ['stack_memory', 'call_frames', 'recursion', 'trees']
    root_mastery: float
    severity: GapSeverity
    explanation: str


class GapAnalyzer:
    """
    Analyzes learner knowledge state against prerequisite graphs
    to pinpoint blocking gaps and determine root causes.
    """

    COMPETENCE_THRESHOLD: float = 0.70
    HIGH_RISK_THRESHOLD: float = 0.40

    @classmethod
    def determine_severity(
        cls,
        mastery_score: float,
        is_root: bool,
        downstream_dependents_count: int
    ) -> GapSeverity:
        """Calculate gap severity based on score and structural impact."""
        if mastery_score < cls.HIGH_RISK_THRESHOLD and (is_root or downstream_dependents_count >= 3):
            return GapSeverity.CRITICAL
        elif mastery_score < cls.HIGH_RISK_THRESHOLD or downstream_dependents_count >= 2:
            return GapSeverity.HIGH
        elif mastery_score < cls.COMPETENCE_THRESHOLD:
            return GapSeverity.MEDIUM
        return GapSeverity.LOW

    @classmethod
    def find_root_cause(
        cls,
        target_concept: str,
        mastery_map: Dict[str, float],
        dag: PrerequisiteDAG
    ) -> Optional[RootCauseResult]:
        """
        Trace upstream from target_concept to identify the deepest unmastered prerequisite.
        If a learner struggles on Concept C, and C requires B, and B requires A:
        If A is weak, A is the ROOT CAUSE, not B or C.
        """
        if not dag.has_concept(target_concept):
            return None

        # Find all blocking ancestors
        blocking = dag.find_blocking_prerequisites(
            target_concept,
            mastery_map,
            competence_threshold=cls.COMPETENCE_THRESHOLD
        )
        if not blocking:
            return None

        # The blocking list is sorted by topological depth; the first one is the deepest root
        root_concept = blocking[0]
        root_score = mastery_map.get(root_concept, 0.0)

        # Build path from root to target
        chain = cls._find_path(dag, root_concept, target_concept) or [root_concept, target_concept]
        deps_count = len(dag.get_descendants(root_concept))
        is_primitive_root = (len(dag.get_prerequisites(root_concept)) == 0)

        severity = cls.determine_severity(root_score, is_primitive_root, deps_count)

        explanation = (
            f"Struggle in '{dag.get_concept(target_concept).name}' is rooted in deficit in "
            f"prerequisite '{dag.get_concept(root_concept).name}' (Mastery: {round(root_score, 2)}). "
            f"Resolving '{dag.get_concept(root_concept).name}' unlocks the entire chain: {' -> '.join(chain)}."
        )

        return RootCauseResult(
            target_concept=target_concept,
            root_concept=root_concept,
            dependency_chain=chain,
            root_mastery=root_score,
            severity=severity,
            explanation=explanation
        )

    @classmethod
    def analyze_concept_gaps(
        cls,
        learner_id: str,
        target_concept: str,
        mastery_map: Dict[str, float],
        dag: PrerequisiteDAG,
        diagnostic_evidence: str = ""
    ) -> List[KnowledgeGap]:
        """
        Evaluate target_concept and its prerequisites to produce structured KnowledgeGap records.
        """
        gaps: List[KnowledgeGap] = []
        target_score = mastery_map.get(target_concept, 0.0)

        # 1. Direct gap on target concept if weak
        if target_score < cls.COMPETENCE_THRESHOLD:
            # Check if this concept itself is a gap
            descendants = dag.get_descendants(target_concept) if dag.has_concept(target_concept) else set()
            blocking_id = next(iter(descendants)) if descendants else target_concept
            sev = cls.determine_severity(target_score, is_root=False, downstream_dependents_count=len(descendants))

            gaps.append(KnowledgeGap(
                gap_id=f"gap_{uuid.uuid4().hex[:8]}",
                learner_id=learner_id,
                concept_id=target_concept,
                blocking_topic_id=blocking_id,
                severity=sev.value,
                diagnostic_evidence=diagnostic_evidence or f"Mastery score {round(target_score, 2)} below 0.70 threshold"
            ))

        # 2. Trace upstream blocking prerequisites
        if dag.has_concept(target_concept):
            blocking_prereqs = dag.find_blocking_prerequisites(target_concept, mastery_map, cls.COMPETENCE_THRESHOLD)
            for prereq in blocking_prereqs:
                p_score = mastery_map.get(prereq, 0.0)
                is_root = len(dag.get_prerequisites(prereq)) == 0
                deps_count = len(dag.get_descendants(prereq))
                sev = cls.determine_severity(p_score, is_root, deps_count)

                gaps.append(KnowledgeGap(
                    gap_id=f"gap_{uuid.uuid4().hex[:8]}",
                    learner_id=learner_id,
                    concept_id=prereq,
                    blocking_topic_id=target_concept,
                    severity=sev.value,
                    diagnostic_evidence=f"Prerequisite deficit blocking '{target_concept}'. Mastery: {round(p_score, 2)}"
                ))

        return gaps

    @classmethod
    def _find_path(cls, dag: PrerequisiteDAG, start: str, end: str) -> Optional[List[str]]:
        """Find a directed path from start to end in the DAG using BFS."""
        if start == end:
            return [start]
        from collections import deque
        queue = deque([[start]])
        visited: Set[str] = {start}

        while queue:
            path = queue.popleft()
            node = path[-1]
            if node == end:
                return path
            for child in dag.get_dependents(node):
                if child not in visited:
                    visited.add(child)
                    queue.append(path + [child])
        return None
