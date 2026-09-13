"""Tests for Document Understanding and Bounded PDF/Doc Chunking Subsystem."""

from __future__ import annotations

import tempfile
from pathlib import Path
import pytest

from tarkyaan.vision.document_understanding import (
    DocumentOutline,
    DocumentSection,
    DocumentUnderstandingEngine,
)


def test_document_understanding_markdown_chunking():
    """Verify document chunking detects structural headers and bounds sections."""
    doc_content = """# Dynamic Programming Tutorial
This is an overview of dynamic programming. Memoization saves redundant calculations.

## Overlapping Subproblems
When subproblems share sub-subproblems, dynamic programming computes each once.

## Optimal Substructure
An optimal solution contains optimal solutions to subproblems.

## Complexity Analysis
Tabulation typically yields O(N) space and time complexity for 1D problems.
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(doc_content)
        temp_path = f.name

    try:
        engine = DocumentUnderstandingEngine()
        outline: DocumentOutline = engine.parse_document(temp_path, max_chunk_words=100)

        assert outline.file_type == "md"
        assert outline.total_sections >= 3
        assert len(outline.sections) >= 3
        assert any("Overlapping Subproblems" in s.title for s in outline.sections)
        assert any("Optimal Substructure" in s.title for s in outline.sections)

        # Verify bounded retrieval
        relevant: list[DocumentSection] = engine.get_relevant_sections(outline, query_or_topic="complexity analysis", max_sections=1)
        assert len(relevant) == 1
        assert "Complexity Analysis" in relevant[0].title or "Complexity Analysis" in relevant[0].content
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_document_understanding_missing_file():
    """Verify handling of missing files returns informative error without crashing."""
    engine = DocumentUnderstandingEngine()
    outline = engine.parse_document("/nonexistent/path/to/missing_file.pdf")
    assert outline.total_sections == 0
    assert "File not found" in outline.summary


def test_document_understanding_code_file_parsing():
    """Verify source code file parsing into bounded sections."""
    code_content = """# Binary Search Tree Implementation
class Node:
    def __init__(self, val):
        self.val = val
        self.left = None
        self.right = None

# Section Insertion
def insert(root, key):
    if root is None:
        return Node(key)
    if key < root.val:
        root.left = insert(root.left, key)
    else:
        root.right = insert(root.right, key)
    return root
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code_content)
        temp_path = f.name

    try:
        engine = DocumentUnderstandingEngine()
        outline = engine.parse_document(temp_path)
        assert outline.file_type == "py"
        assert outline.total_sections >= 1
        assert "insert" in outline.sections[1].title.lower() or "root" in outline.summary.lower()
    finally:
        Path(temp_path).unlink(missing_ok=True)
