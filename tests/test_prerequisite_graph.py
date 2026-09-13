"""
Unit tests for PrerequisiteDAG knowledge graph.
Tests node insertion, cycle detection, topological sorting,
ancestor/descendant traversal, and blocking prerequisite identification.
"""

import pytest

from tarkyaan.knowledge.prerequisite_graph import (
    ConceptNotFoundError,
    CyclicDependencyError,
    PrerequisiteDAG,
)


class TestPrerequisiteGraph:
    def test_add_and_query_concepts(self):
        dag = PrerequisiteDAG()
        dag.add_concept("c1", name="Variables", subject_id="prog")
        dag.add_concept("c2", name="Conditionals", subject_id="prog")

        assert dag.has_concept("c1")
        assert dag.has_concept("c2")
        assert not dag.has_concept("c3")

        node = dag.get_concept("c1")
        assert node.name == "Variables"
        assert node.subject_id == "prog"

    def test_add_prerequisites_and_relationships(self):
        dag = PrerequisiteDAG()
        # c1 -> c2 (c1 is prerequisite for c2)
        dag.add_prerequisite("c2", "c1")
        # c2 -> c3
        dag.add_prerequisite("c3", "c2")

        assert dag.get_prerequisites("c2") == ["c1"]
        assert dag.get_dependents("c2") == ["c3"]
        assert dag.get_ancestors("c3") == {"c1", "c2"}
        assert dag.get_descendants("c1") == {"c2", "c3"}

    def test_cycle_detection_direct(self):
        dag = PrerequisiteDAG()
        dag.add_prerequisite("c2", "c1")

        # Attempting c1 -> c2 creates a 2-node cycle
        with pytest.raises(CyclicDependencyError):
            dag.add_prerequisite("c1", "c2")

    def test_cycle_detection_multihop(self):
        dag = PrerequisiteDAG()
        # A -> B -> C -> D
        dag.add_prerequisite("b", "a")
        dag.add_prerequisite("c", "b")
        dag.add_prerequisite("d", "c")

        # Attempting D -> A creates A -> B -> C -> D -> A cycle
        with pytest.raises(CyclicDependencyError):
            dag.add_prerequisite("a", "d")

    def test_self_loop_rejection(self):
        dag = PrerequisiteDAG()
        with pytest.raises(CyclicDependencyError):
            dag.add_prerequisite("self", "self")

    def test_topological_sort(self):
        dag = PrerequisiteDAG()
        dag.add_prerequisite("trees", "recursion")
        dag.add_prerequisite("recursion", "stack_memory")
        dag.add_prerequisite("stack_memory", "functions")

        order = dag.topological_sort()
        assert order.index("functions") < order.index("stack_memory")
        assert order.index("stack_memory") < order.index("recursion")
        assert order.index("recursion") < order.index("trees")

    def test_roots_and_leaves(self):
        dag = PrerequisiteDAG()
        dag.add_prerequisite("b", "a")
        dag.add_prerequisite("c", "b")
        dag.add_prerequisite("d", "a")

        assert dag.get_roots() == ["a"]
        assert dag.get_leaves() == ["c", "d"]

    def test_depth_calculation(self):
        dag = PrerequisiteDAG()
        dag.add_prerequisite("b", "a")
        dag.add_prerequisite("c", "b")
        dag.add_prerequisite("d", "c")

        assert dag.get_depth("a") == 0
        assert dag.get_depth("b") == 1
        assert dag.get_depth("c") == 2
        assert dag.get_depth("d") == 3

    def test_find_blocking_prerequisites(self):
        dag = PrerequisiteDAG()
        # functions -> stack_memory -> recursion -> trees
        dag.add_prerequisite("stack_memory", "functions")
        dag.add_prerequisite("recursion", "stack_memory")
        dag.add_prerequisite("trees", "recursion")

        mastery_map = {
            "functions": 0.85,     # Competent
            "stack_memory": 0.30,  # Weak / Blocking
            "recursion": 0.50,     # Practicing / Blocking
            "trees": 0.10
        }

        blocking = dag.find_blocking_prerequisites("trees", mastery_map, competence_threshold=0.70)
        # Should return unmastered ancestors sorted by depth (stack_memory before recursion)
        assert blocking == ["stack_memory", "recursion"]
        assert "functions" not in blocking
