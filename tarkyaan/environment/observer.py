"""
Environment Observer Interface.
Captures frontmost application, active file, and desktop context.
"""

from __future__ import annotations

from typing import Optional
from tarkyaan.environment.context import EnvironmentContext


class EnvironmentObserver:
    """
    Observes system environment state and produces an EnvironmentContext snapshot.
    """

    def __init__(self) -> None:
        self._current_context = EnvironmentContext()

    def get_current_context(self) -> EnvironmentContext:
        """Return the current cached environment context."""
        return self._current_context

    def update_learning_context(
        self,
        learner_id: Optional[str] = None,
        goal_id: Optional[str] = None,
        plan_id: Optional[str] = None,
        task_id: Optional[str] = None,
        concept_id: Optional[str] = None
    ) -> EnvironmentContext:
        """Update active educational focus."""
        self._current_context.active_goal_id = goal_id
        self._current_context.active_plan_id = plan_id
        self._current_context.active_task_id = task_id
        self._current_context.active_concept_id = concept_id
        return self._current_context

    def update_workspace_context(
        self,
        active_app: Optional[str] = None,
        file_path: Optional[str] = None,
        selected_text: Optional[str] = None
    ) -> EnvironmentContext:
        """Update active editor or file selection context."""
        if active_app:
            self._current_context.active_application = active_app
        if file_path:
            self._current_context.active_file_path = file_path
        if selected_text:
            self._current_context.selected_text = selected_text
        return self._current_context


# Global environment observer singleton
environment_observer = EnvironmentObserver()
