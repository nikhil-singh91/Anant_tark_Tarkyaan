"""
Tarkyaan Progress Report Engine — Phase 6.
Generates rich, explainable learning progress reports from raw learner evidence.

Components:
- LearningVelocityAnalyzer:      Topics/session, completion rate, trend
- ResourceEffectivenessAnalyzer: Resource quality score aggregation
- ProgressReportEngine:          Synthesizes comprehensive LearningProgressReport
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from tarkyaan.models.enums import HealthStatus, MasteryTier


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Sub-Report Models
# ---------------------------------------------------------------------------

class VelocityReport(BaseModel):
    """Learning velocity measurements over a time window."""
    topics_per_session: float = 0.0
    sessions_analyzed: int = 0
    tasks_completed: int = 0
    tasks_total: int = 0
    task_completion_rate: float = 0.0
    trend: str = "stable"   # "improving", "declining", "stable"


class ResourceEffectivenessReport(BaseModel):
    """Aggregated resource effectiveness measurements."""
    high_impact_resource_ids: List[str] = Field(default_factory=list)
    low_impact_resource_ids: List[str] = Field(default_factory=list)
    avg_resource_score: float = 0.0
    resources_evaluated: int = 0


class MasteryProgressSummary(BaseModel):
    """Summary of mastery distribution across all tracked topics."""
    total_topics_tracked: int = 0
    mastered_count: int = 0
    competent_count: int = 0
    practicing_count: int = 0
    introduced_count: int = 0
    unexplored_count: int = 0
    average_mastery: float = 0.0
    top_strong_topics: List[str] = Field(default_factory=list)
    top_weak_topics: List[str] = Field(default_factory=list)


class LearningProgressReport(BaseModel):
    """
    Comprehensive learning progress report synthesized from all available evidence.
    Human-readable, auditable, and exportable.
    """
    learner_id: str
    report_id: str
    generated_at: datetime = Field(default_factory=_utc_now)
    health_status: HealthStatus = HealthStatus.HEALTHY
    velocity: VelocityReport = Field(default_factory=VelocityReport)
    mastery_summary: MasteryProgressSummary = Field(default_factory=MasteryProgressSummary)
    resource_effectiveness: ResourceEffectivenessReport = Field(
        default_factory=ResourceEffectivenessReport
    )
    active_gaps_count: int = 0
    resolved_gaps_count: int = 0
    active_plan_id: Optional[str] = None
    active_plan_version: Optional[int] = None
    total_sessions_completed: int = 0
    total_study_minutes: float = 0.0
    headline: str = ""
    recommendations: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# LearningVelocityAnalyzer
# ---------------------------------------------------------------------------

class LearningVelocityAnalyzer:
    """
    Computes topics-per-session velocity from session data.
    Also computes task completion rate and trend direction.
    """

    @classmethod
    def _parse_topics(cls, raw: Any) -> List[Any]:
        if isinstance(raw, list):
            return raw
        if isinstance(raw, str):
            try:
                val = json.loads(raw)
                return val if isinstance(val, list) else []
            except Exception:
                return []
        return []

    @classmethod
    def analyze(
        cls,
        sessions: List[Dict[str, Any]],
        tasks: Optional[List[Dict[str, Any]]] = None,
    ) -> VelocityReport:
        """
        :param sessions: List of session dicts with 'topics_covered'
        :param tasks:    Optional list of task dicts with 'status'
        """
        n = len(sessions)
        if n == 0:
            return VelocityReport()

        total_topics = sum(
            len(cls._parse_topics(s.get("topics_covered", [])))
            for s in sessions
        )
        topics_per_session = round(total_topics / n, 3)

        tasks_total = len(tasks) if tasks else 0
        tasks_completed = 0
        if tasks:
            tasks_completed = sum(
                1 for t in tasks if t.get("status") == "completed"
            )
        completion_rate = round(tasks_completed / max(tasks_total, 1), 3)

        # Trend: first half vs second half
        trend = "stable"
        if n >= 4:
            mid = n // 2
            first_vel = sum(
                len(cls._parse_topics(s.get("topics_covered", [])))
                for s in sessions[:mid]
            ) / mid
            second_vel = sum(
                len(cls._parse_topics(s.get("topics_covered", [])))
                for s in sessions[mid:]
            ) / (n - mid)
            if second_vel > first_vel * 1.1:
                trend = "improving"
            elif second_vel < first_vel * 0.9:
                trend = "declining"

        return VelocityReport(
            topics_per_session=topics_per_session,
            sessions_analyzed=n,
            tasks_completed=tasks_completed,
            tasks_total=tasks_total,
            task_completion_rate=completion_rate,
            trend=trend,
        )


# ---------------------------------------------------------------------------
# ResourceEffectivenessAnalyzer
# ---------------------------------------------------------------------------

class ResourceEffectivenessAnalyzer:
    """
    Evaluates which resources have high vs. low overall quality scores.
    """

    HIGH_SCORE_THRESHOLD: float = 0.75
    LOW_SCORE_THRESHOLD: float = 0.40

    @classmethod
    def analyze(cls, resources: List[Dict[str, Any]]) -> ResourceEffectivenessReport:
        """
        :param resources: List of resource dicts with 'resource_id' and 'overall_score'
        """
        if not resources:
            return ResourceEffectivenessReport()

        high_impact = [
            r["resource_id"] for r in resources
            if float(r.get("overall_score", 0.5)) >= cls.HIGH_SCORE_THRESHOLD
        ]
        low_impact = [
            r["resource_id"] for r in resources
            if float(r.get("overall_score", 0.5)) <= cls.LOW_SCORE_THRESHOLD
        ]
        avg_score = round(
            sum(float(r.get("overall_score", 0.5)) for r in resources) / len(resources), 3
        )
        return ResourceEffectivenessReport(
            high_impact_resource_ids=high_impact,
            low_impact_resource_ids=low_impact,
            avg_resource_score=avg_score,
            resources_evaluated=len(resources),
        )


# ---------------------------------------------------------------------------
# ProgressReportEngine
# ---------------------------------------------------------------------------

class ProgressReportEngine:
    """
    Synthesizes a comprehensive LearningProgressReport from memory evidence.
    """

    def __init__(
        self,
        memory: Optional[Any] = None,
        event_bus: Optional[Any] = None,
    ) -> None:
        self._memory = memory
        self._event_bus = event_bus

    @property
    def memory(self) -> Any:
        if self._memory is None:
            from tarkyaan.memory.memory_manager import TarkyaanMemoryManager
            self._memory = TarkyaanMemoryManager()
        return self._memory

    @property
    def bus(self) -> Any:
        if self._event_bus is None:
            from tarkyaan.events import event_bus as _bus
            return _bus
        return self._event_bus

    def generate_report(
        self,
        learner_id: str,
        health_status: HealthStatus = HealthStatus.HEALTHY,
    ) -> LearningProgressReport:
        """
        Generate a comprehensive progress report for a learner.
        Pulls all data from MemoryManager automatically.
        """
        report_id = f"report_{uuid.uuid4().hex[:8]}"

        # 1. Mastery summary
        mastery_summary = self._build_mastery_summary(learner_id)

        # 2. Session velocity
        velocity, total_sessions, total_study_minutes = self._build_velocity(learner_id)

        # 3. Gaps
        active_gaps_count, resolved_gaps_count = self._count_gaps(learner_id)

        # 4. Active plan
        active_plan_id, active_plan_version = self._active_plan_info(learner_id)

        # 5. Resource effectiveness
        resource_report = self._build_resource_report()

        # 6. Headline + recommendations
        headline = self._build_headline(health_status, mastery_summary, velocity)
        recommendations = self._build_recommendations(
            health_status, mastery_summary, active_gaps_count, velocity
        )

        report = LearningProgressReport(
            learner_id=learner_id,
            report_id=report_id,
            health_status=health_status,
            velocity=velocity,
            mastery_summary=mastery_summary,
            resource_effectiveness=resource_report,
            active_gaps_count=active_gaps_count,
            resolved_gaps_count=resolved_gaps_count,
            active_plan_id=active_plan_id,
            active_plan_version=active_plan_version,
            total_sessions_completed=total_sessions,
            total_study_minutes=round(total_study_minutes, 1),
            headline=headline,
            recommendations=recommendations,
        )

        # Publish event
        try:
            from tarkyaan.events.event_bus import TarkyaanEvent
            self.bus.publish(
                TarkyaanEvent.PROGRESS_REPORT_GENERATED,
                payload={"report_id": report_id, "health_status": health_status.value},
                learner_id=learner_id,
                source="progress_report_engine",
            )
        except Exception:
            pass

        return report

    def _build_mastery_summary(self, learner_id: str) -> MasteryProgressSummary:
        summary = MasteryProgressSummary()
        try:
            all_mastery = self.memory.get_all_topic_mastery(learner_id)
            if not all_mastery:
                return summary
            summary.total_topics_tracked = len(all_mastery)
            tier_counts: Dict[MasteryTier, int] = {t: 0 for t in MasteryTier}
            total_mastery = 0.0
            scored: List[Tuple[str, float]] = []
            for tm in all_mastery:
                try:
                    tier = MasteryTier(tm.tier)
                    tier_counts[tier] = tier_counts.get(tier, 0) + 1
                except Exception:
                    pass
                total_mastery += tm.mastery_score
                scored.append((tm.topic_id, tm.mastery_score))
            summary.mastered_count = tier_counts.get(MasteryTier.MASTERED, 0)
            summary.competent_count = tier_counts.get(MasteryTier.COMPETENT, 0)
            summary.practicing_count = tier_counts.get(MasteryTier.PRACTICING, 0)
            summary.introduced_count = tier_counts.get(MasteryTier.INTRODUCED, 0)
            summary.unexplored_count = tier_counts.get(MasteryTier.UNEXPLORED, 0)
            summary.average_mastery = round(total_mastery / len(all_mastery), 3)
            sorted_scores = sorted(scored, key=lambda x: x[1], reverse=True)
            summary.top_strong_topics = [t for t, _ in sorted_scores[:3]]
            summary.top_weak_topics = [t for t, _ in sorted_scores[-3:]]
        except Exception:
            pass
        return summary

    def _build_velocity(
        self, learner_id: str
    ) -> Tuple[VelocityReport, int, float]:
        try:
            rows = self.memory.store.fetchall(
                "SELECT * FROM learning_sessions WHERE learner_id = ? ORDER BY start_time DESC LIMIT 30;",
                (learner_id,)
            )
            session_dicts = [dict(r) for r in rows]
            total_sessions = len(session_dicts)
            total_minutes = sum(
                float(s.get("duration_minutes", 0) or 0) for s in session_dicts
            )
            velocity = LearningVelocityAnalyzer.analyze(sessions=session_dicts)
            return velocity, total_sessions, total_minutes
        except Exception:
            return VelocityReport(), 0, 0.0

    def _count_gaps(self, learner_id: str) -> Tuple[int, int]:
        try:
            active = self.memory.get_knowledge_gaps(learner_id, active_only=True)
            all_gaps = self.memory.get_knowledge_gaps(learner_id, active_only=False)
            return len(active), len(all_gaps) - len(active)
        except Exception:
            return 0, 0

    def _active_plan_info(self, learner_id: str) -> Tuple[Optional[str], Optional[int]]:
        try:
            plan = self.memory.get_active_learning_plan(learner_id)
            if plan:
                return plan.plan_id, plan.version
        except Exception:
            pass
        return None, None

    def _build_resource_report(self) -> ResourceEffectivenessReport:
        try:
            rows = self.memory.store.fetchall(
                "SELECT resource_id, overall_score FROM resources LIMIT 50;", ()
            )
            return ResourceEffectivenessAnalyzer.analyze([dict(r) for r in rows])
        except Exception:
            return ResourceEffectivenessReport()

    @staticmethod
    def _build_headline(
        health_status: HealthStatus,
        mastery: MasteryProgressSummary,
        velocity: VelocityReport,
    ) -> str:
        status_text = {
            HealthStatus.HEALTHY: "Learning is on track",
            HealthStatus.STALLED: "Learning progress has stalled",
            HealthStatus.REGRESSING: "Mastery regression detected",
            HealthStatus.OVERLOADED: "Difficulty overload detected",
            HealthStatus.PLATEAUED: "Learning has plateaued",
            HealthStatus.AT_RISK: "Multiple learning risk signals detected",
            HealthStatus.RECOVERING: "Learning is recovering",
        }.get(health_status, "Learning in progress")

        strong = mastery.mastered_count + mastery.competent_count
        return (
            f"{status_text}. "
            f"{strong}/{mastery.total_topics_tracked} topics at competent+ level "
            f"({velocity.task_completion_rate:.0%} task completion rate)."
        )

    @staticmethod
    def _build_recommendations(
        health_status: HealthStatus,
        mastery: MasteryProgressSummary,
        active_gaps: int,
        velocity: VelocityReport,
    ) -> List[str]:
        recs: List[str] = []
        if active_gaps > 0:
            recs.append(f"Address {active_gaps} active knowledge gap(s) before advancing.")
        if health_status == HealthStatus.STALLED:
            recs.append("Try shorter, more frequent sessions to break the stall.")
        if health_status == HealthStatus.OVERLOADED:
            recs.append("Reduce task difficulty; focus on foundational concepts first.")
        if health_status == HealthStatus.PLATEAUED:
            recs.append("Introduce varied practice types (apply, debug, compare) to break plateau.")
        if mastery.practicing_count > 0:
            recs.append(
                f"Consolidate {mastery.practicing_count} practicing topic(s) to reach competence."
            )
        if velocity.trend == "declining":
            recs.append("Velocity is declining — review session length and scheduling.")
        if not recs:
            recs.append("Continue your current learning rhythm — progress is healthy!")
        return recs
