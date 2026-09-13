"""
Tarkyaan Adaptive Learning Engine — Phase 6.
Continuously monitors learner evidence and drives autonomous curriculum adaptation.

Components:
- LearningHealthAnalyzer:      Classifies overall learner health from recent evidence
- MasteryTrajectoryAnalyzer:   Velocity, trend, regression detection
- GapEvolutionAnalyzer:        Gap age, recurrence, severity drift
- MisconceptionTrendAnalyzer:  Repeated error pattern analysis
- AdaptiveLearningEngine:      Top-level orchestrator (subscribes to EventBus)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from tarkyaan.models.enums import HealthStatus, MasteryTier, ReplanningTrigger


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Analysis Result Models
# ---------------------------------------------------------------------------

class MasteryTrajectory(BaseModel):
    """Computed mastery velocity and trend for a single topic."""
    topic_id: str
    current_mastery: float
    mastery_delta: float           # Change since first sample in window
    velocity: float                # mastery / sessions (positive = improving)
    is_regressing: bool
    is_plateaued: bool             # Stuck at same tier for many sessions
    sessions_sampled: int


class GapEvolutionReport(BaseModel):
    """Evolution status of tracked knowledge gaps."""
    total_active_gaps: int
    persistent_gap_ids: List[str]   # Gaps unresolved for > threshold sessions
    resolved_gap_count: int
    new_gap_count: int
    avg_gap_age_days: float


class MisconceptionTrend(BaseModel):
    """Recurrence pattern of misconceptions across sessions."""
    recurring_topic_ids: List[str]  # Topics with recurring misconceptions
    total_misconceptions: int
    recurring_count: int
    most_common_category: Optional[str]


class LearningHealthReport(BaseModel):
    """Holistic health classification with explainable signals."""
    health_status: HealthStatus
    signals: List[str] = Field(default_factory=list)     # Plain-language evidence
    triggers_detected: List[ReplanningTrigger] = Field(default_factory=list)
    trajectory: Optional[MasteryTrajectory] = None
    gap_report: Optional[GapEvolutionReport] = None
    misconception_trend: Optional[MisconceptionTrend] = None
    velocity_topics_per_session: float = 0.0
    analyzed_at: datetime = Field(default_factory=_utc_now)


# ---------------------------------------------------------------------------
# MasteryTrajectoryAnalyzer
# ---------------------------------------------------------------------------

class MasteryTrajectoryAnalyzer:
    """
    Computes mastery velocity and trend from a sequence of mastery snapshots.
    Detects regressions (mastery decreasing) and plateaus (tier unchanged
    despite multiple practice sessions).
    """

    REGRESSION_THRESHOLD: float = -0.05   # Delta below which regression is flagged
    PLATEAU_MIN_SESSIONS: int = 4          # Sessions at same tier = plateau
    STALL_DELTA_THRESHOLD: float = 0.02   # If total delta < this, considered stalled

    @classmethod
    def analyze(
        cls,
        topic_id: str,
        mastery_history: List[float],      # Ordered [oldest → newest]
        tier_history: Optional[List[str]] = None,
    ) -> MasteryTrajectory:
        """
        Analyze mastery history for velocity, regression, and plateau signals.

        :param topic_id:        Concept/topic being analyzed
        :param mastery_history: List of mastery scores ordered oldest → newest
        :param tier_history:    Parallel list of MasteryTier string values
        :return: MasteryTrajectory with computed signals
        """
        n = len(mastery_history)
        if n == 0:
            return MasteryTrajectory(
                topic_id=topic_id,
                current_mastery=0.0,
                mastery_delta=0.0,
                velocity=0.0,
                is_regressing=False,
                is_plateaued=False,
                sessions_sampled=0,
            )

        current = mastery_history[-1]
        first = mastery_history[0]
        delta = round(current - first, 4)
        velocity = round(delta / max(n - 1, 1), 4)

        is_regressing = delta < cls.REGRESSION_THRESHOLD

        is_plateaued = False
        if tier_history and len(tier_history) >= cls.PLATEAU_MIN_SESSIONS:
            recent_tiers = tier_history[-cls.PLATEAU_MIN_SESSIONS:]
            is_plateaued = len(set(recent_tiers)) == 1

        return MasteryTrajectory(
            topic_id=topic_id,
            current_mastery=current,
            mastery_delta=delta,
            velocity=velocity,
            is_regressing=is_regressing,
            is_plateaued=is_plateaued,
            sessions_sampled=n,
        )


# ---------------------------------------------------------------------------
# GapEvolutionAnalyzer
# ---------------------------------------------------------------------------

class GapEvolutionAnalyzer:
    """
    Analyzes knowledge gap persistence, recurrence, and severity trends.
    A gap is 'persistent' if it has been active for longer than the threshold.
    """

    PERSISTENCE_DAYS: int = 7      # Gap unresolved after 7 days → persistent

    @classmethod
    def analyze(
        cls,
        active_gaps: List[Dict[str, Any]],
        resolved_gaps: Optional[List[Dict[str, Any]]] = None,
    ) -> GapEvolutionReport:
        """
        :param active_gaps:   List of active gap dicts with 'gap_id' and 'detected_at'
        :param resolved_gaps: Optional list of recently resolved gaps
        """
        now = _utc_now()
        persistent_ids: List[str] = []
        total_age_days = 0.0

        for gap in active_gaps:
            detected_str = gap.get("detected_at", "")
            try:
                detected_at = datetime.fromisoformat(detected_str)
                if detected_at.tzinfo is None:
                    detected_at = detected_at.replace(tzinfo=timezone.utc)
                age_days = (now - detected_at).total_seconds() / 86400.0
                total_age_days += age_days
                if age_days > cls.PERSISTENCE_DAYS:
                    persistent_ids.append(gap["gap_id"])
            except Exception:
                pass

        avg_age = total_age_days / max(len(active_gaps), 1)
        resolved_count = len(resolved_gaps) if resolved_gaps else 0

        return GapEvolutionReport(
            total_active_gaps=len(active_gaps),
            persistent_gap_ids=persistent_ids,
            resolved_gap_count=resolved_count,
            new_gap_count=0,  # Caller can populate after diff
            avg_gap_age_days=round(avg_age, 2),
        )


# ---------------------------------------------------------------------------
# MisconceptionTrendAnalyzer
# ---------------------------------------------------------------------------

class MisconceptionTrendAnalyzer:
    """
    Detects recurring misconception patterns across sessions.
    A misconception is 'recurring' if the same topic appears more than once.
    """

    @classmethod
    def analyze(
        cls,
        misconceptions: List[Dict[str, Any]],
    ) -> MisconceptionTrend:
        """
        :param misconceptions: List of misconception dicts with 'topic_id' and 'category'
        """
        from collections import Counter

        topic_counts: Counter[str] = Counter()
        category_counts: Counter[str] = Counter()

        for m in misconceptions:
            topic_id = m.get("topic_id", "")
            category = m.get("category", "")
            if topic_id:
                topic_counts[topic_id] += 1
            if category:
                category_counts[category] += 1

        recurring = [t for t, c in topic_counts.items() if c > 1]
        most_common_cat = category_counts.most_common(1)[0][0] if category_counts else None

        return MisconceptionTrend(
            recurring_topic_ids=recurring,
            total_misconceptions=len(misconceptions),
            recurring_count=len(recurring),
            most_common_category=most_common_cat,
        )


# ---------------------------------------------------------------------------
# LearningHealthAnalyzer
# ---------------------------------------------------------------------------

class LearningHealthAnalyzer:
    """
    Synthesizes all evidence signals into a holistic LearningHealthReport.
    Classifies HealthStatus and identifies ReplanningTriggers.
    """

    # Evidence thresholds
    STALL_VELOCITY_THRESHOLD: float = 0.005  # < 0.5% per session = stall
    OVERLOAD_FAIL_RATE: float = 0.60          # > 60% failures in recent tasks = overload
    REGRESSION_DELTA: float = -0.05           # Mastery drop > 5% = regression
    GAP_PERSISTENCE_TRIGGER: int = 2          # ≥ 2 persistent gaps triggers replanning

    @classmethod
    def analyze(
        cls,
        trajectory: Optional[MasteryTrajectory] = None,
        gap_report: Optional[GapEvolutionReport] = None,
        misconception_trend: Optional[MisconceptionTrend] = None,
        recent_task_fail_rate: float = 0.0,
        sessions_since_last_progress: int = 0,
        stall_session_threshold: int = 3,
    ) -> LearningHealthReport:
        """
        Evaluate all signals and produce a classified health report.

        :param trajectory:                    Mastery velocity/trend analysis
        :param gap_report:                    Gap evolution report
        :param misconception_trend:           Misconception recurrence data
        :param recent_task_fail_rate:         Fraction of recent tasks failed [0,1]
        :param sessions_since_last_progress:  Sessions with no measurable improvement
        :param stall_session_threshold:       Sessions before stall is declared
        """
        signals: List[str] = []
        triggers: List[ReplanningTrigger] = []

        # 1. Stall
        stalled = False
        if sessions_since_last_progress >= stall_session_threshold:
            stalled = True
            signals.append(
                f"No progress detected for {sessions_since_last_progress} consecutive sessions."
            )
            triggers.append(ReplanningTrigger.STALL)

        # 2. Velocity drop
        if trajectory and abs(trajectory.velocity) < cls.STALL_VELOCITY_THRESHOLD and not stalled:
            signals.append(
                f"Very low learning velocity: {trajectory.velocity:.4f} mastery/session."
            )
            triggers.append(ReplanningTrigger.VELOCITY_DROP)

        # 3. Regression
        regression = False
        if trajectory and trajectory.is_regressing:
            regression = True
            signals.append(
                f"Mastery regression detected: Δ={trajectory.mastery_delta:.3f} over "
                f"{trajectory.sessions_sampled} sessions."
            )
            triggers.append(ReplanningTrigger.REGRESSION)

        # 4. Plateau
        if trajectory and trajectory.is_plateaued:
            signals.append(
                f"Mastery plateau detected: topic '{trajectory.topic_id}' stuck at same tier."
            )
            triggers.append(ReplanningTrigger.PLATEAU)

        # 5. Overload
        overloaded = False
        if recent_task_fail_rate >= cls.OVERLOAD_FAIL_RATE:
            overloaded = True
            signals.append(
                f"Overload signal: {recent_task_fail_rate:.0%} task failure rate in recent sessions."
            )
            triggers.append(ReplanningTrigger.OVERLOAD)

        # 6. Persistent gaps
        if gap_report and len(gap_report.persistent_gap_ids) >= cls.GAP_PERSISTENCE_TRIGGER:
            signals.append(
                f"{len(gap_report.persistent_gap_ids)} knowledge gaps unresolved beyond threshold."
            )
            triggers.append(ReplanningTrigger.GAP_PERSISTENCE)

        # 7. Misconception loop
        if misconception_trend and misconception_trend.recurring_count >= 2:
            signals.append(
                f"Recurring misconceptions in {misconception_trend.recurring_count} topics: "
                f"{', '.join(misconception_trend.recurring_topic_ids[:3])}."
            )
            triggers.append(ReplanningTrigger.MISCONCEPTION_LOOP)

        # Classify health status
        if not triggers:
            health = HealthStatus.HEALTHY
        elif regression:
            health = HealthStatus.REGRESSING
        elif overloaded:
            health = HealthStatus.OVERLOADED
        elif stalled:
            health = HealthStatus.STALLED
        elif len(triggers) >= 3:
            health = HealthStatus.AT_RISK
        elif trajectory and trajectory.is_plateaued:
            health = HealthStatus.PLATEAUED
        else:
            health = HealthStatus.AT_RISK

        # Compute overall velocity
        velocity = trajectory.velocity if trajectory else 0.0

        return LearningHealthReport(
            health_status=health,
            signals=signals,
            triggers_detected=triggers,
            trajectory=trajectory,
            gap_report=gap_report,
            misconception_trend=misconception_trend,
            velocity_topics_per_session=velocity,
        )


# ---------------------------------------------------------------------------
# AdaptiveLearningEngine (Orchestrator)
# ---------------------------------------------------------------------------

class AdaptiveLearningEngine:
    """
    Top-level Phase 6 orchestrator.

    Responsibilities:
    - Accepts learner evidence (mastery history, gaps, misconceptions, sessions)
    - Runs all analyzers to produce a LearningHealthReport
    - Integrates with EventBus to broadcast health alerts and replanning triggers
    - Delegates actual replanning to ReplanningEngine
    """

    def __init__(
        self,
        memory: Optional[Any] = None,       # TarkyaanMemoryManager (optional)
        event_bus: Optional[Any] = None,    # EventBus (optional, defaults to global)
    ) -> None:
        self.memory = memory
        self._event_bus = event_bus

    @property
    def bus(self) -> Any:
        if self._event_bus is None:
            from tarkyaan.events import event_bus as _bus
            return _bus
        return self._event_bus

    def evaluate_learner_health(
        self,
        learner_id: str,
        mastery_history: Optional[List[float]] = None,
        tier_history: Optional[List[str]] = None,
        topic_id: str = "general",
        sessions_since_last_progress: int = 0,
        stall_session_threshold: int = 3,
        recent_task_fail_rate: float = 0.0,
    ) -> LearningHealthReport:
        """
        Evaluate learner health from provided evidence.
        Automatically pulls gaps + misconceptions from memory if memory is available.

        Returns a LearningHealthReport with classified HealthStatus and triggers.
        """
        # 1. Analyze mastery trajectory
        trajectory: Optional[MasteryTrajectory] = None
        if mastery_history:
            trajectory = MasteryTrajectoryAnalyzer.analyze(
                topic_id=topic_id,
                mastery_history=mastery_history,
                tier_history=tier_history,
            )

        # 2. Analyze gap evolution
        gap_report: Optional[GapEvolutionReport] = None
        if self.memory:
            try:
                active_gaps = self.memory.get_knowledge_gaps(learner_id, active_only=True)
                gap_dicts = [g.model_dump() if hasattr(g, "model_dump") else dict(g) for g in active_gaps]
                gap_report = GapEvolutionAnalyzer.analyze(active_gaps=gap_dicts)
            except Exception:
                pass

        # 3. Analyze misconception trends
        misconception_trend: Optional[MisconceptionTrend] = None
        if self.memory:
            try:
                misconceptions = self.memory.get_misconceptions(learner_id)
                misc_dicts = [m.model_dump() if hasattr(m, "model_dump") else dict(m) for m in misconceptions]
                misconception_trend = MisconceptionTrendAnalyzer.analyze(misc_dicts)
            except Exception:
                pass

        # 4. Synthesize health report
        report = LearningHealthAnalyzer.analyze(
            trajectory=trajectory,
            gap_report=gap_report,
            misconception_trend=misconception_trend,
            recent_task_fail_rate=recent_task_fail_rate,
            sessions_since_last_progress=sessions_since_last_progress,
            stall_session_threshold=stall_session_threshold,
        )

        # 5. Publish health event if status is not HEALTHY
        if report.health_status != HealthStatus.HEALTHY:
            try:
                from tarkyaan.events.event_bus import TarkyaanEvent
                self.bus.publish(
                    TarkyaanEvent.HEALTH_ALERT,
                    payload={
                        "health_status": report.health_status,
                        "signals": report.signals,
                        "triggers": [t.value for t in report.triggers_detected],
                    },
                    learner_id=learner_id,
                    source="adaptive_engine",
                )
            except Exception:
                pass

        return report

    def should_replan(self, report: LearningHealthReport) -> Tuple[bool, List[ReplanningTrigger]]:
        """
        Determine whether current evidence warrants an autonomous replan.
        Returns (should_replan, triggers).
        """
        actionable = [
            ReplanningTrigger.STALL,
            ReplanningTrigger.REGRESSION,
            ReplanningTrigger.OVERLOAD,
            ReplanningTrigger.GAP_PERSISTENCE,
            ReplanningTrigger.MISCONCEPTION_LOOP,
            ReplanningTrigger.VELOCITY_DROP,
        ]
        fired = [t for t in report.triggers_detected if t in actionable]
        return len(fired) > 0, fired
