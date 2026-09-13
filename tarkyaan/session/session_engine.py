"""
Learning Session Engine for Tarkyaan Phase 5.
Coordinates persistent learning sessions, state transitions, interactive stages,
evidence collection, mastery updates, and post-session summaries.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from tarkyaan.events.event_bus import TarkyaanEvent, event_bus
from tarkyaan.learner.learner_model import LearnerModel
from tarkyaan.memory.memory_manager import TarkyaanMemoryManager
from tarkyaan.models.enums import (
    HintLevel,
    PracticeQuestionType,
    SessionStage,
    SessionStatus,
)
from tarkyaan.models.learning import LearningSession
from tarkyaan.models.practice import AnswerEvaluation, HintResponse, PracticeQuestion
from tarkyaan.models.session import (
    MasteryDeltaRecord,
    SessionInteraction,
    SessionSummary,
    StageTransitionRecord,
)
from tarkyaan.practice.practice_engine import PracticeEngine
from tarkyaan.session.evidence_collector import MasteryEvidenceCollector
from tarkyaan.session.state_machine import SessionStateMachine
from tarkyaan.teaching.teaching_engine import TeachingEngine


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class LearningSessionEngine:
    """
    Central learning session coordinator.
    Manages stage progression, pause/resume, teaching, practice, and persistent state.
    """

    def __init__(
        self,
        memory_manager: Optional[TarkyaanMemoryManager] = None,
        learner_model: Optional[LearnerModel] = None,
        teaching_engine: Optional[TeachingEngine] = None,
        practice_engine: Optional[PracticeEngine] = None
    ) -> None:
        self.memory = memory_manager or TarkyaanMemoryManager()
        self.learner_model = learner_model
        self.teaching_engine = teaching_engine or TeachingEngine(learner_model=learner_model)
        self.practice_engine = practice_engine or PracticeEngine()
        self.evidence_collector = MasteryEvidenceCollector(learner_model=learner_model)

    def create_session(
        self,
        learner_id: str,
        concept_id: str,
        objective: str,
        task_id: Optional[str] = None,
        plan_id: Optional[str] = None,
        goal_id: Optional[str] = None
    ) -> LearningSession:
        """Initialize a new persistent learning session in CREATED state."""
        session = LearningSession(
            session_id=f"sess_{uuid.uuid4().hex[:8]}",
            learner_id=learner_id,
            concept_id=concept_id,
            objective=objective,
            task_id=task_id,
            plan_id=plan_id,
            goal_id=goal_id,
            status=SessionStatus.CREATED,
            current_stage=SessionStage.INITIALIZE,
            start_time=_utc_now(),
            topics_covered=[concept_id]
        )
        self.memory.record_learning_session(session)
        event_bus.publish(
            TarkyaanEvent.LEARNING_SESSION_STARTED,
            {"session_id": session.session_id, "concept_id": concept_id, "objective": objective},
            learner_id=learner_id,
            source="session_engine"
        )
        return session

    def start_session(self, session_id: str) -> LearningSession:
        """Activate the session and advance to TEACH or RECALL."""
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Learning session '{session_id}' not found.")

        session.status = SessionStatus.ACTIVE
        self._advance_stage(session, SessionStage.TEACH, "Starting initial concept instruction.")
        self.memory.record_learning_session(session)
        return session

    def transition_stage(
        self,
        session_id: str,
        target_stage: SessionStage,
        reason: str = ""
    ) -> LearningSession:
        """Transition active session to another stage according to state machine."""
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Learning session '{session_id}' not found.")

        self._advance_stage(session, target_stage, reason)
        self.memory.record_learning_session(session)
        return session

    def _advance_stage(
        self,
        session: LearningSession,
        target_stage: SessionStage,
        reason: str
    ) -> None:
        """Execute validated stage transition."""
        transition_rec = SessionStateMachine.create_transition_record(
            from_stage=session.current_stage,
            to_stage=target_stage,
            reason=reason
        )
        session.stage_history.append(transition_rec)
        session.current_stage = target_stage

        # Record interaction turn
        self.record_interaction(
            session_id=session.session_id,
            speaker="system",
            stage=target_stage,
            content=f"Transitioned to stage: {target_stage.value}. Reason: {reason}",
            metadata={"from_stage": transition_rec.from_stage.value, "to_stage": target_stage.value}
        )

    def pause_session(self, session_id: str, notes: str = "") -> LearningSession:
        """Pause active learning session, preserving complete progress in memory."""
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session '{session_id}' not found.")

        session.status = SessionStatus.PAUSED
        if notes:
            session.notes = f"{session.notes}\nPaused: {notes}".strip()
        self.memory.record_learning_session(session)

        self.record_interaction(
            session_id=session_id,
            speaker="system",
            stage=session.current_stage,
            content="Session paused by learner or system.",
            metadata={"notes": notes}
        )
        return session

    def resume_session(self, session_id: str) -> LearningSession:
        """Resume a paused session at its exact previous stage and context."""
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session '{session_id}' not found.")

        session.status = SessionStatus.ACTIVE
        self.memory.record_learning_session(session)

        self.record_interaction(
            session_id=session_id,
            speaker="system",
            stage=session.current_stage,
            content=f"Session resumed at stage: {session.current_stage.value}."
        )
        return session

    def cancel_session(self, session_id: str, reason: str = "") -> LearningSession:
        """Cancel an ongoing session."""
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session '{session_id}' not found.")

        session.status = SessionStatus.CANCELLED
        session.end_session(notes=f"Cancelled: {reason}")
        self.memory.record_learning_session(session)
        return session

    def complete_session(self, session_id: str) -> SessionSummary:
        """
        Finalize session, apply evidence to Phase 1 MasteryEngine, and produce summary.
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session '{session_id}' not found.")

        # Ensure terminal stage
        if session.current_stage != SessionStage.COMPLETE:
            if SessionStateMachine.can_transition(session.current_stage, SessionStage.COMPLETE):
                self._advance_stage(session, SessionStage.COMPLETE, "Session completed.")

        session.status = SessionStatus.COMPLETED
        session.end_session()

        # Apply collected evidence to mastery via MasteryEvidenceCollector
        mastery_deltas: List[MasteryDeltaRecord] = []
        if session.concept_id and self.learner_model and session.answers_received:
            prior_m_obj = self.learner_model.get_topic_mastery(session.concept_id)
            prior_val = prior_m_obj.mastery_score if prior_m_obj else 0.0

            assess_result = self.evidence_collector.apply_session_evidence_to_mastery(
                concept_id=session.concept_id,
                evaluations=session.answers_received,
                total_hints_used=session.hints_used,
                task_id=session.task_id,
                learner_model=self.learner_model
            )
            if assess_result:
                new_val = assess_result.new_mastery
                delta = round(new_val - prior_val, 4)
                mastery_deltas.append(MasteryDeltaRecord(
                    concept_id=session.concept_id,
                    prior_mastery=prior_val,
                    new_mastery=new_val,
                    delta=delta,
                    evidence_count=len(session.answers_received)
                ))
                session.mastery_changes[session.concept_id] = {
                    "prior": prior_val,
                    "new": new_val,
                    "delta": delta
                }

        # Analyze strengths and remaining weaknesses
        correct_count = sum(1 for a in session.answers_received if a.is_correct)
        strengths: List[str] = []
        weaknesses: List[str] = []
        misconceptions: List[str] = []

        for a in session.answers_received:
            if a.detected_misconceptions:
                misconceptions.extend(a.detected_misconceptions)
            if a.is_correct or a.score >= 0.70:
                strengths.append(f"Strong understanding demonstrated on question {a.question_id}")
            else:
                weaknesses.append(f"Struggled on question {a.question_id}")

        if not strengths and correct_count > 0:
            strengths.append(f"Successfully solved {correct_count} practice exercises.")
        if not weaknesses and not misconceptions:
            strengths.append("No active misconceptions detected during session.")

        rec_next_action = "Advance to next curriculum milestone" if correct_count >= 1 else "Review fundamentals and retry practice"

        summary = SessionSummary(
            session_id=session.session_id,
            learner_id=session.learner_id,
            objective=session.objective,
            duration_minutes=session.duration_minutes,
            stages_traversed=[h.to_stage for h in session.stage_history],
            concepts_covered=session.topics_covered,
            questions_attempted=len(session.questions_asked),
            questions_correct=correct_count,
            hints_requested=session.hints_used,
            strengths_demonstrated=strengths[:3],
            remaining_weaknesses=weaknesses[:3],
            misconceptions_addressed=list(set(misconceptions)),
            mastery_changes=mastery_deltas,
            recommended_next_task_id=session.next_recommended_task_id,
            recommended_next_action=rec_next_action
        )

        session.summary = summary
        self.memory.record_learning_session(session)

        event_bus.publish(
            TarkyaanEvent.LEARNING_SESSION_ENDED,
            {"session_id": session.session_id, "summary": summary.model_dump(mode="json")},
            learner_id=session.learner_id,
            source="session_engine"
        )
        return summary

    def present_practice_question(
        self,
        session_id: str,
        difficulty: int = 2,
        question_type: Optional[PracticeQuestionType] = None
    ) -> PracticeQuestion:
        """Generate and attach a practice question to the session."""
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session '{session_id}' not found.")

        q = self.practice_engine.generate_practice(
            concept_id=session.concept_id or "general",
            difficulty=difficulty,
            question_type=question_type,
            session_id=session_id,
            learner_id=session.learner_id
        )
        session.questions_asked.append(q)
        self.memory.record_learning_session(session)

        self.record_interaction(
            session_id=session_id,
            speaker="companion",
            stage=session.current_stage,
            content=q.prompt,
            metadata={"question_id": q.question_id, "difficulty": q.difficulty}
        )
        return q

    def submit_answer(
        self,
        session_id: str,
        question_id: str,
        learner_response: str
    ) -> AnswerEvaluation:
        """Evaluate learner answer, record it in session, and return evaluation."""
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session '{session_id}' not found.")

        # Find matching question
        target_q: Optional[PracticeQuestion] = None
        for q in reversed(session.questions_asked):
            if q.question_id == question_id:
                target_q = q
                break

        if not target_q:
            raise ValueError(f"Question '{question_id}' not found in session '{session_id}'.")

        eval_result = self.practice_engine.evaluate_response(
            question=target_q,
            learner_response=learner_response,
            hints_used=session.hints_used
        )
        session.answers_received.append(eval_result)
        session.evidence_collected.append(eval_result.score)
        self.memory.record_learning_session(session)

        self.record_interaction(
            session_id=session_id,
            speaker="learner",
            stage=session.current_stage,
            content=learner_response,
            metadata={"question_id": question_id}
        )
        self.record_interaction(
            session_id=session_id,
            speaker="companion",
            stage=session.current_stage,
            content=eval_result.feedback,
            metadata={
                "score": eval_result.score,
                "is_correct": eval_result.is_correct,
                "action": eval_result.suggested_action
            }
        )
        return eval_result

    def request_hint_for_active_question(
        self,
        session_id: str,
        question_id: Optional[str] = None,
        allow_solution: bool = False
    ) -> HintResponse:
        """Request progressive hint for active question, tracking hint usage count."""
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session '{session_id}' not found.")

        if not session.questions_asked:
            raise ValueError(f"No questions present in session '{session_id}'.")

        target_q = session.questions_asked[-1]
        if question_id:
            for q in reversed(session.questions_asked):
                if q.question_id == question_id:
                    target_q = q
                    break

        session.hints_used += 1
        # Determine hint level
        level = min(HintLevel.FULL_SOLUTION if allow_solution else HintLevel.NEAR_SOLUTION, HintLevel(min(5, session.hints_used)))

        hint_resp = self.practice_engine.request_hint(
            question=target_q,
            requested_level=level,
            attempt_count=len([a for a in session.answers_received if a.question_id == target_q.question_id]),
            session_id=session_id,
            allow_full_solution=allow_solution
        )
        self.memory.record_learning_session(session)

        self.record_interaction(
            session_id=session_id,
            speaker="companion",
            stage=session.current_stage,
            content=hint_resp.hint_text,
            metadata={"hint_level": hint_resp.hint_level.value, "remaining": hint_resp.remaining_hints}
        )
        return hint_resp

    def record_interaction(
        self,
        session_id: str,
        speaker: str,
        stage: SessionStage,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log dialogue or event turn in memory manager."""
        return self.memory.record_session_interaction(
            session_id=session_id,
            speaker=speaker,
            stage=stage.value if hasattr(stage, "value") else str(stage),
            content=content,
            metadata=metadata
        )

    def get_session(self, session_id: str) -> Optional[LearningSession]:
        """Fetch session from persistent memory."""
        return self.memory.get_learning_session(session_id)
