"""
Tarkyaan Diagnostic Engine.
Master orchestrator for Phase 2: coordinates Socratic diagnostic questioning,
evidence generation, Bayesian mastery updates, prerequisite root-cause gap analysis,
misconception detection, and diagnostic report synthesis.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from tarkyaan.assessment.answer_evaluator import AnswerEvaluator
from tarkyaan.assessment.evidence import DiagnosticEvidence
from tarkyaan.assessment.question_generator import QuestionGenerator
from tarkyaan.knowledge.gap_analyzer import GapAnalyzer, RootCauseResult
from tarkyaan.knowledge.misconception_detector import MisconceptionDetector
from tarkyaan.knowledge.prerequisite_graph import PrerequisiteDAG
from tarkyaan.learner.mastery_engine import MasteryEngine
from tarkyaan.memory.memory_manager import TarkyaanMemoryManager
from tarkyaan.models.diagnostic import (
    DiagnosticQuestion,
    DiagnosticReport,
    DiagnosticSession,
    DiagnosticSessionStatus,
)
from tarkyaan.models.enums import MasteryTier, MisconceptionCategory
from tarkyaan.models.gaps import KnowledgeGap, MisconceptionRecord
from tarkyaan.models.mastery import TopicMastery


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DiagnosticEngine:
    """
    Orchestrates the entire diagnostic assessment lifecycle.
    Keeps all state in Tarkyaan's independent memory.
    """

    def __init__(
        self,
        memory_manager: Optional[TarkyaanMemoryManager] = None,
        dag: Optional[PrerequisiteDAG] = None
    ) -> None:
        self.memory = memory_manager or TarkyaanMemoryManager()
        self.dag = dag or PrerequisiteDAG()
        self._active_sessions: Dict[str, DiagnosticSession] = {}

    # =========================================================================
    # 1. SESSION MANAGEMENT
    # =========================================================================

    def start_session(
        self,
        learner_id: str,
        target_concepts: List[str],
        goal_id: Optional[str] = None,
        max_questions: int = 8
    ) -> DiagnosticSession:
        """
        Initiate a new interactive diagnostic session for a learner.
        """
        learner = self.memory.get_learner(learner_id)
        if not learner:
            raise ValueError(f"Cannot start diagnostic session: Learner '{learner_id}' not found.")

        # Ensure concepts exist in graph or create basic nodes
        for cid in target_concepts:
            if not self.dag.has_concept(cid):
                self.dag.add_concept(cid, name=cid)

        session = DiagnosticSession(
            session_id=f"ds_{uuid.uuid4().hex[:8]}",
            learner_id=learner_id,
            goal_id=goal_id,
            target_concepts=target_concepts,
            status=DiagnosticSessionStatus.IN_PROGRESS,
            max_questions=max_questions
        )
        self._active_sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[DiagnosticSession]:
        return self._active_sessions.get(session_id)

    def pause_session(self, session_id: str) -> Optional[DiagnosticSession]:
        sess = self.get_session(session_id)
        if sess:
            sess.pause()
        return sess

    def resume_session(self, session_id: str) -> Optional[DiagnosticSession]:
        sess = self.get_session(session_id)
        if sess and sess.status == DiagnosticSessionStatus.PAUSED:
            sess.status = DiagnosticSessionStatus.IN_PROGRESS
        return sess

    def cancel_session(self, session_id: str) -> Optional[DiagnosticSession]:
        sess = self.get_session(session_id)
        if sess:
            sess.cancel()
        return sess

    # =========================================================================
    # 2. SOCRATIC QUESTIONING & PROBING
    # =========================================================================

    def next_probe(self, session_id: str) -> Optional[DiagnosticQuestion]:
        """
        Select the next concept to evaluate and generate a tailored diagnostic probe.
        Prioritizes:
        1. Root blocking prerequisites if target concept's foundations are uncertain.
        2. Target concepts with high uncertainty or lowest mastery.
        """
        session = self.get_session(session_id)
        if not session or session.status != DiagnosticSessionStatus.IN_PROGRESS:
            return None

        # Check stopping criteria
        if len(session.questions_asked) >= session.max_questions:
            return None

        learner = self.memory.get_learner(session.learner_id)
        if not learner:
            return None

        # Collect current mastery map
        mastery_map: Dict[str, float] = {}
        uncertainty_map: Dict[str, float] = {}
        for cid in session.target_concepts:
            m = self.memory.get_topic_mastery(session.learner_id, cid)
            mastery_map[cid] = m.mastery_score if m else 0.0
            uncertainty_map[cid] = m.uncertainty if m else 1.0

        # Select concept: check if any prerequisite is blocking
        selected_concept = self._select_next_concept(session, mastery_map, uncertainty_map)
        if not selected_concept:
            return None

        current_m = mastery_map.get(selected_concept, 0.0)
        current_u = uncertainty_map.get(selected_concept, 1.0)
        concept_name = self.dag.get_concept(selected_concept).name if self.dag.has_concept(selected_concept) else selected_concept

        # Fetch recent misconceptions for this concept
        recent_misc = self.memory.get_misconceptions(session.learner_id, topic_id=selected_concept)

        question = QuestionGenerator.generate_question(
            learner=learner,
            concept_id=selected_concept,
            concept_name=concept_name,
            current_mastery=current_m,
            uncertainty=current_u,
            dag=self.dag,
            previous_questions=session.questions_asked,
            recent_misconceptions=recent_misc
        )

        session.questions_asked.append(question)
        return question

    def _select_next_concept(
        self,
        session: DiagnosticSession,
        mastery_map: Dict[str, float],
        uncertainty_map: Dict[str, float]
    ) -> Optional[str]:
        """Choose concept with highest uncertainty or examine an unprobed root prerequisite."""
        # 1. Check if an ancestor prerequisite needs verification first
        for target in session.target_concepts:
            blocking = self.dag.find_blocking_prerequisites(target, mastery_map, competence_threshold=0.70)
            for prereq in blocking:
                # If this prereq hasn't been probed yet in this session
                prereq_probed_count = sum(1 for q in session.questions_asked if q.concept_id == prereq)
                if prereq_probed_count == 0:
                    return prereq

        # 2. Otherwise pick target concept with highest uncertainty
        ranked = sorted(
            session.target_concepts,
            key=lambda cid: (uncertainty_map.get(cid, 1.0), -mastery_map.get(cid, 0.0)),
            reverse=True
        )

        for c in ranked:
            probed_count = sum(1 for q in session.questions_asked if q.concept_id == c)
            if probed_count < 3:  # Max 3 probes per concept in a single session
                return c

        return ranked[0] if ranked else None

    # =========================================================================
    # 3. ANSWER SUBMISSION & EVIDENCE EVALUATION
    # =========================================================================

    def submit_answer(
        self,
        session_id: str,
        question_id: str,
        response_text: str,
        submitted_code: Optional[str] = None,
        time_taken_seconds: float = 0.0
    ) -> DiagnosticEvidence:
        """
        Evaluate response, update mastery in memory, diagnose root gaps, and record misconceptions.
        """
        session = self.get_session(session_id)
        if not session or session.status != DiagnosticSessionStatus.IN_PROGRESS:
            raise ValueError(f"Diagnostic session '{session_id}' is not currently active.")

        # Find question
        question = next((q for q in session.questions_asked if q.question_id == question_id), None)
        if not question:
            raise ValueError(f"Question '{question_id}' not found in active session.")

        # Retrieve prior mastery
        prior_mastery_obj = self.memory.get_topic_mastery(session.learner_id, question.concept_id)
        prior_m = prior_mastery_obj.mastery_score if prior_mastery_obj else 0.0
        prior_u = prior_mastery_obj.uncertainty if prior_mastery_obj else 1.0

        # Prior assessments
        recent_assessments = self.memory.get_assessments(session.learner_id, topic_id=question.concept_id, limit=5)
        recent_scores = [a.score for a in recent_assessments]

        # Prior misconceptions
        prior_misc = self.memory.get_misconceptions(session.learner_id, topic_id=question.concept_id)

        # 1. Evaluate answer
        evidence = AnswerEvaluator.evaluate(
            learner_id=session.learner_id,
            question=question,
            response_text=response_text,
            submitted_code=submitted_code,
            time_taken_seconds=time_taken_seconds,
            prior_mastery=prior_m,
            recent_scores=recent_scores,
            prior_misconceptions=prior_misc
        )
        evidence.session_id = session_id

        # 2. Deterministic Mastery Update via Phase 1 MasteryEngine
        composite_score = evidence.composite_score
        update_result = MasteryEngine.calculate_update(
            current_mastery=prior_m,
            current_uncertainty=prior_u,
            evidence_score=composite_score
        )

        # Update topic mastery in Tarkyaan Memory
        concept_name = self.dag.get_concept(question.concept_id).name if self.dag.has_concept(question.concept_id) else question.concept_id
        prior_succ = prior_mastery_obj.successful_recalls if prior_mastery_obj else 0
        prior_fail = prior_mastery_obj.failed_recalls if prior_mastery_obj else 0
        new_succ = (prior_succ + 1) if composite_score >= 0.7 else prior_succ
        new_fail = (prior_fail + 1) if composite_score < 0.7 else prior_fail

        updated_mastery = TopicMastery(
            learner_id=session.learner_id,
            topic_id=question.concept_id,
            name=concept_name,
            mastery_score=update_result.new_mastery,
            uncertainty=update_result.new_uncertainty,
            tier=update_result.new_tier,
            last_practiced=_utc_now(),
            successful_recalls=new_succ,
            failed_recalls=new_fail
        )
        self.memory.update_topic_mastery(updated_mastery)

        # 3. Gap Analysis & Root-Cause Extraction
        mastery_map = {m.topic_id: m.mastery_score for m in self.memory.list_topic_mastery(session.learner_id)}
        discovered_gaps = GapAnalyzer.analyze_concept_gaps(
            learner_id=session.learner_id,
            target_concept=question.concept_id,
            mastery_map=mastery_map,
            dag=self.dag,
            diagnostic_evidence=f"Evidence from question {question.question_id}: score {composite_score}"
        )
        for g in discovered_gaps:
            self.memory.create_knowledge_gap(g)
            if g.gap_id not in session.discovered_gap_ids:
                session.discovered_gap_ids.append(g.gap_id)

        # 4. Misconception Recording
        candidate_misc = MisconceptionDetector.evaluate_error(
            learner_id=session.learner_id,
            topic_id=question.concept_id,
            error_tags=evidence.evaluation.detected_errors,
            reasoning_excerpt=response_text[:120],
            code_snippet=submitted_code,
            prior_mastery=prior_m,
            recent_scores=recent_scores,
            prior_misconceptions=prior_misc
        )
        for cand in candidate_misc:
            if cand.confidence >= 0.70:
                rec = MisconceptionDetector.create_record(session.learner_id, cand)
                self.memory.record_misconception(rec)
                if rec.record_id not in session.discovered_misconception_ids:
                    session.discovered_misconception_ids.append(rec.record_id)

        # 5. Update session records
        session.responses.append({
            "question_id": question_id,
            "concept_id": question.concept_id,
            "response": response_text,
            "code": submitted_code,
            "score": composite_score,
            "delta_mastery": update_result.delta_mastery
        })
        session.evidence_records.append(evidence.model_dump())
        session.mastery_deltas[question.concept_id] = update_result.delta_mastery

        # Auto-complete session if max questions reached
        if len(session.questions_asked) >= session.max_questions:
            session.complete()

        return evidence

    # =========================================================================
    # 4. REPORT SYNTHESIS
    # =========================================================================

    def complete_session(self, session_id: str) -> DiagnosticReport:
        """
        Finalize diagnostic session and synthesize structured report.
        """
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session '{session_id}' not found.")

        session.complete()
        learner = self.memory.get_learner(session.learner_id)

        # Assemble concept mastery map
        mastery_map: Dict[str, Dict[str, Any]] = {}
        all_masteries = self.memory.list_topic_mastery(session.learner_id)
        for m in all_masteries:
            mastery_map[m.topic_id] = {
                "name": m.name,
                "score": round(m.mastery_score, 2),
                "tier": m.tier.value,
                "uncertainty": round(m.uncertainty, 2)
            }

        # Knowledge gaps & root causes
        gaps_data: List[Dict[str, Any]] = []
        active_gaps = self.memory.get_active_gaps(session.learner_id)
        for gap in active_gaps:
            root_res = GapAnalyzer.find_root_cause(
                target_concept=gap.blocking_topic_id,
                mastery_map={k: v["score"] for k, v in mastery_map.items()},
                dag=self.dag
            )
            gaps_data.append({
                "gap_id": gap.gap_id,
                "concept_id": gap.concept_id,
                "blocking_topic_id": gap.blocking_topic_id,
                "severity": gap.severity,
                "diagnostic_evidence": gap.diagnostic_evidence,
                "root_cause_concept": root_res.root_concept if root_res else gap.concept_id,
                "root_cause_explanation": root_res.explanation if root_res else ""
            })

        # Misconceptions
        misconceptions = self.memory.get_misconceptions(session.learner_id)
        misc_data = [
            {
                "record_id": m.record_id,
                "topic_id": m.topic_id,
                "category": m.category.value,
                "description": m.description,
                "corrective_action": m.corrective_action_taken
            }
            for m in misconceptions
        ]

        # Strengths & Weaknesses
        strengths = [
            m.name for m in all_masteries
            if m.tier in (MasteryTier.COMPETENT, MasteryTier.MASTERED)
        ]
        weaknesses = [
            m.name for m in all_masteries
            if m.tier in (MasteryTier.INTRODUCED, MasteryTier.UNEXPLORED) and m.topic_id in session.target_concepts
        ]

        # Narrative summary
        narrative = (
            f"Diagnostic assessment evaluated {len(session.questions_asked)} probes across concepts "
            f"'{', '.join(session.target_concepts)}'. Pinpointed {len(gaps_data)} knowledge gap(s) "
            f"and {len(misc_data)} active cognitive misconception(s)."
        )

        report = DiagnosticReport(
            report_id=f"dr_{uuid.uuid4().hex[:8]}",
            learner_id=session.learner_id,
            goal_id=session.goal_id,
            session_id=session.session_id,
            overall_confidence=0.85,
            concept_mastery_map=mastery_map,
            knowledge_gaps=gaps_data,
            detected_misconceptions=misc_data,
            strengths=strengths,
            weaknesses=weaknesses,
            summary_narrative=narrative,
            next_learning_priorities=[g["concept_id"] for g in gaps_data if g["severity"] in ("critical", "high")]
        )

        return report
