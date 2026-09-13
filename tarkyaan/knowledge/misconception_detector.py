"""
Misconception Detection Engine.
Identifies conceptual, algorithmic, syntax, and cognitive fatigue patterns
from learner errors and evaluates diagnosis confidence.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from tarkyaan.models.enums import MisconceptionCategory
from tarkyaan.models.gaps import MisconceptionRecord


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class CandidateMisconception:
    """An inferred cognitive flaw under observation before formal confirmation."""
    topic_id: str
    category: MisconceptionCategory
    description: str
    confidence: float  # 0.0 to 1.0
    supporting_evidence: List[str] = field(default_factory=list)
    observed_code_snippet: Optional[str] = None
    is_confirmed: bool = False


class MisconceptionDetector:
    """
    Detects and classifies patterns of learner struggle.
    Enforces strict rules:
    - Never flags COGNITIVE_FATIGUE on a single error.
    - Requires cumulative evidence to reach high confidence.
    """

    FATIGUE_MIN_SESSION_MINUTES: float = 75.0
    CONFIRMATION_THRESHOLD: float = 0.70

    @classmethod
    def evaluate_error(
        cls,
        learner_id: str,
        topic_id: str,
        error_tags: List[str],
        reasoning_excerpt: str = "",
        code_snippet: Optional[str] = None,
        prior_mastery: float = 0.0,
        recent_scores: Optional[List[float]] = None,
        session_duration_minutes: float = 0.0,
        prior_misconceptions: Optional[List[MisconceptionRecord]] = None
    ) -> List[CandidateMisconception]:
        """
        Analyze an error or suboptimal response and return candidate misconceptions.
        """
        candidates: List[CandidateMisconception] = []
        prior_misc_list = prior_misconceptions or []
        scores = recent_scores or []

        # 1. Cognitive Fatigue Check (Strict Rule: NEVER diagnose from a single wrong answer!)
        # Requires: long session OR sudden plunge after demonstrated competence
        has_long_session = session_duration_minutes >= cls.FATIGUE_MIN_SESSION_MINUTES
        had_prior_competence = prior_mastery >= 0.70
        sudden_drop = len(scores) >= 3 and scores[-1] < 0.3 and (sum(scores[:-1]) / len(scores[:-1])) >= 0.75

        if has_long_session and (sudden_drop or had_prior_competence):
            candidates.append(CandidateMisconception(
                topic_id=topic_id,
                category=MisconceptionCategory.COGNITIVE_FATIGUE,
                description="Sudden performance decline following sustained session duration (>75 min); suggests cognitive overload or fatigue.",
                confidence=0.75 if sudden_drop else 0.55,
                supporting_evidence=[
                    f"Session duration: {session_duration_minutes}m",
                    f"Prior mastery: {round(prior_mastery, 2)}",
                    f"Recent scores: {scores}"
                ]
            ))

        # 2. Syntax / Idiomatic Friction Check
        syntax_keywords = {"syntax", "compilation", "type_mismatch", "semicolon", "undefined_identifier", "header"}
        syntax_matches = [tag for tag in error_tags if any(k in tag.lower() for k in syntax_keywords)]
        if syntax_matches or (code_snippet and ("error: expected" in reasoning_excerpt.lower() or "undeclared" in reasoning_excerpt.lower())):
            candidates.append(CandidateMisconception(
                topic_id=topic_id,
                category=MisconceptionCategory.SYNTAX_IDIOM,
                description=f"Syntax or language construct friction: {', '.join(syntax_matches or ['language syntax issue'])}",
                confidence=0.85,
                supporting_evidence=[reasoning_excerpt] if reasoning_excerpt else syntax_matches,
                observed_code_snippet=code_snippet
            ))

        # 3. Algorithmic Logic Check (Boundary, Off-by-one, Loop condition)
        logic_keywords = {"off_by_one", "boundary", "infinite_loop", "null_pointer", "index_out_of_bounds", "pivot_choice"}
        logic_matches = [tag for tag in error_tags if any(k in tag.lower() for k in logic_keywords)]
        if logic_matches or "infinite loop" in reasoning_excerpt.lower() or "off-by-one" in reasoning_excerpt.lower():
            # Check if this error repeated from prior observations
            repeat_count = sum(1 for m in prior_misc_list if m.category == MisconceptionCategory.ALGORITHMIC_LOGIC and m.topic_id == topic_id)
            conf = min(0.95, 0.65 + (repeat_count * 0.15))

            candidates.append(CandidateMisconception(
                topic_id=topic_id,
                category=MisconceptionCategory.ALGORITHMIC_LOGIC,
                description=f"Algorithmic boundary condition or loop logic flaw: {', '.join(logic_matches or ['index/loop condition error'])}",
                confidence=round(conf, 2),
                supporting_evidence=[reasoning_excerpt],
                observed_code_snippet=code_snippet,
                is_confirmed=(conf >= cls.CONFIRMATION_THRESHOLD)
            ))

        # 4. Conceptual Deficit Check (Flawed theoretical assumption, false mental model)
        conceptual_keywords = {"false_assumption", "wrong_paradigm", "call_stack_misunderstanding", "greedy_on_dp", "tree_depth_height"}
        concept_matches = [tag for tag in error_tags if any(k in tag.lower() for k in conceptual_keywords)]
        # Default to conceptual only if there are error tags that were not classified by other categories
        if concept_matches or (error_tags and not candidates):
            repeat_count = sum(1 for m in prior_misc_list if m.category == MisconceptionCategory.CONCEPTUAL and m.topic_id == topic_id)
            conf = min(0.95, 0.70 + (repeat_count * 0.15))

            desc = f"Flawed conceptual model: {', '.join(concept_matches or ['misunderstanding of core concept mechanics'])}"
            candidates.append(CandidateMisconception(
                topic_id=topic_id,
                category=MisconceptionCategory.CONCEPTUAL,
                description=desc,
                confidence=round(conf, 2),
                supporting_evidence=[reasoning_excerpt] if reasoning_excerpt else ["Incorrect theoretical reasoning"],
                observed_code_snippet=code_snippet,
                is_confirmed=(conf >= cls.CONFIRMATION_THRESHOLD)
            ))

        return candidates

    @classmethod
    def create_record(
        cls,
        learner_id: str,
        candidate: CandidateMisconception,
        corrective_action: str = ""
    ) -> MisconceptionRecord:
        """Convert a confirmed or high-confidence candidate into a persistent MisconceptionRecord."""
        return MisconceptionRecord(
            record_id=f"misc_{uuid.uuid4().hex[:8]}",
            learner_id=learner_id,
            topic_id=candidate.topic_id,
            category=candidate.category,
            description=candidate.description,
            observed_code_snippet=candidate.observed_code_snippet,
            corrective_action_taken=corrective_action or f"Address {candidate.category.value} misconception via targeted probe."
        )
