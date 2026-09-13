"""
Unit tests for TarkyaanMemoryStore SQLite engine.
"""

import sqlite3
import pytest
from pathlib import Path

from tarkyaan.memory.memory_store import TarkyaanMemoryStore


class TestMemoryStore:
    def test_in_memory_initialization(self):
        store = TarkyaanMemoryStore(":memory:")
        assert store.db_path == ":memory:"
        # Verify tables exist
        rows = store.fetchall("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {r["name"] for r in rows}
        expected_tables = {
            "learners", "learning_goals", "subjects", "topics",
            "topic_prerequisites", "topic_mastery", "knowledge_gaps",
            "misconceptions", "assessments", "assessment_evidence",
            "learning_sessions", "learning_events", "learning_tasks",
            "resources", "progress_snapshots", "interaction_memory",
            "memory_items"
        }
        assert expected_tables.issubset(tables)
        store.close()

    def test_file_database_initialization(self, tmp_path: Path):
        db_file = tmp_path / "test_tarkyaan.db"
        store = TarkyaanMemoryStore(db_file)
        assert db_file.is_file()
        store.execute(
            "INSERT INTO subjects (subject_id, name, domain) VALUES (?, ?, ?);",
            ("dsa", "DSA", "CS")
        )
        row = store.fetchone("SELECT * FROM subjects WHERE subject_id = ?;", ("dsa",))
        assert row is not None
        assert row["name"] == "DSA"
        store.close()

    def test_foreign_key_cascade(self):
        store = TarkyaanMemoryStore(":memory:")
        # Insert learner
        store.execute(
            """INSERT INTO learners (
                learner_id, display_name, primary_domain, preferred_language,
                preferred_learning_style, preferred_explanation_style,
                daily_time_budget_minutes, current_autonomy_level,
                created_at, updated_at, last_active_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);""",
            ("l_test", "Test Learner", "DSA", "C++", "hands_on", "socratic", 120, 3, "2026-01-01", "2026-01-01", "2026-01-01")
        )

        # Insert goal for this learner
        store.execute(
            """INSERT INTO learning_goals (
                goal_id, learner_id, title, target_outcome, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?);""",
            ("g_test", "l_test", "Master Trees", "Solve tree problems", "2026-01-01", "2026-01-01")
        )

        assert store.fetchone("SELECT * FROM learning_goals WHERE goal_id = ?;", ("g_test",)) is not None

        # Delete learner -> goal should cascade delete
        store.execute("DELETE FROM learners WHERE learner_id = ?;", ("l_test",))
        assert store.fetchone("SELECT * FROM learning_goals WHERE goal_id = ?;", ("g_test",)) is None
        store.close()

    def test_transaction_rollback(self):
        store = TarkyaanMemoryStore(":memory:")
        store.execute("INSERT INTO subjects (subject_id, name, domain) VALUES ('math', 'Math', 'STEM');")

        try:
            with store.transaction():
                store.execute("INSERT INTO subjects (subject_id, name, domain) VALUES ('calc', 'Calculus', 'STEM');")
                # Intentional error to trigger rollback
                raise RuntimeError("Force Rollback")
        except RuntimeError:
            pass

        assert store.fetchone("SELECT * FROM subjects WHERE subject_id = 'calc';") is None
        assert store.fetchone("SELECT * FROM subjects WHERE subject_id = 'math';") is not None
        store.close()
