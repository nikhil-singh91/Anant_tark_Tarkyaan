"""
Prerequisite Knowledge Graph for Tarkyaan.
Implements a Directed Acyclic Graph (DAG) for curriculum concepts,
strict cycle detection, topological sorting, ancestor/descendant traversal,
and blocking prerequisite identification.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


class CyclicDependencyError(Exception):
    """Raised when adding a prerequisite relationship would introduce a circular dependency."""


class ConceptNotFoundError(Exception):
    """Raised when querying or linking a non-existent concept node."""


@dataclass
class ConceptNode:
    """A single conceptual knowledge node in the prerequisite graph."""
    concept_id: str
    name: str
    subject_id: str = "general"
    description: Optional[str] = None
    prerequisites: Set[str] = field(default_factory=set)  # Nodes this concept depends upon
    dependents: Set[str] = field(default_factory=set)     # Nodes that depend upon this concept


class PrerequisiteDAG:
    """
    Directed Acyclic Graph representing concept dependencies.
    Domain-independent: supports DSA, Machine Learning, Mathematics, Systems, etc.
    """

    def __init__(self) -> None:
        self._nodes: Dict[str, ConceptNode] = {}

    def add_concept(
        self,
        concept_id: str,
        name: str,
        subject_id: str = "general",
        description: Optional[str] = None
    ) -> ConceptNode:
        """Add a concept to the graph or update existing metadata."""
        if concept_id in self._nodes:
            node = self._nodes[concept_id]
            node.name = name
            node.subject_id = subject_id
            if description is not None:
                node.description = description
            return node

        node = ConceptNode(
            concept_id=concept_id,
            name=name,
            subject_id=subject_id,
            description=description
        )
        self._nodes[concept_id] = node
        return node

    def has_concept(self, concept_id: str) -> bool:
        """Check if concept exists in graph."""
        return concept_id in self._nodes

    def get_concept(self, concept_id: str) -> ConceptNode:
        """Retrieve concept node or raise ConceptNotFoundError."""
        if concept_id not in self._nodes:
            raise ConceptNotFoundError(f"Concept '{concept_id}' not found in prerequisite graph.")
        return self._nodes[concept_id]

    def remove_concept(self, concept_id: str) -> None:
        """Remove concept and clean up in/out edges."""
        if concept_id not in self._nodes:
            return

        # Remove from prerequisites of dependents
        for dep_id in list(self._nodes[concept_id].dependents):
            if dep_id in self._nodes:
                self._nodes[dep_id].prerequisites.discard(concept_id)

        # Remove from dependents of prerequisites
        for prereq_id in list(self._nodes[concept_id].prerequisites):
            if prereq_id in self._nodes:
                self._nodes[prereq_id].dependents.discard(concept_id)

        del self._nodes[concept_id]

    def add_prerequisite(self, concept_id: str, prerequisite_id: str) -> None:
        """
        Establish a dependency: prerequisite_id is required before concept_id.
        (prerequisite_id -> concept_id)
        Rejects self-loops and circular dependencies with CyclicDependencyError.
        """
        if concept_id == prerequisite_id:
            raise CyclicDependencyError(
                f"Cannot make concept '{concept_id}' a prerequisite of itself."
            )

        if concept_id not in self._nodes:
            self.add_concept(concept_id, name=concept_id)
        if prerequisite_id not in self._nodes:
            self.add_concept(prerequisite_id, name=prerequisite_id)

        # Check if already established
        if prerequisite_id in self._nodes[concept_id].prerequisites:
            return

        # Cycle check: prerequisite_id must NOT be reachable from concept_id
        # i.e., prerequisite_id cannot already be a descendant of concept_id
        descendants = self.get_descendants(concept_id)
        if prerequisite_id in descendants:
            raise CyclicDependencyError(
                f"Adding dependency '{prerequisite_id}' -> '{concept_id}' creates a cycle. "
                f"'{prerequisite_id}' is already a downstream descendant of '{concept_id}'."
            )

        self._nodes[concept_id].prerequisites.add(prerequisite_id)
        self._nodes[prerequisite_id].dependents.add(concept_id)

    def remove_prerequisite(self, concept_id: str, prerequisite_id: str) -> None:
        """Remove a dependency edge."""
        if concept_id in self._nodes and prerequisite_id in self._nodes:
            self._nodes[concept_id].prerequisites.discard(prerequisite_id)
            self._nodes[prerequisite_id].dependents.discard(concept_id)

    def get_prerequisites(self, concept_id: str) -> List[str]:
        """Return immediate prerequisites."""
        return sorted(list(self.get_concept(concept_id).prerequisites))

    def get_dependents(self, concept_id: str) -> List[str]:
        """Return immediate dependents."""
        return sorted(list(self.get_concept(concept_id).dependents))

    def get_ancestors(self, concept_id: str) -> Set[str]:
        """
        Traverse transitively upwards to find all upstream prerequisite concepts.
        """
        self.get_concept(concept_id)  # Validate existence
        visited: Set[str] = set()
        queue = deque(self._nodes[concept_id].prerequisites)

        while queue:
            curr = queue.popleft()
            if curr not in visited:
                visited.add(curr)
                if curr in self._nodes:
                    for parent in self._nodes[curr].prerequisites:
                        if parent not in visited:
                            queue.append(parent)

        return visited

    def get_descendants(self, concept_id: str) -> Set[str]:
        """
        Traverse transitively downwards to find all downstream dependent concepts.
        """
        self.get_concept(concept_id)  # Validate existence
        visited: Set[str] = set()
        queue = deque(self._nodes[concept_id].dependents)

        while queue:
            curr = queue.popleft()
            if curr not in visited:
                visited.add(curr)
                if curr in self._nodes:
                    for child in self._nodes[curr].dependents:
                        if child not in visited:
                            queue.append(child)

        return visited

    def get_roots(self) -> List[str]:
        """Return concepts that have no prerequisites (foundational starting points)."""
        return sorted([cid for cid, node in self._nodes.items() if not node.prerequisites])

    def get_leaves(self) -> List[str]:
        """Return concepts that have no dependents (terminal/advanced topics)."""
        return sorted([cid for cid, node in self._nodes.items() if not node.dependents])

    def topological_sort(self) -> List[str]:
        """
        Return a valid linear ordering of all concepts respecting prerequisites.
        Uses Kahn's algorithm.
        """
        in_degrees: Dict[str, int] = {cid: len(node.prerequisites) for cid, node in self._nodes.items()}
        queue = deque([cid for cid, deg in in_degrees.items() if deg == 0])
        ordered: List[str] = []

        while queue:
            curr = queue.popleft()
            ordered.append(curr)

            for dep in self._nodes[curr].dependents:
                in_degrees[dep] -= 1
                if in_degrees[dep] == 0:
                    queue.append(dep)

        if len(ordered) != len(self._nodes):
            raise CyclicDependencyError("Graph contains a cycle; topological sort not possible.")

        return ordered

    def get_depth(self, concept_id: str) -> int:
        """
        Compute longest path from any root to concept_id.
        Roots have depth 0.
        """
        node = self.get_concept(concept_id)
        if not node.prerequisites:
            return 0

        max_parent_depth = max(self.get_depth(p) for p in node.prerequisites if p in self._nodes)
        return max_parent_depth + 1

    def find_blocking_prerequisites(
        self,
        concept_id: str,
        mastery_map: Dict[str, float],
        competence_threshold: float = 0.70
    ) -> List[str]:
        """
        Identify which prerequisites for a target concept are below the competence threshold.
        Traverses ancestors in topological order so foundational deficits appear first.
        """
        ancestors = self.get_ancestors(concept_id)
        if not ancestors:
            return []

        # Filter and sort by prerequisite depth
        blocking: List[str] = []
        for anc in ancestors:
            score = mastery_map.get(anc, 0.0)
            if score < competence_threshold:
                blocking.append(anc)

        # Sort blocking concepts by depth so root primitive deficits come first
        blocking.sort(key=lambda c: self.get_depth(c))
        return blocking

    def clear(self) -> None:
        """Clear all concepts and edges."""
        self._nodes.clear()

    def all_concepts(self) -> List[str]:
        """Return list of all concept identifiers."""
        return sorted(list(self._nodes.keys()))
