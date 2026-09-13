"""
Voice Context Resolver for Tarkyaan Phase 5.
Resolves anaphoric expressions, implicit topic references, and active session context.
"""

from __future__ import annotations

import re
from typing import Optional
from tarkyaan.models.learning import LearningSession


class VoiceContextResolver:
    """
    Maintains conversational memory of recent entities and concepts.
    Maps phrases like 'make it harder' or 'explain it simply' to the active concept.
    """

    def __init__(self) -> None:
        self.last_concept: Optional[str] = None
        self.last_question_id: Optional[str] = None
        self.current_difficulty: int = 2

    def update_context(
        self,
        concept_id: Optional[str] = None,
        question_id: Optional[str] = None,
        difficulty: Optional[int] = None
    ) -> None:
        """Update active contextual pointers."""
        if concept_id:
            self.last_concept = concept_id
        if question_id:
            self.last_question_id = question_id
        if difficulty is not None:
            self.current_difficulty = difficulty

    def sync_with_session(self, session: LearningSession) -> None:
        """Sync context resolver state with an active LearningSession."""
        if session.concept_id:
            self.last_concept = session.concept_id
        if session.questions_asked:
            last_q = session.questions_asked[-1]
            self.last_question_id = last_q.question_id
            self.current_difficulty = last_q.difficulty

    def resolve_concept(self, user_utterance: str, extracted_arg: Optional[str] = None) -> str:
        """
        Resolve what concept the user is referring to.
        If extracted_arg is provided (e.g. "teach me recursion" -> "recursion"), use it.
        If user says "explain it" or "make it harder", resolve to last_concept.
        """
        if extracted_arg:
            cleaned = extracted_arg.strip().lower()
            if cleaned not in ("it", "this", "that", "the concept"):
                c_id = cleaned.replace(" ", "_")
                self.last_concept = c_id
                return c_id

        # Check for pronouns in utterance
        cleaned_utt = user_utterance.lower().strip()
        if any(w in cleaned_utt for w in [" it", " this", " that"]) and self.last_concept:
            return self.last_concept

        return self.last_concept or "general_learning"

    def adjust_difficulty(self, direction: str) -> int:
        """Adjust tracked difficulty level up or down."""
        if direction == "up":
            self.current_difficulty = min(5, self.current_difficulty + 1)
        elif direction == "down":
            self.current_difficulty = max(1, self.current_difficulty - 1)
        return self.current_difficulty
