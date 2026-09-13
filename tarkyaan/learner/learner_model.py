"""
Tarkyaan Learner Model.
The central cognitive representation of a learner. Coordinates knowledge state,
Bayesian mastery updates, retention decay, gap detection, and episodic history
using Tarkyaan's independent persistent memory system.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from tarkyaan.learner.mastery_engine import MasteryEngine
from tarkyaan.learner.retention_engine import RetentionEngine
from tarkyaan.memory.memory_manager import TarkyaanMemoryManager
from tarkyaan.memory.memory_models import MemoryItem
from tarkyaan.models.assessment import AssessmentResult
from tarkyaan.models.enums import (
    AutonomyLevel,
    EpistemicStatus,
    MasteryTier,
    MemorySource,
    MemoryType,
    MisconceptionCategory,
)
from tarkyaan.models.gaps import KnowledgeGap, MisconceptionRecord
from tarkyaan.models.goals import LearningGoal
from tarkyaan.models.learner import LearnerProfile
from tarkyaan.models.learning import LearningSession
from tarkyaan.models.mastery import Subject, Topic, TopicMastery


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class LearnerModel:
    """
    Central cognitive model representing an individual learner in Tarkyaan.
    """

    def __init__(
        self,
        learner_id: Optional[str] = None,
        memory_manager: Optional[TarkyaanMemoryManager] = None
    ) -> None:
        self.memory = memory_manager or TarkyaanMemoryManager()
        self.learner_id = learner_id
        self._profile: Optional[LearnerProfile] = None

        if self.learner_id:
            self._profile = self.memory.get_learner(self.learner_id)

    @property
    def profile(self) -> LearnerProfile:
        if not self._profile:
            raise ValueError(f"No active learner profile initialized or found for ID '{self.learner_id}'.")
        return self._profile

    # =========================================================================
    # 1. LIFECYCLE & PROFILE
    # =========================================================================

    def initialize_learner(
        self,
        display_name: str = "Learner",
        primary_domain: str = "Computer Science / DSA",
        preferred_language: str = "C++",
        daily_time_budget_minutes: int = 120,
        autonomy_level: AutonomyLevel = AutonomyLevel.LEVEL_3
    ) -> LearnerProfile:
        """Create and persist a new learner profile."""
        profile = LearnerProfile(
            display_name=display_name,
            primary_domain=primary_domain,
            preferred_language=preferred_language,
            daily_time_budget_minutes=daily_time_budget_minutes,
            current_autonomy_level=autonomy_level
        )
        self.memory.create_learner(profile)
        self.learner_id = profile.learner_id
        self._profile = profile

        # Record explicit profile fact in memory items
        self.memory.store_memory_item(MemoryItem(
            learner_id=self.learner_id,
            memory_type=MemoryType.SEMANTIC_LEARNER,
            key="preferred_language",
            content=f"Primary language is {preferred_language}",
            source=MemorySource.USER_EXPLICIT,
            epistemic_status=EpistemicStatus.FACT,
            importance=5
        ))
        return profile

    def load_learner(self, learner_id: str) -> Optional[LearnerProfile]:
        """Load an existing learner from persistent storage."""
        p = self.memory.get_learner(learner_id)
        if p:
            self.learner_id = learner_id
            self._profile = p
        return p

    def update_profile(
        self,
        display_name: Optional[str] = None,
        primary_domain: Optional[str] = None,
        preferred_language: Optional[str] = None,
        daily_time_budget_minutes: Optional[int] = None,
        autonomy_level: Optional[AutonomyLevel] = None
    ) -> LearnerProfile:
        """Update active profile attributes."""
        prof = self.profile
        if display_name is not None:
            prof.display_name = display_name
        if primary_domain is not None:
            prof.primary_domain = primary_domain
        if preferred_language is not None:
            prof.preferred_language = preferred_language
        if daily_time_budget_minutes is not None:
            prof.daily_time_budget_minutes = daily_time_budget_minutes
        if autonomy_level is not None:
            prof.current_autonomy_level = autonomy_level

        return self.memory.update_learner(prof)

    # =========================================================================
    # 2. GOALS
    # =========================================================================

    def create_goal(
        self,
        title: str,
        target_outcome: str,
        deadline: Optional[datetime] = None,
        daily_hours: float = 2.0,
        priority: int = 3
    ) -> LearningGoal:
        """Create and track a new learning goal."""
        goal = LearningGoal(
            learner_id=self.profile.learner_id,
            title=title,
            target_outcome=target_outcome,
            deadline=deadline,
            daily_hours=daily_hours,
            priority=priority
        )
        self.memory.create_goal(goal)

        self.memory.store_memory_item(MemoryItem(
            learner_id=self.profile.learner_id,
            memory_type=MemoryType.GOAL_MEMORY,
            key=f"goal_{goal.goal_id}",
            content=f"{title}: {target_outcome}",
            source=MemorySource.USER_EXPLICIT,
            epistemic_status=EpistemicStatus.FACT,
            importance=priority
        ))
        return goal

    def get_active_goals(self) -> List[LearningGoal]:
        """Retrieve all non-completed goals."""
        return self.memory.get_goals(self.profile.learner_id, active_only=True)

    # =========================================================================
    # 3. CURRICULUM & TOPICS
    # =========================================================================

    def register_topic(
        self,
        topic_id: str,
        name: str,
        subject_id: str = "dsa",
        subject_name: str = "Data Structures & Algorithms",
        description: Optional[str] = None,
        prerequisites: Optional[List[str]] = None
    ) -> TopicMastery:
        """
        Register a concept in the curriculum and initialize learner mastery state.
        """
        prereqs = prerequisites or []
        # Ensure subject exists
        if not self.memory.get_subject(subject_id):
            self.memory.create_subject(Subject(subject_id=subject_id, name=subject_name))

        # Register topic definition
        self.memory.create_topic(Topic(
            topic_id=topic_id,
            subject_id=subject_id,
            name=name,
            description=description,
            prerequisites=prereqs
        ))

        # Check if mastery already exists
        existing = self.memory.get_topic_mastery(self.profile.learner_id, topic_id)
        if existing:
            return existing

        # Initialize unpracticed mastery
        initial_mastery = TopicMastery(
            learner_id=self.profile.learner_id,
            topic_id=topic_id,
            subject_id=subject_id,
            name=name,
            mastery_score=0.0,
            uncertainty=1.0,
            tier=MasteryTier.UNEXPLORED,
            prerequisites=prereqs
        )
        return self.memory.update_topic_mastery(initial_mastery)

    def get_topic_mastery(self, topic_id: str) -> Optional[TopicMastery]:
        return self.memory.get_topic_mastery(self.profile.learner_id, topic_id)

    def list_all_masteries(self) -> List[TopicMastery]:
        return self.memory.list_topic_mastery(self.profile.learner_id)

    # =========================================================================
    # 4. EVIDENCE-BASED MASTERY UPDATES
    # =========================================================================

    def update_mastery_from_assessment(
        self,
        topic_id: str,
        score: float,
        task_id: Optional[str] = None,
        feedback: str = "",
        identified_misconceptions: Optional[List[str]] = None
    ) -> AssessmentResult:
        """
        Incorporate empirical performance into Bayesian mastery state.
        """
        mastery = self.get_topic_mastery(topic_id)
        if not mastery:
            mastery = self.register_topic(topic_id=topic_id, name=topic_id)

        # Apply deterministic update
        calc = MasteryEngine.calculate_update(
            current_mastery=mastery.mastery_score,
            current_uncertainty=mastery.uncertainty,
            evidence_score=score
        )

        # Update stability factor based on recall performance
        new_stability = RetentionEngine.calculate_reinforced_stability(
            current_stability=mastery.stability_factor,
            recall_score=score
        )

        # Update mastery object
        mastery.mastery_score = calc.new_mastery
        mastery.uncertainty = calc.new_uncertainty
        mastery.tier = calc.new_tier
        mastery.stability_factor = new_stability
        mastery.last_practiced = _utc_now()
        if score >= 0.70:
            mastery.successful_recalls += 1
        else:
            mastery.failed_recalls += 1

        self.memory.update_topic_mastery(mastery)

        # Create immutable assessment record
        misconceptions = identified_misconceptions or []
        assessment = AssessmentResult(
            learner_id=self.profile.learner_id,
            topic_id=topic_id,
            task_id=task_id,
            score=score,
            prior_mastery=calc.prior_mastery,
            new_mastery=calc.new_mastery,
            prior_uncertainty=calc.prior_uncertainty,
            new_uncertainty=calc.new_uncertainty,
            evaluated_tier=calc.new_tier,
            identified_misconceptions=misconceptions,
            feedback_notes=feedback
        )
        self.memory.record_assessment(assessment)

        # Record inference memory item
        self.memory.store_memory_item(MemoryItem(
            learner_id=self.profile.learner_id,
            memory_type=MemoryType.KNOWLEDGE_STATE,
            key=f"mastery_{topic_id}",
            content=f"Mastery of {mastery.name} updated to {calc.new_mastery} ({calc.new_tier.value}) based on test score {score}",
            source=MemorySource.ASSESSMENT,
            epistemic_status=EpistemicStatus.INFERENCE,
            importance=4,
            confidence=round(1.0 - calc.new_uncertainty, 2),
            topic_id=topic_id
        ))

        return assessment

    def apply_temporal_decay(
        self,
        topic_id: str,
        as_of: Optional[datetime] = None
    ) -> float:
        """Compute and persist retention decay for a topic."""
        mastery = self.get_topic_mastery(topic_id)
        if not mastery or not mastery.last_practiced:
            return 0.0

        decayed = RetentionEngine.calculate_decayed_mastery(
            current_mastery=mastery.mastery_score,
            last_practiced=mastery.last_practiced,
            as_of=as_of,
            stability_days=mastery.stability_factor
        )

        if decayed != mastery.mastery_score:
            mastery.mastery_score = decayed
            mastery.tier = MasteryEngine.classify_tier(decayed, mastery.uncertainty)
            self.memory.update_topic_mastery(mastery)

        return decayed

    # =========================================================================
    # 5. KNOWLEDGE GAPS & MISCONCEPTIONS
    # =========================================================================

    def flag_knowledge_gap(
        self,
        concept_id: str,
        blocking_topic_id: str,
        diagnostic_evidence: str,
        severity: str = "high"
    ) -> KnowledgeGap:
        """Register an active knowledge gap."""
        gap = KnowledgeGap(
            learner_id=self.profile.learner_id,
            concept_id=concept_id,
            blocking_topic_id=blocking_topic_id,
            severity=severity,
            diagnostic_evidence=diagnostic_evidence
        )
        self.memory.create_knowledge_gap(gap)

        self.memory.store_memory_item(MemoryItem(
            learner_id=self.profile.learner_id,
            memory_type=MemoryType.KNOWLEDGE_STATE,
            key=f"gap_{gap.gap_id}",
            content=f"Deficit in {concept_id} blocking {blocking_topic_id}: {diagnostic_evidence}",
            source=MemorySource.SYSTEM_INFERENCE,
            epistemic_status=EpistemicStatus.INFERENCE,
            importance=5,
            topic_id=concept_id
        ))
        return gap

    def resolve_knowledge_gap(self, gap_id: str) -> bool:
        """Mark a diagnosed gap as resolved."""
        return self.memory.resolve_knowledge_gap(self.profile.learner_id, gap_id)

    def flag_misconception(
        self,
        topic_id: str,
        category: MisconceptionCategory,
        description: str,
        observed_code: Optional[str] = None,
        code_snippet: Optional[str] = None,
        corrective_action: str = ""
    ) -> MisconceptionRecord:
        """Record an observed conceptual or algorithmic misconception."""
        snippet = code_snippet if code_snippet is not None else observed_code
        rec = MisconceptionRecord(
            learner_id=self.profile.learner_id,
            topic_id=topic_id,
            category=category,
            description=description,
            observed_code_snippet=snippet,
            corrective_action_taken=corrective_action
        )
        return self.memory.record_misconception(rec)

    # =========================================================================
    # 6. SESSIONS & SNAPSHOTS
    # =========================================================================

    def log_learning_session(
        self,
        goal_id: Optional[str],
        duration_minutes: float,
        topics_covered: List[str],
        tasks_completed: List[str],
        notes: str = ""
    ) -> LearningSession:
        """Log a completed focus study session."""
        sess = LearningSession(
            learner_id=self.profile.learner_id,
            goal_id=goal_id,
            duration_minutes=duration_minutes,
            topics_covered=topics_covered,
            tasks_completed=tasks_completed,
            notes=notes
        )
        return self.memory.record_learning_session(sess)

    def get_learner_snapshot(self) -> Dict[str, Any]:
        """Produce an immutable serialized snapshot of learner state."""
        prof = self.profile
        goals = self.get_active_goals()
        masteries = self.list_all_masteries()
        gaps = self.memory.get_active_gaps(prof.learner_id)
        sessions = self.memory.get_learning_sessions(prof.learner_id, limit=5)

        return {
            "learner_id": prof.learner_id,
            "display_name": prof.display_name,
            "primary_domain": prof.primary_domain,
            "preferred_language": prof.preferred_language,
            "daily_time_budget_minutes": prof.daily_time_budget_minutes,
            "autonomy_level": prof.current_autonomy_level.name,
            "active_goals": [g.model_dump() for g in goals],
            "total_topics_tracked": len(masteries),
            "mastered_topics": [m.topic_id for m in masteries if m.tier == MasteryTier.MASTERED],
            "practicing_topics": [m.topic_id for m in masteries if m.tier == MasteryTier.PRACTICING],
            "active_knowledge_gaps": [g.model_dump() for g in gaps],
            "recent_sessions_count": len(sessions),
            "snapshot_taken_at": _utc_now().isoformat()
        }
