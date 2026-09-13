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
    LearningStrategy,
    MasteryTier,
    MemorySource,
    MemoryType,
    MilestoneStatus,
    MisconceptionCategory,
    PlanStatus,
    PlanValidationStatus,
    TaskStatus,
    TaskType,
)
from tarkyaan.models.gaps import KnowledgeGap, MisconceptionRecord
from tarkyaan.models.goals import LearningGoal
from tarkyaan.models.learner import LearnerProfile
from tarkyaan.models.learning import LearningResource, LearningSession, ProgressSnapshot
from tarkyaan.models.mastery import Subject, Topic, TopicMastery
from tarkyaan.models.planning import (
    LearningPlan,
    LearningTask,
    Milestone,
    PlanExplanation,
    StudyPhase,
)
from tarkyaan.models.research import ResearchHistoryEntry, ResourceProvenance


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

    save_learner_profile = create_learner

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

    def get_goal(self, goal_id: str) -> Optional[LearningGoal]:
        row = self.store.fetchone("SELECT * FROM learning_goals WHERE goal_id = ?;", (goal_id,))
        if not row:
            return None
        return LearningGoal(
            goal_id=row["goal_id"],
            learner_id=row["learner_id"],
            title=row["title"],
            target_outcome=row["target_outcome"],
            deadline=_parse_dt(row["deadline"]),
            priority=row["priority"],
            target_level=row["target_level"],
            daily_hours=row["daily_hours"],
            milestones=json.loads(row["milestones"] or "[]"),
            is_active=bool(row["is_active"]),
            created_at=_parse_dt(row["created_at"]) or _utc_now(),
            updated_at=_parse_dt(row["updated_at"]) or _utc_now(),
            completed_at=_parse_dt(row["completed_at"]),
        )

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

    def get_all_topic_mastery(self, learner_id: str) -> List[TopicMastery]:
        return self.list_topic_mastery(learner_id)

    def update_topic_mastery(self, mastery: TopicMastery) -> TopicMastery:
        mastery.updated_at = _utc_now()
        subject_id = mastery.subject_id or "general"
        self.store.execute(
            "INSERT OR IGNORE INTO subjects (subject_id, name, domain) VALUES (?, ?, ?);",
            (subject_id, subject_id.capitalize(), "general")
        )
        self.store.execute(
            "INSERT OR IGNORE INTO topics (topic_id, subject_id, name, prerequisites) VALUES (?, ?, ?, ?);",
            (mastery.topic_id, subject_id, mastery.name or mastery.topic_id, json.dumps(mastery.prerequisites))
        )
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

    def get_knowledge_gaps(self, learner_id: str, active_only: bool = True) -> List[KnowledgeGap]:
        if active_only:
            return self.get_active_gaps(learner_id)
        sql = "SELECT * FROM knowledge_gaps WHERE learner_id = ? ORDER BY detected_at DESC;"
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
            duration_minutes, topics_covered, tasks_completed, notes,
            plan_id, task_id, concept_id, objective, status, current_stage,
            stage_history, questions_asked, answers_received, hints_used,
            evidence_collected, resources_used, mastery_changes, summary,
            next_recommended_task_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
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
            session.notes,
            session.plan_id,
            session.task_id,
            session.concept_id,
            session.objective,
            session.status.value if hasattr(session.status, "value") else str(session.status),
            session.current_stage.value if hasattr(session.current_stage, "value") else str(session.current_stage),
            json.dumps([h.model_dump(mode="json") if hasattr(h, "model_dump") else h for h in session.stage_history]),
            json.dumps([q.model_dump(mode="json") if hasattr(q, "model_dump") else q for q in session.questions_asked]),
            json.dumps([a.model_dump(mode="json") if hasattr(a, "model_dump") else a for a in session.answers_received]),
            session.hints_used,
            json.dumps(session.evidence_collected),
            json.dumps(session.resources_used),
            json.dumps(session.mastery_changes),
            session.summary.model_dump_json() if session.summary else None,
            session.next_recommended_task_id
        ))
        return session

    def _row_to_session(self, r: Any) -> LearningSession:
        from tarkyaan.models.enums import SessionStage, SessionStatus
        from tarkyaan.models.practice import AnswerEvaluation, PracticeQuestion
        from tarkyaan.models.session import SessionSummary, StageTransitionRecord

        keys = r.keys() if hasattr(r, "keys") else []
        plan_id = r["plan_id"] if "plan_id" in keys else None
        task_id = r["task_id"] if "task_id" in keys else None
        concept_id = r["concept_id"] if "concept_id" in keys else None
        objective = r["objective"] if "objective" in keys and r["objective"] else ""
        raw_status = r["status"] if "status" in keys and r["status"] else "created"
        try:
            status = SessionStatus(raw_status)
        except Exception:
            status = SessionStatus.CREATED

        raw_stage = r["current_stage"] if "current_stage" in keys and r["current_stage"] else "initialize"
        try:
            current_stage = SessionStage(raw_stage)
        except Exception:
            current_stage = SessionStage.INITIALIZE

        stage_history: List[StageTransitionRecord] = []
        if "stage_history" in keys and r["stage_history"]:
            try:
                for item in json.loads(r["stage_history"]):
                    stage_history.append(StageTransitionRecord.model_validate(item))
            except Exception:
                pass

        questions_asked: List[PracticeQuestion] = []
        if "questions_asked" in keys and r["questions_asked"]:
            try:
                for item in json.loads(r["questions_asked"]):
                    questions_asked.append(PracticeQuestion.model_validate(item))
            except Exception:
                pass

        answers_received: List[AnswerEvaluation] = []
        if "answers_received" in keys and r["answers_received"]:
            try:
                for item in json.loads(r["answers_received"]):
                    answers_received.append(AnswerEvaluation.model_validate(item))
            except Exception:
                pass

        hints_used = r["hints_used"] if "hints_used" in keys and r["hints_used"] is not None else 0
        evidence_collected = json.loads(r["evidence_collected"] or "[]") if "evidence_collected" in keys and r["evidence_collected"] else []
        resources_used = json.loads(r["resources_used"] or "[]") if "resources_used" in keys and r["resources_used"] else []
        mastery_changes = json.loads(r["mastery_changes"] or "{}") if "mastery_changes" in keys and r["mastery_changes"] else {}

        summary: Optional[SessionSummary] = None
        if "summary" in keys and r["summary"]:
            try:
                summary = SessionSummary.model_validate_json(r["summary"])
            except Exception:
                pass

        next_rec = r["next_recommended_task_id"] if "next_recommended_task_id" in keys else None

        return LearningSession(
            session_id=r["session_id"],
            learner_id=r["learner_id"],
            goal_id=r["goal_id"],
            plan_id=plan_id,
            task_id=task_id,
            concept_id=concept_id,
            objective=objective,
            status=status,
            current_stage=current_stage,
            stage_history=stage_history,
            questions_asked=questions_asked,
            answers_received=answers_received,
            hints_used=hints_used,
            evidence_collected=evidence_collected,
            resources_used=resources_used,
            mastery_changes=mastery_changes,
            summary=summary,
            next_recommended_task_id=next_rec,
            start_time=_parse_dt(r["start_time"]) or _utc_now(),
            end_time=_parse_dt(r["end_time"]),
            duration_minutes=r["duration_minutes"],
            topics_covered=json.loads(r["topics_covered"] or "[]"),
            tasks_completed=json.loads(r["tasks_completed"] or "[]"),
            notes=r["notes"] or ""
        )

    def get_learning_session(self, session_id: str) -> Optional[LearningSession]:
        sql = "SELECT * FROM learning_sessions WHERE session_id = ?;"
        row = self.store.fetchone(sql, (session_id,))
        if not row:
            return None
        return self._row_to_session(row)

    def get_learning_sessions(self, learner_id: str, limit: int = 10) -> List[LearningSession]:
        sql = "SELECT * FROM learning_sessions WHERE learner_id = ? ORDER BY start_time DESC LIMIT ?;"
        rows = self.store.fetchall(sql, (learner_id, limit))
        return [self._row_to_session(r) for r in rows]

    def record_session_interaction(
        self,
        session_id: str,
        speaker: str,
        stage: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        interaction_id: Optional[str] = None
    ) -> str:
        i_id = interaction_id or f"turn_{uuid.uuid4().hex[:8]}"
        now = _iso(_utc_now())
        count_row = self.store.fetchone(
            "SELECT COUNT(*) as cnt FROM session_interactions WHERE session_id = ?;",
            (session_id,)
        )
        turn_index = count_row["cnt"] if count_row else 0
        meta_json = json.dumps(metadata or {})

        sql = """
        INSERT INTO session_interactions (
            interaction_id, session_id, turn_index, speaker, stage, content, metadata, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """
        self.store.execute(sql, (i_id, session_id, turn_index, speaker, stage, content, meta_json, now))
        return i_id

    def get_session_interactions(self, session_id: str) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM session_interactions WHERE session_id = ? ORDER BY turn_index ASC;"
        rows = self.store.fetchall(sql, (session_id,))
        results: List[Dict[str, Any]] = []
        for r in rows:
            results.append({
                "interaction_id": r["interaction_id"],
                "session_id": r["session_id"],
                "turn_index": r["turn_index"],
                "speaker": r["speaker"],
                "stage": r["stage"],
                "content": r["content"],
                "metadata": json.loads(r["metadata"] or "{}"),
                "timestamp": r["timestamp"]
            })
        return results

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

    # =========================================================================
    # 9. LEARNING PLANS & ROADMAP PERSISTENCE
    # =========================================================================

    def save_learning_plan(self, plan: LearningPlan) -> LearningPlan:
        """
        Thread-safely persist a LearningPlan, its study phases, milestones, and tasks.
        """
        plan.updated_at = _utc_now()
        explanation_json = plan.explanation.model_dump_json() if plan.explanation else "{}"
        provenance_json = json.dumps(plan.provenance)
        dependencies_json = json.dumps(plan.dependencies)
        assumptions_json = json.dumps(plan.assumptions)
        outcomes_json = json.dumps(plan.expected_outcomes)

        with self.store.transaction():
            # 1. Insert or update plan header
            sql_plan = """
            INSERT OR REPLACE INTO learning_plans (
                plan_id, learner_id, goal_id, title, description, objective,
                status, strategy, version, parent_plan_id, revision_reason,
                total_estimated_hours, estimated_total_minutes, priority,
                dependencies, assumptions, expected_outcomes, validation_status,
                provenance, explanation, start_date, target_date, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """
            self.store.execute(sql_plan, (
                plan.plan_id,
                plan.learner_id,
                plan.goal_id,
                plan.title,
                plan.description,
                plan.objective,
                plan.status.value,
                plan.strategy.value,
                plan.version,
                plan.parent_plan_id,
                plan.revision_reason,
                plan.total_estimated_hours,
                plan.estimated_total_minutes,
                plan.priority,
                dependencies_json,
                assumptions_json,
                outcomes_json,
                plan.validation_status.value,
                provenance_json,
                explanation_json,
                _iso(plan.start_date),
                _iso(plan.target_date),
                _iso(plan.created_at),
                _iso(plan.updated_at)
            ))

            # 2. Re-create study phases for this plan
            self.store.execute("DELETE FROM study_phases WHERE plan_id = ?;", (plan.plan_id,))
            for phase in plan.phases:
                phase.plan_id = plan.plan_id
                sql_phase = """
                INSERT INTO study_phases (
                    phase_id, plan_id, name, title, objective, concepts,
                    prerequisite_phase_ids, task_ids, estimated_minutes,
                    phase_order, completion_criteria, status, is_completed
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """
                self.store.execute(sql_phase, (
                    phase.phase_id,
                    phase.plan_id,
                    phase.name or phase.title,
                    phase.title or phase.name,
                    phase.objective,
                    json.dumps(phase.concepts),
                    json.dumps(phase.prerequisite_phase_ids),
                    json.dumps(phase.task_ids),
                    phase.estimated_minutes,
                    phase.phase_order,
                    json.dumps(phase.completion_criteria),
                    phase.status,
                    1 if phase.is_completed else 0
                ))

            # 3. Re-create plan milestones
            self.store.execute("DELETE FROM plan_milestones WHERE plan_id = ?;", (plan.plan_id,))
            for ms in plan.milestones:
                ms.plan_id = plan.plan_id
                sql_ms = """
                INSERT INTO plan_milestones (
                    milestone_id, plan_id, title, objective, required_task_ids,
                    required_concepts, completion_criteria, status, milestone_order,
                    target_date, achieved_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """
                self.store.execute(sql_ms, (
                    ms.milestone_id,
                    ms.plan_id,
                    ms.title,
                    ms.objective,
                    json.dumps(ms.required_task_ids),
                    json.dumps(ms.required_concepts),
                    json.dumps(ms.completion_criteria),
                    ms.status.value,
                    ms.milestone_order,
                    _iso(ms.target_date),
                    _iso(ms.achieved_at)
                ))

            # 4. Save tasks
            for task in plan.tasks:
                task.plan_id = plan.plan_id
                task.learner_id = plan.learner_id
                sql_task = """
                INSERT OR REPLACE INTO learning_tasks (
                    task_id, plan_id, phase_id, learner_id, goal_id, topic_id,
                    concept_id, title, description, task_type, objective,
                    difficulty, estimated_minutes, priority, prerequisite_task_ids,
                    prerequisite_concept_ids, expected_evidence, completion_criteria,
                    mastery_target, task_order, status, rationale, resource_ids,
                    parameters, completed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """
                self.store.execute(sql_task, (
                    task.task_id,
                    task.plan_id,
                    task.phase_id,
                    task.learner_id,
                    task.goal_id or plan.goal_id,
                    task.topic_id or task.concept_id,
                    task.concept_id or task.topic_id,
                    task.title,
                    task.description,
                    task.task_type.value,
                    task.objective,
                    task.difficulty,
                    task.estimated_minutes,
                    task.priority,
                    json.dumps(task.prerequisite_task_ids),
                    json.dumps(task.prerequisite_concept_ids),
                    task.expected_evidence,
                    json.dumps(task.completion_criteria),
                    task.mastery_target,
                    task.task_order,
                    task.status.value,
                    task.rationale,
                    json.dumps(task.resource_ids),
                    json.dumps(task.parameters),
                    _iso(task.completed_at)
                ))

        return plan

    def get_learning_plan(self, plan_id: str) -> Optional[LearningPlan]:
        """
        Reassemble a complete LearningPlan from normalized tables.
        """
        row = self.store.fetchone("SELECT * FROM learning_plans WHERE plan_id = ?;", (plan_id,))
        if not row:
            return None

        # Fetch tasks
        t_rows = self.store.fetchall("SELECT * FROM learning_tasks WHERE plan_id = ? ORDER BY task_order ASC;", (plan_id,))
        tasks: List[LearningTask] = []
        for tr in t_rows:
            tasks.append(LearningTask(
                task_id=tr["task_id"],
                plan_id=tr["plan_id"],
                phase_id=tr["phase_id"],
                learner_id=tr["learner_id"],
                goal_id=tr["goal_id"],
                topic_id=tr["topic_id"] or tr["concept_id"],
                concept_id=tr["concept_id"] or tr["topic_id"],
                title=tr["title"],
                description=tr["description"] or "",
                task_type=TaskType(tr["task_type"]) if tr["task_type"] in TaskType.__members__.values() else TaskType.PRACTICE,
                objective=tr["objective"] or "",
                difficulty=tr["difficulty"] or 2,
                estimated_minutes=tr["estimated_minutes"] or 30,
                priority=tr["priority"] or 1.0,
                prerequisite_task_ids=json.loads(tr["prerequisite_task_ids"] or "[]"),
                prerequisite_concept_ids=json.loads(tr["prerequisite_concept_ids"] or "[]"),
                expected_evidence=tr["expected_evidence"] or "",
                completion_criteria=json.loads(tr["completion_criteria"] or "[]"),
                mastery_target=tr["mastery_target"] or 0.70,
                task_order=tr["task_order"] or 1,
                status=TaskStatus(tr["status"]) if tr["status"] in TaskStatus.__members__.values() else TaskStatus.PENDING,
                rationale=tr["rationale"] or "",
                resource_ids=json.loads(tr["resource_ids"] or "[]"),
                parameters=json.loads(tr["parameters"] or "{}"),
                completed_at=_parse_dt(tr["completed_at"])
            ))

        task_map = {t.task_id: t for t in tasks}

        # Fetch phases
        p_rows = self.store.fetchall("SELECT * FROM study_phases WHERE plan_id = ? ORDER BY phase_order ASC;", (plan_id,))
        phases: List[StudyPhase] = []
        for pr in p_rows:
            t_ids = json.loads(pr["task_ids"] or "[]")
            phase_tasks = [task_map[tid] for tid in t_ids if tid in task_map]
            # Also catch tasks matching phase_id
            if not phase_tasks:
                phase_tasks = [t for t in tasks if t.phase_id == pr["phase_id"]]
            phases.append(StudyPhase(
                phase_id=pr["phase_id"],
                plan_id=pr["plan_id"],
                name=pr["name"],
                title=pr["title"],
                objective=pr["objective"] or "",
                concepts=json.loads(pr["concepts"] or "[]"),
                prerequisite_phase_ids=json.loads(pr["prerequisite_phase_ids"] or "[]"),
                task_ids=t_ids or [t.task_id for t in phase_tasks],
                tasks=phase_tasks,
                estimated_minutes=pr["estimated_minutes"] or 0,
                phase_order=pr["phase_order"] or 1,
                completion_criteria=json.loads(pr["completion_criteria"] or "[]"),
                status=pr["status"] or "pending",
                is_completed=bool(pr["is_completed"])
            ))

        # Fetch milestones
        m_rows = self.store.fetchall("SELECT * FROM plan_milestones WHERE plan_id = ? ORDER BY milestone_order ASC;", (plan_id,))
        milestones: List[Milestone] = []
        for mr in m_rows:
            milestones.append(Milestone(
                milestone_id=mr["milestone_id"],
                plan_id=mr["plan_id"],
                title=mr["title"],
                objective=mr["objective"] or "",
                required_task_ids=json.loads(mr["required_task_ids"] or "[]"),
                required_concepts=json.loads(mr["required_concepts"] or "[]"),
                completion_criteria=json.loads(mr["completion_criteria"] or "[]"),
                status=MilestoneStatus(mr["status"]) if mr["status"] in MilestoneStatus.__members__.values() else MilestoneStatus.PENDING,
                milestone_order=mr["milestone_order"] or 1,
                target_date=_parse_dt(mr["target_date"]),
                achieved_at=_parse_dt(mr["achieved_at"])
            ))

        # Deserialize explanation
        explanation = None
        if row["explanation"]:
            try:
                exp_dict = json.loads(row["explanation"])
                if exp_dict:
                    explanation = PlanExplanation(**exp_dict)
            except Exception:
                pass

        return LearningPlan(
            plan_id=row["plan_id"],
            learner_id=row["learner_id"],
            goal_id=row["goal_id"],
            title=row["title"],
            description=row["description"] or "",
            objective=row["objective"] or "",
            status=PlanStatus(row["status"]) if row["status"] in PlanStatus.__members__.values() else PlanStatus.PROPOSED,
            strategy=LearningStrategy(row["strategy"]) if row["strategy"] in LearningStrategy.__members__.values() else LearningStrategy.BALANCED,
            version=row["version"] or 1,
            parent_plan_id=row["parent_plan_id"],
            revision_reason=row["revision_reason"],
            phases=phases,
            milestones=milestones,
            tasks=tasks,
            dependencies=json.loads(row["dependencies"] or "{}"),
            assumptions=json.loads(row["assumptions"] or "[]"),
            expected_outcomes=json.loads(row["expected_outcomes"] or "[]"),
            validation_status=PlanValidationStatus(row["validation_status"]) if row["validation_status"] in PlanValidationStatus.__members__.values() else PlanValidationStatus.VALID,
            provenance=json.loads(row["provenance"] or "{}"),
            explanation=explanation,
            total_estimated_hours=row["total_estimated_hours"] or 0.0,
            estimated_total_minutes=row["estimated_total_minutes"] or 0,
            priority=row["priority"] or 3,
            start_date=_parse_dt(row["start_date"]),
            target_date=_parse_dt(row["target_date"]),
            created_at=_parse_dt(row["created_at"]) or _utc_now(),
            updated_at=_parse_dt(row["updated_at"]) or _utc_now()
        )

    def get_active_learning_plan(self, learner_id: str) -> Optional[LearningPlan]:
        """Fetch the current active (or most recent proposed/active) plan for a learner."""
        sql = """
        SELECT plan_id FROM learning_plans
        WHERE learner_id = ? AND status IN ('active', 'proposed')
        ORDER BY updated_at DESC LIMIT 1;
        """
        row = self.store.fetchone(sql, (learner_id,))
        if not row:
            return None
        return self.get_learning_plan(row["plan_id"])

    def list_learning_plans(self, learner_id: str) -> List[LearningPlan]:
        """Return all historical and active plans for a learner."""
        sql = "SELECT plan_id FROM learning_plans WHERE learner_id = ? ORDER BY version DESC, updated_at DESC;"
        rows = self.store.fetchall(sql, (learner_id,))
        plans: List[LearningPlan] = []
        for r in rows:
            p = self.get_learning_plan(r["plan_id"])
            if p:
                plans.append(p)
        return plans

    def update_plan_status(self, plan_id: str, status: PlanStatus) -> None:
        """Update plan status flag."""
        now = _iso(_utc_now())
        sql = "UPDATE learning_plans SET status = ?, updated_at = ? WHERE plan_id = ?;"
        self.store.execute(sql, (status.value, now, plan_id))

    def archive_plan_version(self, plan: LearningPlan, change_reason: str) -> None:
        """Store immutable snapshot of plan version in audit trail."""
        version_id = f"pv_{uuid.uuid4().hex[:8]}"
        now = _iso(_utc_now())
        snapshot_json = plan.model_dump_json()
        sql = """
        INSERT INTO plan_versions (
            version_id, plan_id, learner_id, version, status, change_reason, snapshot_json, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """
        self.store.execute(sql, (
            version_id, plan.plan_id, plan.learner_id, plan.version,
            plan.status.value, change_reason, snapshot_json, now
        ))

    def get_plan_version_history(self, plan_id: str) -> List[Dict[str, Any]]:
        """Return full version change history for a plan."""
        sql = "SELECT * FROM plan_versions WHERE plan_id = ? ORDER BY version ASC, created_at ASC;"
        rows = self.store.fetchall(sql, (plan_id,))
        return [dict(r) for r in rows]

    # =========================================================================
    # PHASE 4: EDUCATIONAL RESOURCES & RESEARCH PERSISTENCE
    # =========================================================================

    def save_resource(self, res: LearningResource) -> None:
        """Persist or update an evaluated educational resource."""
        sql = """
        INSERT OR REPLACE INTO resources (
            resource_id, topic_id, title, url, resource_type, domain, provider,
            author, description, concept_ids, task_ids, difficulty, language,
            duration_minutes, published_at, updated_at, relevance_score, authority_score,
            quality_score, learner_fit_score, freshness_score, usefulness_score,
            overall_score, confidence, provenance, evaluation_notes, recommended_order,
            discovered_at, last_verified_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        prov_json = res.provenance.model_dump_json() if res.provenance else "{}"
        self.store.execute(sql, (
            res.resource_id,
            res.topic_id or (res.concept_ids[0] if res.concept_ids else ""),
            res.title,
            res.url,
            res.resource_type,
            res.domain,
            res.provider,
            res.author,
            res.description,
            json.dumps(res.concept_ids),
            json.dumps(res.task_ids),
            res.difficulty,
            res.language,
            res.duration_minutes,
            _iso(res.published_at),
            _iso(res.updated_at),
            res.relevance_score,
            res.authority_score,
            res.quality_score,
            res.learner_fit_score,
            res.freshness_score,
            res.usefulness_score,
            res.overall_score,
            res.confidence,
            prov_json,
            json.dumps(res.evaluation_notes),
            res.recommended_order,
            _iso(res.discovered_at),
            _iso(res.last_verified_at)
        ))

    def get_resource(self, resource_id: str) -> Optional[LearningResource]:
        """Fetch a single resource by its unique identifier."""
        sql = "SELECT * FROM resources WHERE resource_id = ?;"
        row = self.store.fetchone(sql, (resource_id,))
        if not row:
            return None
        return self._row_to_resource(row)

    def list_resources_for_task(self, task_id: str) -> List[LearningResource]:
        """Fetch all resources attached to a specific learning task."""
        sql = "SELECT * FROM resources WHERE task_ids LIKE ? ORDER BY overall_score DESC;"
        pattern = f'%"{task_id}"%'
        rows = self.store.fetchall(sql, (pattern,))
        return [self._row_to_resource(r) for r in rows]

    def list_resources_for_concept(self, concept_id: str) -> List[LearningResource]:
        """Fetch all resources mapped to a specific concept."""
        sql = "SELECT * FROM resources WHERE topic_id = ? OR concept_ids LIKE ? ORDER BY overall_score DESC;"
        pattern = f'%"{concept_id}"%'
        rows = self.store.fetchall(sql, (concept_id, pattern))
        return [self._row_to_resource(r) for r in rows]

    def save_research_history(self, entry: ResearchHistoryEntry) -> None:
        """Audit log of an autonomous research run."""
        sql = """
        INSERT OR REPLACE INTO research_history (
            history_id, learner_id, task_id, concept_id, query, provider,
            status, discovered_count, selected_count, selected_resource_ids, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """
        self.store.execute(sql, (
            entry.history_id,
            entry.learner_id,
            entry.task_id,
            entry.concept_id,
            entry.query,
            entry.provider,
            entry.status,
            entry.discovered_count,
            entry.selected_count,
            json.dumps(entry.selected_resource_ids),
            _iso(entry.timestamp)
        ))

    def get_research_history(self, learner_id: str, limit: int = 20) -> List[ResearchHistoryEntry]:
        """Retrieve recent research runs for a learner."""
        sql = "SELECT * FROM research_history WHERE learner_id = ? ORDER BY timestamp DESC LIMIT ?;"
        rows = self.store.fetchall(sql, (learner_id, limit))
        entries: List[ResearchHistoryEntry] = []
        for r in rows:
            entries.append(ResearchHistoryEntry(
                history_id=r["history_id"],
                learner_id=r["learner_id"],
                task_id=r["task_id"],
                concept_id=r["concept_id"],
                query=r["query"],
                provider=r["provider"],
                status=r["status"],
                discovered_count=r["discovered_count"],
                selected_count=r["selected_count"],
                selected_resource_ids=json.loads(r["selected_resource_ids"] or "[]"),
                timestamp=_parse_dt(r["timestamp"]) or _utc_now()
            ))
        return entries

    def _row_to_resource(self, r: Any) -> LearningResource:
        """Convert a database row into a validated LearningResource model."""
        prov_data = json.loads(r["provenance"] or "{}") if "provenance" in r.keys() else {}
        prov = ResourceProvenance(**prov_data) if prov_data else None

        return LearningResource(
            resource_id=r["resource_id"],
            title=r["title"],
            url=r["url"],
            resource_type=r["resource_type"],
            domain=r["domain"] if "domain" in r.keys() and r["domain"] else "",
            provider=r["provider"] if "provider" in r.keys() and r["provider"] else "mock",
            author=r["author"] if "author" in r.keys() else None,
            description=r["description"] if "description" in r.keys() and r["description"] else "",
            topic_id=r["topic_id"] if "topic_id" in r.keys() and r["topic_id"] else "",
            concept_ids=json.loads(r["concept_ids"] or "[]") if "concept_ids" in r.keys() and r["concept_ids"] else [],
            task_ids=json.loads(r["task_ids"] or "[]") if "task_ids" in r.keys() and r["task_ids"] else [],
            difficulty=r["difficulty"] if "difficulty" in r.keys() and r["difficulty"] else 2,
            language=r["language"] if "language" in r.keys() and r["language"] else "en",
            duration_minutes=r["duration_minutes"] if "duration_minutes" in r.keys() else None,
            published_at=_parse_dt(r["published_at"]) if "published_at" in r.keys() else None,
            updated_at=_parse_dt(r["updated_at"]) if "updated_at" in r.keys() else None,
            relevance_score=r["relevance_score"] if "relevance_score" in r.keys() else 0.5,
            authority_score=r["authority_score"] if "authority_score" in r.keys() else 0.5,
            quality_score=r["quality_score"] if "quality_score" in r.keys() else 0.5,
            learner_fit_score=r["learner_fit_score"] if "learner_fit_score" in r.keys() else 0.5,
            freshness_score=r["freshness_score"] if "freshness_score" in r.keys() else 0.5,
            usefulness_score=r["usefulness_score"] if "usefulness_score" in r.keys() else 0.5,
            overall_score=r["overall_score"] if "overall_score" in r.keys() else 0.5,
            confidence=r["confidence"] if "confidence" in r.keys() else 0.7,
            provenance=prov,
            evaluation_notes=json.loads(r["evaluation_notes"] or "[]") if "evaluation_notes" in r.keys() and r["evaluation_notes"] else [],
            recommended_order=r["recommended_order"] if "recommended_order" in r.keys() else 1,
            discovered_at=(_parse_dt(r["discovered_at"]) if "discovered_at" in r.keys() and r["discovered_at"] else None) or _utc_now(),
            last_verified_at=_parse_dt(r["last_verified_at"]) if "last_verified_at" in r.keys() else None,
        )

