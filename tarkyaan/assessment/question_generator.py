"""
Diagnostic Question Generator.
Generates targeted Socratic diagnostic questions based on concept prerequisites,
current mastery tier, uncertainty, and observed misconceptions.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set

from tarkyaan.knowledge.prerequisite_graph import PrerequisiteDAG
from tarkyaan.models.diagnostic import (
    DiagnosticDimension,
    DiagnosticQuestion,
    QuestionType,
)
from tarkyaan.models.enums import MasteryTier
from tarkyaan.models.gaps import MisconceptionRecord
from tarkyaan.models.learner import LearnerProfile
from tarkyaan.models.mastery import TopicMastery


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class QuestionGenerator:
    """
    Socratic diagnostic question generator.
    Selects the next optimal probe based on pedagogical progression:
    - High uncertainty -> Conceptual / Trace probe
    - Weak fundamentals -> Simplified prerequisite probe
    - Competent -> Application / Debugging / Edge-case challenge
    """

    @classmethod
    def generate_question(
        cls,
        learner: LearnerProfile,
        concept_id: str,
        concept_name: str,
        current_mastery: float,
        uncertainty: float,
        dag: Optional[PrerequisiteDAG] = None,
        previous_questions: Optional[List[DiagnosticQuestion]] = None,
        recent_misconceptions: Optional[List[MisconceptionRecord]] = None
    ) -> DiagnosticQuestion:
        """
        Generate a diagnostic question tailored to the learner's current cognitive state.
        """
        prev_types: Set[QuestionType] = {q.question_type for q in (previous_questions or []) if q.concept_id == concept_id}
        prereqs = dag.get_prerequisites(concept_id) if dag and dag.has_concept(concept_id) else []

        # 1. Determine cognitive dimension and question type
        tier = cls._determine_target_dimension(current_mastery, uncertainty)
        q_type = cls._select_question_type(tier, prev_types)
        difficulty = min(5, max(1, int(current_mastery * 4) + 1))

        # 2. Build question prompt and expected reasoning
        prompt, reasoning, rubric = cls._compose_probe(
            concept_id=concept_id,
            concept_name=concept_name,
            q_type=q_type,
            dimension=tier,
            language=learner.preferred_language,
            prereqs=prereqs,
            difficulty=difficulty,
            recent_misconceptions=recent_misconceptions or []
        )

        return DiagnosticQuestion(
            question_id=f"dq_{uuid.uuid4().hex[:8]}",
            concept_id=concept_id,
            difficulty=difficulty,
            diagnostic_dimension=tier,
            question_type=q_type,
            prompt=prompt,
            expected_reasoning=reasoning,
            prerequisite_concepts=prereqs,
            evaluation_rubric=rubric,
            created_at=_utc_now()
        )

    @classmethod
    def _determine_target_dimension(cls, mastery: float, uncertainty: float) -> DiagnosticDimension:
        """Map mastery & uncertainty to the next diagnostic hurdle."""
        if uncertainty >= 0.70 or mastery < 0.20:
            return DiagnosticDimension.UNDERSTANDING
        elif mastery < 0.45:
            return DiagnosticDimension.RECALL
        elif mastery < 0.75:
            return DiagnosticDimension.APPLICATION
        else:
            return DiagnosticDimension.MASTERY

    @classmethod
    def _select_question_type(cls, dimension: DiagnosticDimension, prev_types: Set[QuestionType]) -> QuestionType:
        """Pick an inquiry style suited to the targeted dimension, rotating across styles."""
        dimension_map = {
            DiagnosticDimension.UNDERSTANDING: [QuestionType.CONCEPTUAL, QuestionType.WHY, QuestionType.WHAT_IF],
            DiagnosticDimension.RECALL: [QuestionType.TRACE, QuestionType.RECALL, QuestionType.CODE_READING],
            DiagnosticDimension.APPLICATION: [QuestionType.APPLICATION, QuestionType.DEBUGGING, QuestionType.CODE_WRITING],
            DiagnosticDimension.MASTERY: [QuestionType.EDGE_CASE, QuestionType.COMPARISON, QuestionType.TRANSFER]
        }

        candidates = dimension_map.get(dimension, [QuestionType.CONCEPTUAL])
        for c in candidates:
            if c not in prev_types:
                return c
        return candidates[0]

    @classmethod
    def _compose_probe(
        cls,
        concept_id: str,
        concept_name: str,
        q_type: QuestionType,
        dimension: DiagnosticDimension,
        language: str,
        prereqs: List[str],
        difficulty: int,
        recent_misconceptions: List[MisconceptionRecord]
    ) -> tuple[str, str, Dict[str, Any]]:
        """Synthesize the prompt text and evaluation criteria."""
        prereq_mention = f" (building on prerequisite knowledge of {', '.join(prereqs)})" if prereqs else ""

        if q_type == QuestionType.CONCEPTUAL:
            prompt = (
                f"In your own words, explain the core invariant of '{concept_name}'{prereq_mention}. "
                f"Why does this structure/technique guarantee correctness?"
            )
            reasoning = (
                f"Learner should articulate the foundational logic of {concept_name}, identifying the state "
                f"transition or mathematical guarantee rather than merely reciting surface definitions."
            )
            rubric = {"keywords": [concept_id, "guarantee", "invariant"], "expected_depth": "first_principles"}

        elif q_type == QuestionType.TRACE:
            prompt = (
                f"Trace step-by-step what happens in '{concept_name}'{prereq_mention} with a small test input "
                f"using {language}. Describe how memory/state evolves at each step."
            )
            reasoning = (
                f"Learner should trace exact state transformations (stack frames, index pointers, or variables) "
                f"without skipping intermediate steps."
            )
            rubric = {"keywords": ["step", "state", "variable", "pointer"], "expected_depth": "execution_trace"}

        elif q_type == QuestionType.DEBUGGING:
            prompt = (
                f"Consider an implementation of '{concept_name}'{prereq_mention} in {language} that exhibits an off-by-one boundary error "
                f"or infinite loop on edge inputs. What invariant condition was violated and how would you fix it?"
            )
            reasoning = (
                f"Learner must identify the specific boundary condition (e.g. <= vs <, base cases) and explain the fix."
            )
            rubric = {"keywords": ["boundary", "condition", "loop", "fix"], "expected_depth": "error_diagnosis"}

        elif q_type == QuestionType.EDGE_CASE:
            prompt = (
                f"What are the most critical edge cases for '{concept_name}'{prereq_mention} (e.g. empty inputs, duplicates, single elements)? "
                f"How does the algorithm prevent degradation or exceptions?"
            )
            reasoning = (
                f"Learner demonstrates mastery by examining boundary extremes and showing resilience against edge cases."
            )
            rubric = {"keywords": ["edge case", "empty", "overflow", "duplicates"], "expected_depth": "robustness"}

        elif q_type == QuestionType.COMPARISON:
            prompt = (
                f"Compare '{concept_name}'{prereq_mention} with alternative algorithmic approaches. "
                f"Under what specific time/space complexity or data layout constraints would you choose {concept_name} over the alternatives?"
            )
            reasoning = (
                f"Learner provides trade-off analysis comparing time/space complexity, cache locality, or operational overhead."
            )
            rubric = {"keywords": ["complexity", "trade-off", "alternative", "overhead"], "expected_depth": "trade_offs"}

        else:  # Default / APPLICATION
            prompt = (
                f"How would you apply '{concept_name}'{prereq_mention} in {language} to solve a real problem with constrained runtime? "
                f"Walk through the algorithmic outline and time complexity."
            )
            reasoning = (
                f"Learner constructs an algorithmic plan leveraging {concept_name} with accurate Big-O reasoning."
            )
            rubric = {"keywords": ["algorithm", "complexity", "implementation"], "expected_depth": "applied_synthesis"}

        return prompt, reasoning, rubric
