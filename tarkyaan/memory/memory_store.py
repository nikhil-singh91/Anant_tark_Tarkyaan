"""
Tarkyaan Persistent SQLite Storage Engine.
Provides schema creation, thread-safe connection pooling, foreign keys,
and transactional data integrity for Tarkyaan's independent memory.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class TarkyaanMemoryStore:
    """
    SQLite persistent storage engine for Tarkyaan.
    Completely independent of NOVA.
    """

    def __init__(self, db_path: str | Path = ":memory:") -> None:
        """
        Initialize the database store.
        :param db_path: Path to the SQLite database file, or ':memory:' for transient storage.
        """
        self.db_path = str(db_path)
        self._lock = threading.RLock()
        self._conn: Optional[sqlite3.Connection] = None

        if self.db_path != ":memory:":
            p = Path(self.db_path)
            p.parent.mkdir(parents=True, exist_ok=True)

        self._initialize_database()

    def get_connection(self) -> sqlite3.Connection:
        """Get or initialize the thread-safe connection."""
        with self._lock:
            if self._conn is None:
                self._conn = sqlite3.connect(
                    self.db_path,
                    check_same_thread=False,
                    timeout=30.0,
                    isolation_level=None  # autocommit by default unless explicit transaction
                )
                self._conn.row_factory = sqlite3.Row
                self._conn.execute("PRAGMA foreign_keys = ON;")
                if self.db_path != ":memory:":
                    self._conn.execute("PRAGMA journal_mode = WAL;")
                    self._conn.execute("PRAGMA synchronous = NORMAL;")
            return self._conn

    def close(self) -> None:
        """Close the database connection safely."""
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None

    def execute(self, sql: str, params: Tuple[Any, ...] | Dict[str, Any] = ()) -> sqlite3.Cursor:
        """Thread-safely execute a SQL statement."""
        with self._lock:
            conn = self.get_connection()
            return conn.execute(sql, params)

    def executemany(self, sql: str, params_seq: List[Tuple[Any, ...]]) -> sqlite3.Cursor:
        """Thread-safely execute batch SQL statements."""
        with self._lock:
            conn = self.get_connection()
            return conn.executemany(sql, params_seq)

    def fetchone(self, sql: str, params: Tuple[Any, ...] | Dict[str, Any] = ()) -> Optional[sqlite3.Row]:
        """Execute and fetch a single row."""
        with self._lock:
            cur = self.execute(sql, params)
            return cur.fetchone()

    def fetchall(self, sql: str, params: Tuple[Any, ...] | Dict[str, Any] = ()) -> List[sqlite3.Row]:
        """Execute and fetch all matching rows."""
        with self._lock:
            cur = self.execute(sql, params)
            return cur.fetchall()

    def transaction(self):
        """Context manager for explicit atomic transaction."""
        return _TransactionContext(self)

    def _initialize_database(self) -> None:
        """Create all tables, constraints, and indexes if they do not exist."""
        schema_sql = """
        -- 1. Learners
        CREATE TABLE IF NOT EXISTS learners (
            learner_id TEXT PRIMARY KEY,
            display_name TEXT NOT NULL,
            primary_domain TEXT NOT NULL,
            preferred_language TEXT NOT NULL,
            preferred_learning_style TEXT NOT NULL,
            preferred_explanation_style TEXT NOT NULL,
            daily_time_budget_minutes INTEGER NOT NULL,
            current_autonomy_level INTEGER NOT NULL,
            known_strengths TEXT NOT NULL DEFAULT '[]',
            known_weaknesses TEXT NOT NULL DEFAULT '[]',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            last_active_at TEXT NOT NULL
        );

        -- 2. Learning Goals
        CREATE TABLE IF NOT EXISTS learning_goals (
            goal_id TEXT PRIMARY KEY,
            learner_id TEXT NOT NULL REFERENCES learners(learner_id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            target_outcome TEXT NOT NULL,
            deadline TEXT,
            priority INTEGER NOT NULL DEFAULT 3,
            target_level TEXT NOT NULL DEFAULT 'competent',
            daily_hours REAL NOT NULL DEFAULT 2.0,
            milestones TEXT NOT NULL DEFAULT '[]',
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            completed_at TEXT
        );

        -- 3. Subjects
        CREATE TABLE IF NOT EXISTS subjects (
            subject_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            domain TEXT NOT NULL,
            description TEXT
        );

        -- 4. Topics
        CREATE TABLE IF NOT EXISTS topics (
            topic_id TEXT PRIMARY KEY,
            subject_id TEXT NOT NULL REFERENCES subjects(subject_id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            description TEXT,
            prerequisites TEXT NOT NULL DEFAULT '[]'
        );

        -- 5. Topic Prerequisites DAG
        CREATE TABLE IF NOT EXISTS topic_prerequisites (
            topic_id TEXT NOT NULL REFERENCES topics(topic_id) ON DELETE CASCADE,
            prerequisite_id TEXT NOT NULL REFERENCES topics(topic_id) ON DELETE CASCADE,
            PRIMARY KEY (topic_id, prerequisite_id)
        );

        -- 6. Topic Mastery (Per-learner state)
        CREATE TABLE IF NOT EXISTS topic_mastery (
            learner_id TEXT NOT NULL REFERENCES learners(learner_id) ON DELETE CASCADE,
            topic_id TEXT NOT NULL REFERENCES topics(topic_id) ON DELETE CASCADE,
            subject_id TEXT NOT NULL DEFAULT 'general',
            name TEXT NOT NULL,
            mastery_score REAL NOT NULL,
            uncertainty REAL NOT NULL,
            tier TEXT NOT NULL,
            prerequisites TEXT NOT NULL DEFAULT '[]',
            stability_factor REAL NOT NULL DEFAULT 14.0,
            last_practiced TEXT,
            successful_recalls INTEGER NOT NULL DEFAULT 0,
            failed_recalls INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (learner_id, topic_id)
        );

        -- 7. Knowledge Gaps
        CREATE TABLE IF NOT EXISTS knowledge_gaps (
            gap_id TEXT PRIMARY KEY,
            learner_id TEXT NOT NULL REFERENCES learners(learner_id) ON DELETE CASCADE,
            concept_id TEXT NOT NULL,
            blocking_topic_id TEXT NOT NULL,
            severity TEXT NOT NULL,
            diagnostic_evidence TEXT NOT NULL,
            detected_at TEXT NOT NULL,
            resolved INTEGER NOT NULL DEFAULT 0,
            resolved_at TEXT
        );

        -- 8. Misconceptions
        CREATE TABLE IF NOT EXISTS misconceptions (
            record_id TEXT PRIMARY KEY,
            learner_id TEXT NOT NULL REFERENCES learners(learner_id) ON DELETE CASCADE,
            topic_id TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            observed_code_snippet TEXT,
            corrective_action_taken TEXT NOT NULL DEFAULT '',
            timestamp TEXT NOT NULL
        );

        -- 9. Assessments
        CREATE TABLE IF NOT EXISTS assessments (
            assessment_id TEXT PRIMARY KEY,
            learner_id TEXT NOT NULL REFERENCES learners(learner_id) ON DELETE CASCADE,
            topic_id TEXT NOT NULL,
            task_id TEXT,
            score REAL NOT NULL,
            prior_mastery REAL NOT NULL,
            new_mastery REAL NOT NULL,
            prior_uncertainty REAL NOT NULL,
            new_uncertainty REAL NOT NULL,
            evaluated_tier TEXT NOT NULL,
            identified_misconceptions TEXT NOT NULL DEFAULT '[]',
            feedback_notes TEXT NOT NULL DEFAULT '',
            evaluated_at TEXT NOT NULL
        );

        -- 10. Assessment Evidence
        CREATE TABLE IF NOT EXISTS assessment_evidence (
            evidence_id TEXT PRIMARY KEY,
            assessment_id TEXT NOT NULL REFERENCES assessments(assessment_id) ON DELETE CASCADE,
            learner_id TEXT NOT NULL,
            evidence_type TEXT NOT NULL,
            raw_input TEXT NOT NULL,
            raw_output TEXT NOT NULL,
            timestamp TEXT NOT NULL
        );

        -- 11. Learning Sessions
        CREATE TABLE IF NOT EXISTS learning_sessions (
            session_id TEXT PRIMARY KEY,
            learner_id TEXT NOT NULL REFERENCES learners(learner_id) ON DELETE CASCADE,
            goal_id TEXT,
            start_time TEXT NOT NULL,
            end_time TEXT,
            duration_minutes REAL NOT NULL DEFAULT 0.0,
            topics_covered TEXT NOT NULL DEFAULT '[]',
            tasks_completed TEXT NOT NULL DEFAULT '[]',
            notes TEXT NOT NULL DEFAULT ''
        );

        -- 12. Learning Events
        CREATE TABLE IF NOT EXISTS learning_events (
            event_id TEXT PRIMARY KEY,
            learner_id TEXT NOT NULL REFERENCES learners(learner_id) ON DELETE CASCADE,
            event_name TEXT NOT NULL,
            payload TEXT NOT NULL DEFAULT '{}',
            timestamp TEXT NOT NULL
        );

        -- 13. Learning Tasks
        CREATE TABLE IF NOT EXISTS learning_tasks (
            task_id TEXT PRIMARY KEY,
            learner_id TEXT NOT NULL REFERENCES learners(learner_id) ON DELETE CASCADE,
            goal_id TEXT,
            title TEXT NOT NULL,
            topic_id TEXT NOT NULL,
            estimated_minutes INTEGER NOT NULL DEFAULT 30,
            status TEXT NOT NULL DEFAULT 'pending',
            parameters TEXT NOT NULL DEFAULT '{}',
            completed_at TEXT
        );

        -- 14. Resources
        CREATE TABLE IF NOT EXISTS resources (
            resource_id TEXT PRIMARY KEY,
            topic_id TEXT NOT NULL,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            resource_type TEXT NOT NULL,
            evaluation TEXT,
            recommended_order INTEGER NOT NULL DEFAULT 1
        );

        -- 15. Progress Snapshots
        CREATE TABLE IF NOT EXISTS progress_snapshots (
            snapshot_id TEXT PRIMARY KEY,
            learner_id TEXT NOT NULL REFERENCES learners(learner_id) ON DELETE CASCADE,
            timestamp TEXT NOT NULL,
            topics_mastered_count INTEGER NOT NULL DEFAULT 0,
            topics_practicing_count INTEGER NOT NULL DEFAULT 0,
            active_gaps_count INTEGER NOT NULL DEFAULT 0,
            average_mastery REAL NOT NULL DEFAULT 0.0,
            velocity_topics_per_week REAL NOT NULL DEFAULT 0.0
        );

        -- 16. Interaction Memory
        CREATE TABLE IF NOT EXISTS interaction_memory (
            interaction_id TEXT PRIMARY KEY,
            learner_id TEXT NOT NULL REFERENCES learners(learner_id) ON DELETE CASCADE,
            session_id TEXT,
            topic_id TEXT,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp TEXT NOT NULL
        );

        -- 17. Typed Memory Items (General Semantic & Episodic Index)
        CREATE TABLE IF NOT EXISTS memory_items (
            memory_id TEXT PRIMARY KEY,
            learner_id TEXT NOT NULL REFERENCES learners(learner_id) ON DELETE CASCADE,
            memory_type TEXT NOT NULL,
            key TEXT NOT NULL,
            content TEXT NOT NULL,
            structured_data TEXT,
            source TEXT NOT NULL,
            epistemic_status TEXT NOT NULL,
            importance INTEGER NOT NULL DEFAULT 3,
            confidence REAL NOT NULL DEFAULT 1.0,
            topic_id TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            last_accessed_at TEXT,
            access_count INTEGER NOT NULL DEFAULT 0
        );

        -- 18. Learning Plans
        CREATE TABLE IF NOT EXISTS learning_plans (
            plan_id TEXT PRIMARY KEY,
            learner_id TEXT NOT NULL REFERENCES learners(learner_id) ON DELETE CASCADE,
            goal_id TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            objective TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT 'proposed',
            strategy TEXT NOT NULL DEFAULT 'balanced',
            version INTEGER NOT NULL DEFAULT 1,
            parent_plan_id TEXT,
            revision_reason TEXT,
            total_estimated_hours REAL NOT NULL DEFAULT 10.0,
            estimated_total_minutes INTEGER NOT NULL DEFAULT 600,
            priority INTEGER NOT NULL DEFAULT 3,
            dependencies TEXT NOT NULL DEFAULT '{}',
            assumptions TEXT NOT NULL DEFAULT '[]',
            expected_outcomes TEXT NOT NULL DEFAULT '[]',
            validation_status TEXT NOT NULL DEFAULT 'valid',
            provenance TEXT NOT NULL DEFAULT '{}',
            explanation TEXT NOT NULL DEFAULT '{}',
            start_date TEXT,
            target_date TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        -- 19. Study Phases
        CREATE TABLE IF NOT EXISTS study_phases (
            phase_id TEXT PRIMARY KEY,
            plan_id TEXT NOT NULL REFERENCES learning_plans(plan_id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            title TEXT NOT NULL,
            objective TEXT NOT NULL DEFAULT '',
            concepts TEXT NOT NULL DEFAULT '[]',
            prerequisite_phase_ids TEXT NOT NULL DEFAULT '[]',
            task_ids TEXT NOT NULL DEFAULT '[]',
            estimated_minutes INTEGER NOT NULL DEFAULT 0,
            phase_order INTEGER NOT NULL DEFAULT 1,
            completion_criteria TEXT NOT NULL DEFAULT '[]',
            status TEXT NOT NULL DEFAULT 'pending',
            is_completed INTEGER NOT NULL DEFAULT 0
        );

        -- 20. Plan Milestones
        CREATE TABLE IF NOT EXISTS plan_milestones (
            milestone_id TEXT PRIMARY KEY,
            plan_id TEXT NOT NULL REFERENCES learning_plans(plan_id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            objective TEXT NOT NULL DEFAULT '',
            required_task_ids TEXT NOT NULL DEFAULT '[]',
            required_concepts TEXT NOT NULL DEFAULT '[]',
            completion_criteria TEXT NOT NULL DEFAULT '[]',
            status TEXT NOT NULL DEFAULT 'pending',
            milestone_order INTEGER NOT NULL DEFAULT 1,
            target_date TEXT,
            achieved_at TEXT
        );

        -- 21. Plan Versions (Audit Trail)
        CREATE TABLE IF NOT EXISTS plan_versions (
            version_id TEXT PRIMARY KEY,
            plan_id TEXT NOT NULL,
            learner_id TEXT NOT NULL REFERENCES learners(learner_id) ON DELETE CASCADE,
            version INTEGER NOT NULL,
            status TEXT NOT NULL,
            change_reason TEXT NOT NULL DEFAULT '',
            snapshot_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        -- 22. Research History
        CREATE TABLE IF NOT EXISTS research_history (
            history_id TEXT PRIMARY KEY,
            learner_id TEXT NOT NULL,
            task_id TEXT NOT NULL,
            concept_id TEXT NOT NULL,
            query TEXT NOT NULL,
            provider TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'success',
            discovered_count INTEGER NOT NULL DEFAULT 0,
            selected_count INTEGER NOT NULL DEFAULT 0,
            selected_resource_ids TEXT NOT NULL DEFAULT '[]',
            timestamp TEXT NOT NULL
        );

        -- Indexes for fast isolated retrieval
        CREATE INDEX IF NOT EXISTS idx_goals_learner ON learning_goals(learner_id, is_active);
        CREATE INDEX IF NOT EXISTS idx_mastery_learner ON topic_mastery(learner_id, tier);
        CREATE INDEX IF NOT EXISTS idx_gaps_learner ON knowledge_gaps(learner_id, resolved);
        -- 23. Session Interactions (Phase 5)
        CREATE TABLE IF NOT EXISTS session_interactions (
            interaction_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL REFERENCES learning_sessions(session_id) ON DELETE CASCADE,
            turn_index INTEGER NOT NULL DEFAULT 0,
            speaker TEXT NOT NULL,
            stage TEXT NOT NULL,
            content TEXT NOT NULL,
            metadata TEXT NOT NULL DEFAULT '{}',
            timestamp TEXT NOT NULL
        );

        -- 24. Replanning Records (Phase 6 — Audit Trail)
        CREATE TABLE IF NOT EXISTS replanning_records (
            record_id TEXT PRIMARY KEY,
            learner_id TEXT NOT NULL REFERENCES learners(learner_id) ON DELETE CASCADE,
            old_plan_id TEXT NOT NULL,
            new_plan_id TEXT NOT NULL,
            trigger_type TEXT NOT NULL,
            trigger_evidence TEXT NOT NULL DEFAULT '{}',
            rationale TEXT NOT NULL DEFAULT '',
            changes_summary TEXT NOT NULL DEFAULT '',
            health_status TEXT NOT NULL DEFAULT 'healthy',
            created_at TEXT NOT NULL
        );

        -- 25. Review Schedules (Phase 6 — Spaced Repetition)
        CREATE TABLE IF NOT EXISTS review_schedules (
            schedule_id TEXT PRIMARY KEY,
            learner_id TEXT NOT NULL REFERENCES learners(learner_id) ON DELETE CASCADE,
            topic_id TEXT NOT NULL,
            next_review_at TEXT NOT NULL,
            interval_days REAL NOT NULL DEFAULT 1.0,
            ease_factor REAL NOT NULL DEFAULT 2.5,
            repetitions INTEGER NOT NULL DEFAULT 0,
            urgency TEXT NOT NULL DEFAULT 'normal',
            last_reviewed_at TEXT,
            last_mastery_score REAL NOT NULL DEFAULT 0.0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(learner_id, topic_id)
        );

        -- 26. Autonomous Tasks (Phase 7 — Multi-step Orchestration)
        CREATE TABLE IF NOT EXISTS autonomous_tasks (
            task_id TEXT PRIMARY KEY,
            learner_id TEXT NOT NULL REFERENCES learners(learner_id) ON DELETE CASCADE,
            goal TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'created',
            risk_level TEXT NOT NULL DEFAULT 'low',
            current_step INTEGER NOT NULL DEFAULT 0,
            max_steps INTEGER NOT NULL DEFAULT 10,
            cancellation_reason TEXT,
            result_summary TEXT NOT NULL DEFAULT '',
            metadata TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            completed_at TEXT
        );

        -- 27. Agent Steps (Phase 7 — Observe/Plan/Act/Verify Step Audit)
        CREATE TABLE IF NOT EXISTS agent_steps (
            step_id TEXT PRIMARY KEY,
            task_id TEXT NOT NULL REFERENCES autonomous_tasks(task_id) ON DELETE CASCADE,
            step_index INTEGER NOT NULL,
            action TEXT NOT NULL,
            capability_id TEXT NOT NULL,
            risk_level TEXT NOT NULL DEFAULT 'low',
            status TEXT NOT NULL DEFAULT 'pending',
            parameters TEXT NOT NULL DEFAULT '{}',
            result TEXT NOT NULL DEFAULT '{}',
            verification_status TEXT NOT NULL DEFAULT 'pending',
            verification_notes TEXT NOT NULL DEFAULT '',
            error TEXT,
            started_at TEXT,
            completed_at TEXT
        );

        -- 28. Permission Audit Log (Phase 7 — Permission Checks & Elevation Tracking)
        CREATE TABLE IF NOT EXISTS permission_audit_log (
            log_id TEXT PRIMARY KEY,
            task_id TEXT,
            permission_category TEXT NOT NULL,
            action TEXT NOT NULL,
            status TEXT NOT NULL,
            rationale TEXT NOT NULL DEFAULT '',
            timestamp TEXT NOT NULL
        );

        -- 29. Project Learning Contexts (Phase 7 — Project-based learning & code understanding)
        CREATE TABLE IF NOT EXISTS project_learning_contexts (
            project_id TEXT PRIMARY KEY,
            learner_id TEXT NOT NULL REFERENCES learners(learner_id) ON DELETE CASCADE,
            project_path TEXT NOT NULL,
            project_name TEXT NOT NULL,
            language TEXT NOT NULL,
            framework TEXT NOT NULL DEFAULT '',
            summary TEXT NOT NULL DEFAULT '',
            important_files TEXT NOT NULL DEFAULT '[]',
            architecture_notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        -- 30. Multimodal Artifacts (Phase 7 — Metadata for images, docs, screenshots)
        CREATE TABLE IF NOT EXISTS multimodal_artifacts (
            artifact_id TEXT PRIMARY KEY,
            learner_id TEXT NOT NULL REFERENCES learners(learner_id) ON DELETE CASCADE,
            artifact_type TEXT NOT NULL,
            file_path TEXT,
            summary TEXT NOT NULL DEFAULT '',
            extracted_text TEXT NOT NULL DEFAULT '',
            metadata TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_misc_learner ON misconceptions(learner_id, topic_id);
        CREATE INDEX IF NOT EXISTS idx_assess_learner ON assessments(learner_id, topic_id);
        CREATE INDEX IF NOT EXISTS idx_sess_learner ON learning_sessions(learner_id, start_time);
        CREATE INDEX IF NOT EXISTS idx_sess_interactions ON session_interactions(session_id, turn_index);
        CREATE INDEX IF NOT EXISTS idx_tasks_learner ON learning_tasks(learner_id, status);
        CREATE INDEX IF NOT EXISTS idx_plans_learner ON learning_plans(learner_id, status);
        CREATE INDEX IF NOT EXISTS idx_phases_plan ON study_phases(plan_id, phase_order);
        CREATE INDEX IF NOT EXISTS idx_milestones_plan ON plan_milestones(plan_id, milestone_order);
        CREATE INDEX IF NOT EXISTS idx_plan_versions ON plan_versions(plan_id, version);
        CREATE INDEX IF NOT EXISTS idx_items_learner_type ON memory_items(learner_id, memory_type);
        CREATE INDEX IF NOT EXISTS idx_items_key ON memory_items(learner_id, key);
        CREATE INDEX IF NOT EXISTS idx_research_learner ON research_history(learner_id, task_id);
        CREATE INDEX IF NOT EXISTS idx_replanning_learner ON replanning_records(learner_id, created_at);
        CREATE INDEX IF NOT EXISTS idx_review_schedules ON review_schedules(learner_id, next_review_at);
        CREATE INDEX IF NOT EXISTS idx_agent_tasks_learner ON autonomous_tasks(learner_id, status);
        CREATE INDEX IF NOT EXISTS idx_agent_steps_task ON agent_steps(task_id, step_index);
        CREATE INDEX IF NOT EXISTS idx_project_learner ON project_learning_contexts(learner_id, project_path);
        CREATE INDEX IF NOT EXISTS idx_multimodal_learner ON multimodal_artifacts(learner_id, artifact_type);
        """
        with self._lock:
            conn = self.get_connection()
            conn.executescript(schema_sql)

            # Ensure optional extended columns for learning_tasks if upgraded
            for col_name, col_type in [
                ("plan_id", "TEXT"),
                ("phase_id", "TEXT"),
                ("concept_id", "TEXT NOT NULL DEFAULT ''"),
                ("description", "TEXT NOT NULL DEFAULT ''"),
                ("task_type", "TEXT NOT NULL DEFAULT 'practice'"),
                ("objective", "TEXT NOT NULL DEFAULT ''"),
                ("difficulty", "INTEGER NOT NULL DEFAULT 2"),
                ("priority", "REAL NOT NULL DEFAULT 1.0"),
                ("prerequisite_task_ids", "TEXT NOT NULL DEFAULT '[]'"),
                ("prerequisite_concept_ids", "TEXT NOT NULL DEFAULT '[]'"),
                ("expected_evidence", "TEXT NOT NULL DEFAULT ''"),
                ("completion_criteria", "TEXT NOT NULL DEFAULT '[]'"),
                ("mastery_target", "REAL NOT NULL DEFAULT 0.70"),
                ("task_order", "INTEGER NOT NULL DEFAULT 1"),
                ("rationale", "TEXT NOT NULL DEFAULT ''"),
                ("resource_ids", "TEXT NOT NULL DEFAULT '[]'"),
            ]:
                try:
                    conn.execute(f"ALTER TABLE learning_tasks ADD COLUMN {col_name} {col_type};")
                except Exception:
                    pass

            # Ensure extended columns for resources
            for col_name, col_type in [
                ("domain", "TEXT NOT NULL DEFAULT ''"),
                ("provider", "TEXT NOT NULL DEFAULT 'mock'"),
                ("author", "TEXT"),
                ("description", "TEXT NOT NULL DEFAULT ''"),
                ("concept_ids", "TEXT NOT NULL DEFAULT '[]'"),
                ("task_ids", "TEXT NOT NULL DEFAULT '[]'"),
                ("difficulty", "INTEGER NOT NULL DEFAULT 2"),
                ("language", "TEXT NOT NULL DEFAULT 'en'"),
                ("duration_minutes", "REAL"),
                ("published_at", "TEXT"),
                ("updated_at", "TEXT"),
                ("relevance_score", "REAL NOT NULL DEFAULT 0.5"),
                ("authority_score", "REAL NOT NULL DEFAULT 0.5"),
                ("quality_score", "REAL NOT NULL DEFAULT 0.5"),
                ("learner_fit_score", "REAL NOT NULL DEFAULT 0.5"),
                ("freshness_score", "REAL NOT NULL DEFAULT 0.5"),
                ("usefulness_score", "REAL NOT NULL DEFAULT 0.5"),
                ("overall_score", "REAL NOT NULL DEFAULT 0.5"),
                ("confidence", "REAL NOT NULL DEFAULT 0.7"),
                ("provenance", "TEXT NOT NULL DEFAULT '{}'"),
                ("evaluation_notes", "TEXT NOT NULL DEFAULT '[]'"),
                ("discovered_at", "TEXT"),
                ("last_verified_at", "TEXT"),
            ]:
                try:
                    conn.execute(f"ALTER TABLE resources ADD COLUMN {col_name} {col_type};")
                except Exception:
                    pass

            # Ensure extended columns for learning_sessions (Phase 5)
            for col_name, col_type in [
                ("plan_id", "TEXT"),
                ("task_id", "TEXT"),
                ("concept_id", "TEXT"),
                ("objective", "TEXT NOT NULL DEFAULT ''"),
                ("status", "TEXT NOT NULL DEFAULT 'created'"),
                ("current_stage", "TEXT NOT NULL DEFAULT 'initialize'"),
                ("stage_history", "TEXT NOT NULL DEFAULT '[]'"),
                ("questions_asked", "TEXT NOT NULL DEFAULT '[]'"),
                ("answers_received", "TEXT NOT NULL DEFAULT '[]'"),
                ("hints_used", "INTEGER NOT NULL DEFAULT 0"),
                ("evidence_collected", "TEXT NOT NULL DEFAULT '[]'"),
                ("resources_used", "TEXT NOT NULL DEFAULT '[]'"),
                ("mastery_changes", "TEXT NOT NULL DEFAULT '{}'"),
                ("summary", "TEXT"),
                ("next_recommended_task_id", "TEXT"),
            ]:
                try:
                    conn.execute(f"ALTER TABLE learning_sessions ADD COLUMN {col_name} {col_type};")
                except Exception:
                    pass


class _TransactionContext:
    """Helper context manager for atomic transactions."""
    def __init__(self, store: TarkyaanMemoryStore):
        self.store = store
        self._conn = store.get_connection()

    def __enter__(self):
        self.store._lock.acquire()
        self._conn.execute("BEGIN TRANSACTION;")
        return self._conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is not None:
                self._conn.execute("ROLLBACK;")
            else:
                self._conn.execute("COMMIT;")
        finally:
            self.store._lock.release()
