"""
Tarkyaan Memory Manager.
High-level API for persisting, retrieving, updating, and querying all learner memory.
Entirely independent of NOVA.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from tarkyaan.memory.memory_models import MemoryItem
from tarkyaan.memory.memory_store import TarkyaanMemoryStore
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
from tarkyaan.models.learning import LearningSession, ProgressSnapshot
from tarkyaan.models.mastery import Subject, Topic, TopicMastery


def _iso(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat() if dt else None


def _parse_dt(val: Optional[str]) -> Optional[datetime]:
    if not val:
        return None
    try:
        return datetime.fromisoformat(val)
    except Exception:
        return None


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TarkyaanMemoryManager:
    """
    Central memory manager for Tarkyaan.
    Maintains persistent learner state, goals, curriculum progress,
    episodic sessions, and interaction history.
    """

    def __init__(self, store: Optional[TarkyaanMemoryStore] = None) -> None:
        self.store = store or TarkyaanMemoryStore()

    # =========================================================================
    # 1. LEARNER PROFILE
    # =========================================================================

    def create_learner(self, profile: LearnerProfile) -> LearnerProfile:
        sql = """
        INSERT INTO learners (
            learner_id, display_name, primary_domain, preferred_language,
            preferred_learning_style, preferred_explanation_style,
            daily_time_budget_minutes, current_autonomy_level,
            known_strengths, known_weaknesses,
            created_at, updated_at, last_active_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        self.store.execute(sql, (
            profile.learner_id,
            profile.display_name,
            profile.primary_domain,
            profile.preferred_language,
            profile.preferred_learning_style,
            profile.preferred_explanation_style,
            profile.daily_time_budget_minutes,
            int(profile.current_autonomy_level),
            json.dumps(profile.known_strengths),
            json.dumps(profile.known_weaknesses),
            _iso(profile.created_at),
            _iso(profile.updated_at),
            _iso(profile.last_active_at)
        ))
        return profile

    def get_learner(self, learner_id: str) -> Optional[LearnerProfile]:
        sql = "SELECT * FROM learners WHERE learner_id = ?;"
        row = self.store.fetchone(sql, (learner_id,))
        if not row:
            return None
        return LearnerProfile(
            learner_id=row["learner_id"],
            display_name=row["display_name"],
            primary_domain=row["primary_domain"],
            preferred_language=row["preferred_language"],
            preferred_learning_style=row["preferred_learning_style"],
            preferred_explanation_style=row["preferred_explanation_style"],
            daily_time_budget_minutes=row["daily_time_budget_minutes"],
            current_autonomy_level=AutonomyLevel(row["current_autonomy_level"]),
            known_strengths=json.loads(row["known_strengths"] or "[]"),
            known_weaknesses=json.loads(row["known_weaknesses"] or "[]"),
            created_at=_parse_dt(row["created_at"]) or _utc_now(),
            updated_at=_parse_dt(row["updated_at"]) or _utc_now(),
            last_active_at=_parse_dt(row["last_active_at"]) or _utc_now(),
        )

    def update_learner(self, profile: LearnerProfile) -> LearnerProfile:
        profile.touch()
        sql = """
        UPDATE learners SET
            display_name = ?, primary_domain = ?, preferred_language = ?,
            preferred_learning_style = ?, preferred_explanation_style = ?,
            daily_time_budget_minutes = ?, current_autonomy_level = ?,
            known_strengths = ?, known_weaknesses = ?,
            updated_at = ?, last_active_at = ?
        WHERE learner_id = ?;
        """
        self.store.execute(sql, (
            profile.display_name,
            profile.primary_domain,
            profile.preferred_language,
            profile.preferred_learning_style,
            profile.preferred_explanation_style,
            profile.daily_time_budget_minutes,
            int(profile.current_autonomy_level),
            json.dumps(profile.known_strengths),
            json.dumps(profile.known_weaknesses),
            _iso(profile.updated_at),
            _iso(profile.last_active_at),
            profile.learner_id
        ))
        return profile

    # =========================================================================
    # 2. LEARNING GOALS
    # =========================================================================

    def create_goal(self, goal: LearningGoal) -> LearningGoal:
        sql = """
        INSERT INTO learning_goals (
            goal_id, learner_id, title, target_outcome, deadline, priority,
            target_level, daily_hours, milestones, is_active,
            created_at, updated_at, completed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        self.store.execute(sql, (
            goal.goal_id,
            goal.learner_id,
            goal.title,
            goal.target_outcome,
            _iso(goal.deadline),
            goal.priority,
            goal.target_level,
            goal.daily_hours,
            json.dumps(goal.milestones),
            1 if goal.is_active else 0,
            _iso(goal.created_at),
            _iso(goal.updated_at),
            _iso(goal.completed_at)
        ))
        return goal

    def get_goals(self, learner_id: str, active_only: bool = False) -> List[LearningGoal]:
        if active_only:
            sql = "SELECT * FROM learning_goals WHERE learner_id = ? AND is_active = 1 ORDER BY priority DESC, created_at DESC;"
        else:
            sql = "SELECT * FROM learning_goals WHERE learner_id = ? ORDER BY priority DESC, created_at DESC;"
        rows = self.store.fetchall(sql, (learner_id,))
        goals: List[LearningGoal] = []
        for r in rows:
            goals.append(LearningGoal(
                goal_id=r["goal_id"],
                learner_id=r["learner_id"],
                title=r["title"],
                target_outcome=r["target_outcome"],
                deadline=_parse_dt(r["deadline"]),
                priority=r["priority"],
                target_level=r["target_level"],
                daily_hours=r["daily_hours"],
                milestones=json.loads(r["milestones"] or "[]"),
                is_active=bool(r["is_active"]),
                created_at=_parse_dt(r["created_at"]) or _utc_now(),
                updated_at=_parse_dt(r["updated_at"]) or _utc_now(),
                completed_at=_parse_dt(r["completed_at"]),
            ))
        return goals

    def update_goal(self, goal: LearningGoal) -> LearningGoal:
        goal.updated_at = _utc_now()
        sql = """
        UPDATE learning_goals SET
            title = ?, target_outcome = ?, deadline = ?, priority = ?,
            target_level = ?, daily_hours = ?, milestones = ?,
            is_active = ?, updated_at = ?, completed_at = ?
        WHERE goal_id = ? AND learner_id = ?;
        """
        self.store.execute(sql, (
            goal.title,
            goal.target_outcome,
            _iso(goal.deadline),
            goal.priority,
            goal.target_level,
            goal.daily_hours,
            json.dumps(goal.milestones),
            1 if goal.is_active else 0,
            _iso(goal.updated_at),
            _iso(goal.completed_at),
            goal.goal_id,
            goal.learner_id
        ))
        return goal

    # =========================================================================
    # 3. SUBJECTS, TOPICS & PREREQUISITES
    # =========================================================================

    def create_subject(self, subject: Subject) -> Subject:
        sql = "INSERT OR REPLACE INTO subjects (subject_id, name, domain, description) VALUES (?, ?, ?, ?);"
        self.store.execute(sql, (subject.subject_id, subject.name, subject.domain, subject.description))
        return subject

    def get_subject(self, subject_id: str) -> Optional[Subject]:
        row = self.store.fetchone("SELECT * FROM subjects WHERE subject_id = ?;", (subject_id,))
        if not row:
            return None
        return Subject(
            subject_id=row["subject_id"],
            name=row["name"],
            domain=row["domain"],
            description=row["description"]
        )

    def create_topic(self, topic: Topic) -> Topic:
        with self.store.transaction():
            sql = "INSERT OR REPLACE INTO topics (topic_id, subject_id, name, description, prerequisites) VALUES (?, ?, ?, ?, ?);"
            self.store.execute(sql, (
                topic.topic_id,
                topic.subject_id,
                topic.name,
                topic.description,
                json.dumps(topic.prerequisites)
            ))
            for prereq_id in topic.prerequisites:
                self.store.execute(
                    "INSERT OR IGNORE INTO topic_prerequisites (topic_id, prerequisite_id) VALUES (?, ?);",
                    (topic.topic_id, prereq_id)
                )
        return topic

    def get_topic(self, topic_id: str) -> Optional[Topic]:
        row = self.store.fetchone("SELECT * FROM topics WHERE topic_id = ?;", (topic_id,))
        if not row:
            return None
        return Topic(
            topic_id=row["topic_id"],
            subject_id=row["subject_id"],
            name=row["name"],
            description=row["description"],
            prerequisites=json.loads(row["prerequisites"] or "[]")
        )

    def add_prerequisite(self, topic_id: str, prerequisite_id: str) -> None:
        self.store.execute(
            "INSERT OR IGNORE INTO topic_prerequisites (topic_id, prerequisite_id) VALUES (?, ?);",
            (topic_id, prerequisite_id)
        )

    def get_prerequisites(self, topic_id: str) -> List[str]:
        rows = self.store.fetchall("SELECT prerequisite_id FROM topic_prerequisites WHERE topic_id = ?;", (topic_id,))
        return [r["prerequisite_id"] for r in rows]

    # =========================================================================
    # 4. TOPIC MASTERY (KNOWLEDGE-STATE MEMORY)
    # =========================================================================

    def get_topic_mastery(self, learner_id: str, topic_id: str) -> Optional[TopicMastery]:
        sql = "SELECT * FROM topic_mastery WHERE learner_id = ? AND topic_id = ?;"
        row = self.store.fetchone(sql, (learner_id, topic_id))
        if not row:
            return None
        return TopicMastery(
            learner_id=row["learner_id"],
            topic_id=row["topic_id"],
            subject_id=row["subject_id"],
            name=row["name"],
            mastery_score=row["mastery_score"],
            uncertainty=row["uncertainty"],
            tier=MasteryTier(row["tier"]),
            prerequisites=json.loads(row["prerequisites"] or "[]"),
            stability_factor=row["stability_factor"],
            last_practiced=_parse_dt(row["last_practiced"]),
            successful_recalls=row["successful_recalls"],
            failed_recalls=row["failed_recalls"],
            updated_at=_parse_dt(row["updated_at"]) or _utc_now()
        )

    def list_topic_mastery(self, learner_id: str) -> List[TopicMastery]:
        sql = "SELECT * FROM topic_mastery WHERE learner_id = ? ORDER BY mastery_score DESC;"
        rows = self.store.fetchall(sql, (learner_id,))
        items: List[TopicMastery] = []
        for row in rows:
            items.append(TopicMastery(
                learner_id=row["learner_id"],
                topic_id=row["topic_id"],
                subject_id=row["subject_id"],
                name=row["name"],
                mastery_score=row["mastery_score"],
                uncertainty=row["uncertainty"],
                tier=MasteryTier(row["tier"]),
                prerequisites=json.loads(row["prerequisites"] or "[]"),
                stability_factor=row["stability_factor"],
                last_practiced=_parse_dt(row["last_practiced"]),
                successful_recalls=row["successful_recalls"],
                failed_recalls=row["failed_recalls"],
                updated_at=_parse_dt(row["updated_at"]) or _utc_now()
            ))
        return items

    def update_topic_mastery(self, mastery: TopicMastery) -> TopicMastery:
        mastery.updated_at = _utc_now()
        sql = """
        INSERT OR REPLACE INTO topic_mastery (
            learner_id, topic_id, subject_id, name, mastery_score, uncertainty,
            tier, prerequisites, stability_factor, last_practiced,
            successful_recalls, failed_recalls, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        self.store.execute(sql, (
            mastery.learner_id,
            mastery.topic_id,
            mastery.subject_id,
            mastery.name,
            mastery.mastery_score,
            mastery.uncertainty,
            mastery.tier.value,
            json.dumps(mastery.prerequisites),
            mastery.stability_factor,
            _iso(mastery.last_practiced),
            mastery.successful_recalls,
            mastery.failed_recalls,
            _iso(mastery.updated_at)
        ))
        return mastery

    # =========================================================================
    # 5. KNOWLEDGE GAPS & MISCONCEPTIONS
    # =========================================================================

    def create_knowledge_gap(self, gap: KnowledgeGap) -> KnowledgeGap:
        sql = """
        INSERT INTO knowledge_gaps (
            gap_id, learner_id, concept_id, blocking_topic_id, severity,
            diagnostic_evidence, detected_at, resolved, resolved_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        self.store.execute(sql, (
            gap.gap_id,
            gap.learner_id,
            gap.concept_id,
            gap.blocking_topic_id,
            gap.severity,
            gap.diagnostic_evidence,
            _iso(gap.detected_at),
            1 if gap.resolved else 0,
            _iso(gap.resolved_at)
        ))
        return gap

    def get_active_gaps(self, learner_id: str) -> List[KnowledgeGap]:
        sql = "SELECT * FROM knowledge_gaps WHERE learner_id = ? AND resolved = 0 ORDER BY detected_at DESC;"
        rows = self.store.fetchall(sql, (learner_id,))
        gaps: List[KnowledgeGap] = []
        for r in rows:
            gaps.append(KnowledgeGap(
                gap_id=r["gap_id"],
                learner_id=r["learner_id"],
                concept_id=r["concept_id"],
                blocking_topic_id=r["blocking_topic_id"],
                severity=r["severity"],
                diagnostic_evidence=r["diagnostic_evidence"],
                detected_at=_parse_dt(r["detected_at"]) or _utc_now(),
                resolved=bool(r["resolved"]),
                resolved_at=_parse_dt(r["resolved_at"])
            ))
        return gaps

    def resolve_knowledge_gap(self, learner_id: str, gap_id: str) -> bool:
        now = _iso(_utc_now())
        sql = "UPDATE knowledge_gaps SET resolved = 1, resolved_at = ? WHERE gap_id = ? AND learner_id = ?;"
        cur = self.store.execute(sql, (now, gap_id, learner_id))
        return cur.rowcount > 0

    def record_misconception(self, misc: MisconceptionRecord) -> MisconceptionRecord:
        sql = """
        INSERT INTO misconceptions (
            record_id, learner_id, topic_id, category, description,
            observed_code_snippet, corrective_action_taken, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """
        self.store.execute(sql, (
            misc.record_id,
            misc.learner_id,
            misc.topic_id,
            misc.category.value,
            misc.description,
            misc.observed_code_snippet,
            misc.corrective_action_taken,
            _iso(misc.timestamp)
        ))
        return misc

    def get_misconceptions(self, learner_id: str, topic_id: Optional[str] = None) -> List[MisconceptionRecord]:
        if topic_id:
            sql = "SELECT * FROM misconceptions WHERE learner_id = ? AND topic_id = ? ORDER BY timestamp DESC;"
            rows = self.store.fetchall(sql, (learner_id, topic_id))
        else:
            sql = "SELECT * FROM misconceptions WHERE learner_id = ? ORDER BY timestamp DESC;"
            rows = self.store.fetchall(sql, (learner_id,))
        records: List[MisconceptionRecord] = []
        for r in rows:
            records.append(MisconceptionRecord(
                record_id=r["record_id"],
                learner_id=r["learner_id"],
                topic_id=r["topic_id"],
                category=MisconceptionCategory(r["category"]),
                description=r["description"],
                observed_code_snippet=r["observed_code_snippet"],
                corrective_action_taken=r["corrective_action_taken"],
                timestamp=_parse_dt(r["timestamp"]) or _utc_now()
            ))
        return records

    # =========================================================================
    # 6. ASSESSMENTS & EPISODIC LEARNING
    # =========================================================================

    def record_assessment(self, assessment: AssessmentResult) -> AssessmentResult:
        sql = """
        INSERT INTO assessments (
            assessment_id, learner_id, topic_id, task_id, score,
            prior_mastery, new_mastery, prior_uncertainty, new_uncertainty,
            evaluated_tier, identified_misconceptions, feedback_notes, evaluated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        self.store.execute(sql, (
            assessment.assessment_id,
            assessment.learner_id,
            assessment.topic_id,
            assessment.task_id,
            assessment.score,
            assessment.prior_mastery,
            assessment.new_mastery,
            assessment.prior_uncertainty,
            assessment.new_uncertainty,
            assessment.evaluated_tier.value,
            json.dumps(assessment.identified_misconceptions),
            assessment.feedback_notes,
            _iso(assessment.evaluated_at)
        ))
        return assessment

    def get_assessments(self, learner_id: str, topic_id: Optional[str] = None, limit: int = 10) -> List[AssessmentResult]:
        if topic_id:
            sql = "SELECT * FROM assessments WHERE learner_id = ? AND topic_id = ? ORDER BY evaluated_at DESC LIMIT ?;"
            rows = self.store.fetchall(sql, (learner_id, topic_id, limit))
        else:
            sql = "SELECT * FROM assessments WHERE learner_id = ? ORDER BY evaluated_at DESC LIMIT ?;"
            rows = self.store.fetchall(sql, (learner_id, limit))
        items: List[AssessmentResult] = []
        for r in rows:
            items.append(AssessmentResult(
                assessment_id=r["assessment_id"],
                learner_id=r["learner_id"],
                topic_id=r["topic_id"],
                task_id=r["task_id"],
                score=r["score"],
                prior_mastery=r["prior_mastery"],
                new_mastery=r["new_mastery"],
                prior_uncertainty=r["prior_uncertainty"],
                new_uncertainty=r["new_uncertainty"],
                evaluated_tier=MasteryTier(r["evaluated_tier"]),
                identified_misconceptions=json.loads(r["identified_misconceptions"] or "[]"),
                feedback_notes=r["feedback_notes"],
                evaluated_at=_parse_dt(r["evaluated_at"]) or _utc_now()
            ))
        return items

    def record_learning_session(self, session: LearningSession) -> LearningSession:
        sql = """
        INSERT OR REPLACE INTO learning_sessions (
            session_id, learner_id, goal_id, start_time, end_time,
            duration_minutes, topics_covered, tasks_completed, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        self.store.execute(sql, (
            session.session_id,
            session.learner_id,
            session.goal_id,
            _iso(session.start_time),
            _iso(session.end_time),
            session.duration_minutes,
            json.dumps(session.topics_covered),
            json.dumps(session.tasks_completed),
            session.notes
        ))
        return session

    def get_learning_sessions(self, learner_id: str, limit: int = 10) -> List[LearningSession]:
        sql = "SELECT * FROM learning_sessions WHERE learner_id = ? ORDER BY start_time DESC LIMIT ?;"
        rows = self.store.fetchall(sql, (learner_id, limit))
        sessions: List[LearningSession] = []
        for r in rows:
            sessions.append(LearningSession(
                session_id=r["session_id"],
                learner_id=r["learner_id"],
                goal_id=r["goal_id"],
                start_time=_parse_dt(r["start_time"]) or _utc_now(),
                end_time=_parse_dt(r["end_time"]),
                duration_minutes=r["duration_minutes"],
                topics_covered=json.loads(r["topics_covered"] or "[]"),
                tasks_completed=json.loads(r["tasks_completed"] or "[]"),
                notes=r["notes"] or ""
            ))
        return sessions

    def record_progress_snapshot(self, snapshot: ProgressSnapshot) -> ProgressSnapshot:
        sql = """
        INSERT INTO progress_snapshots (
            snapshot_id, learner_id, timestamp, topics_mastered_count,
            topics_practicing_count, active_gaps_count, average_mastery,
            velocity_topics_per_week
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """
        self.store.execute(sql, (
            snapshot.snapshot_id,
            snapshot.learner_id,
            _iso(snapshot.timestamp),
            snapshot.topics_mastered_count,
            snapshot.topics_practicing_count,
            snapshot.active_gaps_count,
            snapshot.average_mastery,
            snapshot.velocity_topics_per_week
        ))
        return snapshot

    def get_progress_snapshots(self, learner_id: str, limit: int = 10) -> List[ProgressSnapshot]:
        sql = "SELECT * FROM progress_snapshots WHERE learner_id = ? ORDER BY timestamp DESC LIMIT ?;"
        rows = self.store.fetchall(sql, (learner_id, limit))
        items: List[ProgressSnapshot] = []
        for r in rows:
            items.append(ProgressSnapshot(
                snapshot_id=r["snapshot_id"],
                learner_id=r["learner_id"],
                timestamp=_parse_dt(r["timestamp"]) or _utc_now(),
                topics_mastered_count=r["topics_mastered_count"],
                topics_practicing_count=r["topics_practicing_count"],
                active_gaps_count=r["active_gaps_count"],
                average_mastery=r["average_mastery"],
                velocity_topics_per_week=r["velocity_topics_per_week"]
            ))
        return items

    # =========================================================================
    # 7. INTERACTION MEMORY
    # =========================================================================

    def save_interaction_memory(
        self,
        learner_id: str,
        role: str,
        message: str,
        topic_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> str:
        interaction_id = f"int_{uuid.uuid4().hex[:10]}"
        now = _iso(_utc_now())
        sql = """
        INSERT INTO interaction_memory (
            interaction_id, learner_id, session_id, topic_id, role, message, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?);
        """
        self.store.execute(sql, (interaction_id, learner_id, session_id, topic_id, role, message, now))
        return interaction_id

    def get_recent_interactions(self, learner_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM interaction_memory WHERE learner_id = ? ORDER BY timestamp DESC LIMIT ?;"
        rows = self.store.fetchall(sql, (learner_id, limit))
        return [dict(r) for r in reversed(rows)]  # return in chronological order

    # =========================================================================
    # 8. TYPED MEMORY ITEMS (FACTS & INFERENCES WITH PROVENANCE)
    # =========================================================================

    def store_memory_item(self, item: MemoryItem) -> MemoryItem:
        sql = """
        INSERT OR REPLACE INTO memory_items (
            memory_id, learner_id, memory_type, key, content, structured_data,
            source, epistemic_status, importance, confidence, topic_id,
            created_at, updated_at, last_accessed_at, access_count
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        self.store.execute(sql, (
            item.memory_id,
            item.learner_id,
            item.memory_type.value,
            item.key,
            item.content,
            json.dumps(item.structured_data) if item.structured_data else None,
            item.source.value,
            item.epistemic_status.value,
            item.importance,
            item.confidence,
            item.topic_id,
            _iso(item.created_at),
            _iso(item.updated_at),
            _iso(item.last_accessed_at),
            item.access_count
        ))
        return item

    def get_memory_items(
        self,
        learner_id: str,
        memory_type: Optional[MemoryType] = None,
        key: Optional[str] = None,
        min_importance: int = 1
    ) -> List[MemoryItem]:
        conditions = ["learner_id = ?", "importance >= ?"]
        params: List[Any] = [learner_id, min_importance]
        if memory_type:
            conditions.append("memory_type = ?")
            params.append(memory_type.value)
        if key:
            conditions.append("key = ?")
            params.append(key)

        sql = f"SELECT * FROM memory_items WHERE {' AND '.join(conditions)} ORDER BY importance DESC, updated_at DESC;"
        rows = self.store.fetchall(sql, tuple(params))
        items: List[MemoryItem] = []
        for r in rows:
            items.append(MemoryItem(
                memory_id=r["memory_id"],
                learner_id=r["learner_id"],
                memory_type=MemoryType(r["memory_type"]),
                key=r["key"],
                content=r["content"],
                structured_data=json.loads(r["structured_data"]) if r["structured_data"] else None,
                source=MemorySource(r["source"]),
                epistemic_status=EpistemicStatus(r["epistemic_status"]),
                importance=r["importance"],
                confidence=r["confidence"],
                topic_id=r["topic_id"],
                created_at=_parse_dt(r["created_at"]) or _utc_now(),
                updated_at=_parse_dt(r["updated_at"]) or _utc_now(),
                last_accessed_at=_parse_dt(r["last_accessed_at"]),
                access_count=r["access_count"]
            ))
        return items

    def delete_memory_item(self, learner_id: str, memory_id: str) -> bool:
        sql = "DELETE FROM memory_items WHERE memory_id = ? AND learner_id = ?;"
        cur = self.store.execute(sql, (memory_id, learner_id))
        return cur.rowcount > 0
