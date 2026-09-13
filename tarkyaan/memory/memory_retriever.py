"""
Contextual Memory Retrieval Engine.
Provides intelligent, bounded context assembly for LLM prompts
with strict learner isolation and token budgeting.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from tarkyaan.memory.memory_manager import TarkyaanMemoryManager
from tarkyaan.models.enums import EpistemicStatus, MemoryType


@dataclass
class ContextualMemorySummary:
    """
    Bounded, formatted memory summary tailored for pedagogical prompting.
    """
    learner_id: str
    display_name: str
    domain: str
    preferred_language: str
    active_goals: List[str] = field(default_factory=list)
    current_topic_mastery: Optional[Dict[str, Any]] = None
    unresolved_gaps: List[Dict[str, Any]] = field(default_factory=list)
    recent_misconceptions: List[str] = field(default_factory=list)
    recent_session_notes: List[str] = field(default_factory=list)
    explicit_facts: List[str] = field(default_factory=list)
    system_inferences: List[str] = field(default_factory=list)
    formatted_prompt_text: str = ""


class MemoryRetriever:
    """
    Retrieves and filters contextual memories for a learner.
    Enforces strict tenant isolation: Learner A's data can never be returned for Learner B.
    """

    def __init__(self, memory_manager: TarkyaanMemoryManager) -> None:
        self._mgr = memory_manager

    def retrieve_context(
        self,
        learner_id: str,
        current_topic: Optional[str] = None,
        query: Optional[str] = None,
        token_budget: int = 1500
    ) -> ContextualMemorySummary:
        """
        Extract relevant learner context respecting character/token limits.
        :param learner_id: Mandatory target learner ID.
        :param current_topic: Optional active topic to focus retrieval.
        :param query: Optional semantic query to match content keywords.
        :param token_budget: Approximate token limit (estimated at ~4 chars per token).
        """
        char_budget = token_budget * 4

        # 1. Profile
        profile = self._mgr.get_learner(learner_id)
        if not profile:
            return ContextualMemorySummary(
                learner_id=learner_id,
                display_name="Unknown",
                domain="General",
                preferred_language="Unknown",
                formatted_prompt_text="[No profile found for learner]"
            )

        summary = ContextualMemorySummary(
            learner_id=profile.learner_id,
            display_name=profile.display_name,
            domain=profile.primary_domain,
            preferred_language=profile.preferred_language
        )

        # 2. Active Goals
        goals = self._mgr.get_goals(learner_id, active_only=True)
        for g in goals[:3]:
            deadline_str = f" (Deadline: {g.deadline.strftime('%Y-%m-%d')})" if g.deadline else ""
            summary.active_goals.append(f"{g.title} [{g.target_outcome}]{deadline_str}")

        # 3. Topic Mastery
        if current_topic:
            mastery = self._mgr.get_topic_mastery(learner_id, current_topic)
            if mastery:
                summary.current_topic_mastery = {
                    "topic": mastery.name,
                    "score": round(mastery.mastery_score, 2),
                    "tier": mastery.tier.value,
                    "uncertainty": round(mastery.uncertainty, 2),
                    "last_practiced": mastery.last_practiced.isoformat() if mastery.last_practiced else None
                }

        # 4. Unresolved Gaps
        gaps = self._mgr.get_active_gaps(learner_id)
        for gap in gaps[:4]:
            summary.unresolved_gaps.append({
                "concept": gap.concept_id,
                "blocking": gap.blocking_topic_id,
                "severity": gap.severity,
                "evidence": gap.diagnostic_evidence
            })

        # 5. Recent Misconceptions
        misc_records = self._mgr.get_misconceptions(learner_id, topic_id=current_topic)
        for m in misc_records[:3]:
            summary.recent_misconceptions.append(f"[{m.category.value}] {m.description}")

        # 6. Recent Sessions
        sessions = self._mgr.get_learning_sessions(learner_id, limit=2)
        for s in sessions:
            if s.notes:
                summary.recent_session_notes.append(f"Session {s.session_id}: {s.notes}")

        # 7. Explicit Facts vs Inferences
        mem_items = self._mgr.get_memory_items(learner_id, min_importance=2)
        for item in mem_items[:8]:
            # Update access telemetry
            item.access()
            if item.epistemic_status == EpistemicStatus.FACT:
                summary.explicit_facts.append(f"{item.key}: {item.content}")
            else:
                summary.system_inferences.append(f"{item.key} (conf={round(item.confidence, 2)}): {item.content}")

        # 8. Assemble formatted prompt block within budget
        lines = [
            f"### LEARNER CONTEXT: {summary.display_name} ({summary.preferred_language} | {summary.domain})",
            f"Daily Time Budget: {profile.daily_time_budget_minutes} mins | Autonomy Level: {profile.current_autonomy_level.name}"
        ]

        if summary.active_goals:
            lines.append(f"Active Goals: {'; '.join(summary.active_goals)}")

        if summary.current_topic_mastery:
            m = summary.current_topic_mastery
            lines.append(f"Active Topic: {m['topic']} (Mastery: {m['score']}, Tier: {m['tier']}, Uncertainty: {m['uncertainty']})")

        if summary.unresolved_gaps:
            gap_strs = [f"{g['concept']} (blocks {g['blocking']})" for g in summary.unresolved_gaps]
            lines.append(f"Active Gaps: {'; '.join(gap_strs)}")

        if summary.recent_misconceptions:
            lines.append(f"Recent Roadblocks: {'; '.join(summary.recent_misconceptions)}")

        if summary.explicit_facts:
            lines.append(f"Verified Facts: {'; '.join(summary.explicit_facts[:4])}")

        if summary.system_inferences:
            lines.append(f"Model Inferences: {'; '.join(summary.system_inferences[:3])}")

        raw_text = "\n".join(lines)
        if len(raw_text) > char_budget:
            raw_text = raw_text[:char_budget] + "\n... [Context truncated to fit token budget]"

        summary.formatted_prompt_text = raw_text
        return summary
