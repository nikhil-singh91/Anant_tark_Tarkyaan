"""
Targeted Query Generator for Educational Research.
Synthesizes structured, pedagogically differentiated search queries.
"""

from __future__ import annotations

from typing import List, Optional
from tarkyaan.models.enums import TaskType
from tarkyaan.models.research import ResearchIntent


class QueryGenerator:
    """
    Generates structured, task-calibrated search queries based on learning intent.
    Prevents vague single-word searches and targets appropriate difficulty and resource types.
    """

    TASK_TYPE_MODIFIERS = {
        TaskType.LEARN: ["tutorial", "comprehensive guide", "concept explanation"],
        TaskType.UNDERSTAND: ["visual intuition", "how it works", "diagrams examples"],
        TaskType.RECALL: ["cheat sheet", "key properties summary", "reference notes"],
        TaskType.PRACTICE: ["practice problems", "exercises solutions", "interactive challenge"],
        TaskType.APPLY: ["implementation examples", "real world use cases", "code tutorial"],
        TaskType.EXPLAIN: ["invariants proof", "step by step breakdown", "deep dive"],
        TaskType.COMPARE: ["vs comparison", "tradeoffs complexity", "difference between"],
        TaskType.SOLVE: ["problem walkthrough", "solution patterns", "coding problems"],
        TaskType.DEBUG: ["common bugs mistakes", "edge cases pitfalls", "debugging guide"],
        TaskType.REVIEW: ["refresher summary", "quick review", "overview"],
        TaskType.ASSESSMENT: ["quiz questions", "mock interview problems", "test understanding"],
    }

    @classmethod
    def generate_queries(
        cls,
        intent: ResearchIntent,
        task_type: TaskType = TaskType.LEARN,
        max_queries: int = 3
    ) -> List[str]:
        """
        Synthesize 1 to max_queries specific search strings based on intent.
        """
        concept = (intent.concept_name or intent.concept_id or "").replace("_", " ").strip()
        queries: List[str] = []

        # 1. Primary Conceptual / Task-specific Query
        modifiers = cls.TASK_TYPE_MODIFIERS.get(task_type, ["guide", "explanation"])
        primary_mod = modifiers[0]

        lang_suffix = f"{intent.programming_language} " if intent.programming_language else ""
        queries.append(f"{concept} {lang_suffix}{primary_mod}".strip())

        # 2. Level / Objective Specific Query
        level_term = "beginner" if intent.difficulty <= 2 else ("intermediate" if intent.difficulty <= 4 else "advanced")
        if task_type in (TaskType.PRACTICE, TaskType.SOLVE, TaskType.APPLY):
            queries.append(f"{concept} {lang_suffix}{level_term} practice problems exercises".strip())
        else:
            queries.append(f"{concept} {lang_suffix}{level_term} visual explanation examples".strip())

        # 3. In-depth Reference or Invariant Query
        if max_queries >= 3:
            if intent.difficulty >= 3 or task_type in (TaskType.EXPLAIN, TaskType.COMPARE):
                queries.append(f"{concept} algorithms invariants time complexity analysis".strip())
            else:
                queries.append(f"{concept} official documentation best practices".strip())

        # Ensure queries are unique and non-empty
        seen = set()
        clean_queries = []
        for q in queries:
            normalized = " ".join(q.split()).strip()
            if normalized and normalized.lower() not in seen:
                seen.add(normalized.lower())
                clean_queries.append(normalized)

        return clean_queries[:max_queries]
