"""
Motion Intelligence Engine — LOT 11.

Aggregates VisionSessions to compute movement health scores and trends.

Algorithms:
  _trend(values)          : slope of simple linear regression (>0.3 = improving)
  asymmetry_score         : proxy via std of stability + amplitude values × 3
  movement_health_score   : 0.40 × stability + 0.40 × mobility + 0.20 × (100 - asymmetry)
  confidence              : sessions_analyzed / 20, capped at 1.0

Per-exercise profiles are computed independently. Global scores aggregate all exercises.

All compute functions are pure and have no DB access.
"""
from __future__ import annotations

import uuid
import logging
import statistics
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

logger = logging.getLogger(__name__)

# ── Thresholds ────────────────────────────────────────────────────────────────

TREND_SLOPE_IMPROVING = 0.3      # score units/session
TREND_SLOPE_DECLINING = -0.3
QUALITY_GOOD_THRESHOLD = 70.0    # quality score considered "good"
LOW_SCORE_ALERT = 55.0           # alert when component < this
CONFIDENCE_SESSION_TARGET = 20   # sessions for full confidence


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class ExerciseMotionProfile:
    """Movement quality profile for a single exercise type."""
    exercise_type: str
    sessions_analyzed: int
    avg_stability: float        # 0-100
    avg_amplitude: float        # 0-100
    avg_quality: float          # 0-100
    stability_trend: str        # "improving" | "stable" | "declining"
    amplitude_trend: str
    quality_trend: str
    quality_variance: float     # std deviation (high = inconsistent)
    last_session_date: Optional[date]
    alerts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "exercise_type": self.exercise_type,
            "sessions_analyzed": self.sessions_analyzed,
            "avg_stability": self.avg_stability,
            "avg_amplitude": self.avg_amplitude,
            "avg_quality": self.avg_quality,
            "stability_trend": self.stability_trend,
            "amplitude_trend": self.amplitude_trend,
            "quality_trend": self.quality_trend,
            "quality_variance": self.quality_variance,
            "last_session_date": self.last_session_date.isoformat() if self.last_session_date else None,
            "alerts": self.alerts,
        }


@dataclass
class MotionIntelligenceResult:
    """Global motion intelligence analysis result."""
    analysis_date: date
    sessions_analyzed: int
    days_analyzed: int
    movement_health_score: float        # 0-100 composite
    stability_score: float              # global avg stability
    mobility_score: float               # global avg amplitude (proxy mobility)
    asymmetry_score: float              # 0-100 (higher = more asymmetric)
    overall_quality_trend: str          # "improving" | "stable" | "declining"
    consecutive_quality_sessions: int   # streak of quality_score >= 70
    exercise_profiles: dict[str, ExerciseMotionProfile] = field(default_factory=dict)
    recommendations: list[str] = field(default_factory=list)
    risk_alerts: list[str] = field(default_factory=list)
    confidence: float = 0.0


# ── Input DTO (plain dict from DB rows) ──────────────────────────────────────

@dataclass
class SessionData:
    """Lightweight representation of a VisionSession for computation."""
    exercise_type: str
    session_date: date
    stability_score: Optional[float]
    amplitude_score: Optional[float]
    quality_score: Optional[float]
    rep_count: int = 0


# ── Core algorithms ───────────────────────────────────────────────────────────

def _trend(values: list[float]) -> str:
    """
    Compute trend direction via simple linear regression slope.

    slope > 0.3  → "improving"
    slope < -0.3 → "declining"
    else         → "stable"
    """
    n = len(values)
    if n < 2:
        return "stable"

    x_mean = (n - 1) / 2.0
    y_mean = sum(values) / n
    numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
    denominator = sum((i - x_mean) ** 2 for i in range(n))

    if denominator == 0:
        return "stable"

    slope = numerator / denominator

    if slope > TREND_SLOPE_IMPROVING:
        return "improving"
    if slope < TREND_SLOPE_DECLINING:
        return "declining"
    return "stable"


def _safe_mean(values: list[float]) -> float:
    """Mean of a non-empty list, 0.0 if empty."""
    return statistics.mean(values) if values else 0.0


def _safe_std(values: list[float]) -> float:
    """Population std dev, 0.0 if fewer than 2 values."""
    return statistics.pstdev(values) if len(values) >= 2 else 0.0


def _asymmetry_score(
    stability_values: list[float],
    amplitude_values: list[float],
) -> float:
    """
    Proxy asymmetry score via variance in biomechanical scores.

    asymmetry = min(100, mean([std(stability), std(amplitude)]) × 3)
    0 = perfectly consistent (symmetric), 100 = highly variable.
    """
    std_stability = _safe_std(stability_values)
    std_amplitude = _safe_std(amplitude_values)

    stds = []
    if stability_values:
        stds.append(std_stability)
    if amplitude_values:
        stds.append(std_amplitude)

    if not stds:
        return 0.0

    return round(min(100.0, _safe_mean(stds) * 3.0), 1)


def _consecutive_quality_sessions(
    sessions: list[SessionData],
    threshold: float = QUALITY_GOOD_THRESHOLD,
) -> int:
    """
    Count consecutive sessions (most recent first) with quality_score >= threshold.
    Sessions ordered by date ascending; we iterate from most recent.
    """
    ordered = sorted(sessions, key=lambda s: s.session_date, reverse=True)
    streak = 0
    for s in ordered:
        if s.quality_score is not None and s.quality_score >= threshold:
            streak += 1
        else:
            break
    return streak


def _build_exercise_profile(
    exercise_type: str,
    sessions: list[SessionData],
) -> ExerciseMotionProfile:
    """Build a motion profile for a single exercise type."""
    # Chronological order for trend computation
    ordered = sorted(sessions, key=lambda s: s.session_date)

    stability_vals = [s.stability_score for s in ordered if s.stability_score is not None]
    amplitude_vals = [s.amplitude_score for s in ordered if s.amplitude_score is not None]
    quality_vals = [s.quality_score for s in ordered if s.quality_score is not None]

    avg_stability = round(_safe_mean(stability_vals), 1)
    avg_amplitude = round(_safe_mean(amplitude_vals), 1)
    avg_quality = round(_safe_mean(quality_vals), 1)
    quality_variance = round(_safe_std(quality_vals), 1)

    last_date = max((s.session_date for s in sessions), default=None)

    alerts: list[str] = []
    if avg_stability < LOW_SCORE_ALERT and stability_vals:
        alerts.append(f"Stabilité faible ({avg_stability:.0f}/100) — vérifier la technique")
    if avg_amplitude < LOW_SCORE_ALERT and amplitude_vals:
        alerts.append(f"Amplitude insuffisante ({avg_amplitude:.0f}/100) — amplitude incomplète détectée")
    if quality_variance > 20 and quality_vals:
        alerts.append(f"Qualité irrégulière (σ={quality_variance:.1f}) — manque de consistance")
    if _trend(quality_vals) == "declining":
        alerts.append("Tendance qualitative en baisse — évaluer surcharge ou fatigue")

    return ExerciseMotionProfile(
        exercise_type=exercise_type,
        sessions_analyzed=len(sessions),
        avg_stability=avg_stability,
        avg_amplitude=avg_amplitude,
        avg_quality=avg_quality,
        stability_trend=_trend(stability_vals),
        amplitude_trend=_trend(amplitude_vals),
        quality_trend=_trend(quality_vals),
        quality_variance=quality_variance,
        last_session_date=last_date,
        alerts=alerts,
    )


def _generate_recommendations(
    movement_health_score: float,
    asymmetry_score: float,
    stability_score: float,
    mobility_score: float,
    overall_quality_trend: str,
    exercise_profiles: dict[str, ExerciseMotionProfile],
) -> list[str]:
    """Generate actionable recommendations from motion data."""
    recs = []

    if movement_health_score >= 80:
        recs.append("Qualité de mouvement excellente — continuer sur cette lancée")
    elif movement_health_score >= 60:
        recs.append("Qualité de mouvement satisfaisante — cibler les exercices sous 70")
    else:
        recs.append("Qualité de mouvement à améliorer — réduire la charge et se concentrer sur la technique")

    if asymmetry_score > 30:
        recs.append(
            f"Asymétrie détectée ({asymmetry_score:.0f}/100) — "
            "intégrer des exercices unila­téraux pour équilibrer"
        )

    if stability_score < 60:
        recs.append(
            "Stabilité globale faible — intégrer du gainage et des exercices proprioceptifs"
        )

    if mobility_score < 60:
        recs.append(
            "Mobilité réduite — ajouter des étirements dynamiques et travail d'amplitude"
        )

    if overall_quality_trend == "declining":
        recs.append(
            "Tendance globale en baisse — envisager une semaine de récupération active"
        )
    elif overall_quality_trend == "improving":
        recs.append("Progression constante détectée — maintenir le programme actuel")

    return recs[:4]  # max 4 recommendations


def _generate_risk_alerts(
    exercise_profiles: dict[str, ExerciseMotionProfile],
    asymmetry_score: float,
    consecutive_poor_quality: int = 0,
) -> list[str]:
    """Generate risk alerts from motion patterns."""
    alerts = []

    for profile in exercise_profiles.values():
        alerts.extend(profile.alerts)

    if asymmetry_score > 50:
        alerts.append(
            f"⚠️ Asymétrie élevée ({asymmetry_score:.0f}/100) — "
            "risque de déséquilibre musculaire à corriger"
        )

    return alerts[:5]  # cap at 5 alerts


# ── Core compute function (pure) ──────────────────────────────────────────────

def compute_motion_intelligence(
    sessions: list[SessionData],
    analysis_date: Optional[date] = None,
    days_analyzed: int = 30,
) -> MotionIntelligenceResult:
    """
    Compute motion intelligence from a list of VisionSession data.

    Pure function — accepts SessionData DTOs, not SQLAlchemy models.
    Handles empty sessions gracefully (confidence=0.0, all scores=0.0).

    Args:
        sessions: List of SessionData from VisionSession DB rows.
        analysis_date: Date of analysis (default: today).
        days_analyzed: Window of days analyzed (for display).

    Returns:
        MotionIntelligenceResult with global scores and per-exercise profiles.
    """
    today = analysis_date or date.today()

    if not sessions:
        return MotionIntelligenceResult(
            analysis_date=today,
            sessions_analyzed=0,
            days_analyzed=days_analyzed,
            movement_health_score=0.0,
            stability_score=0.0,
            mobility_score=0.0,
            asymmetry_score=0.0,
            overall_quality_trend="stable",
            consecutive_quality_sessions=0,
            exercise_profiles={},
            recommendations=["Aucune session CV enregistrée — commencez une analyse de mouvement"],
            risk_alerts=[],
            confidence=0.0,
        )

    # Group sessions by exercise type
    by_exercise: dict[str, list[SessionData]] = {}
    for s in sessions:
        by_exercise.setdefault(s.exercise_type, []).append(s)

    # Build per-exercise profiles
    exercise_profiles = {
        ex: _build_exercise_profile(ex, slist)
        for ex, slist in by_exercise.items()
    }

    # Global biomechanical scores (across all sessions)
    all_stability = [s.stability_score for s in sessions if s.stability_score is not None]
    all_amplitude = [s.amplitude_score for s in sessions if s.amplitude_score is not None]
    all_quality = [s.quality_score for s in sessions if s.quality_score is not None]

    global_stability = round(_safe_mean(all_stability), 1)
    global_mobility = round(_safe_mean(all_amplitude), 1)   # amplitude = mobility proxy
    global_asymmetry = _asymmetry_score(all_stability, all_amplitude)

    # Movement health composite score
    # Requires at least some data; else 0
    if all_stability or all_amplitude:
        movement_health = (
            0.40 * global_stability
            + 0.40 * global_mobility
            + 0.20 * (100.0 - global_asymmetry)
        )
        movement_health = round(max(0.0, min(100.0, movement_health)), 1)
    else:
        movement_health = 0.0

    # Overall quality trend (chronological)
    ordered_quality = [
        s.quality_score
        for s in sorted(sessions, key=lambda s: s.session_date)
        if s.quality_score is not None
    ]
    overall_quality_trend = _trend(ordered_quality)

    # Consecutive quality sessions streak
    streak = _consecutive_quality_sessions(sessions)

    # Confidence
    confidence = round(min(1.0, len(sessions) / CONFIDENCE_SESSION_TARGET), 2)

    # Recommendations and alerts
    recommendations = _generate_recommendations(
        movement_health, global_asymmetry, global_stability, global_mobility,
        overall_quality_trend, exercise_profiles,
    )
    risk_alerts = _generate_risk_alerts(exercise_profiles, global_asymmetry)

    return MotionIntelligenceResult(
        analysis_date=today,
        sessions_analyzed=len(sessions),
        days_analyzed=days_analyzed,
        movement_health_score=movement_health,
        stability_score=global_stability,
        mobility_score=global_mobility,
        asymmetry_score=global_asymmetry,
        overall_quality_trend=overall_quality_trend,
        consecutive_quality_sessions=streak,
        exercise_profiles=exercise_profiles,
        recommendations=recommendations,
        risk_alerts=risk_alerts,
        confidence=confidence,
    )


# ── Persistence helpers ───────────────────────────────────────────────────────

async def save_motion_intelligence(
    db: AsyncSession,
    user_id: uuid.UUID,
    result: MotionIntelligenceResult,
) -> None:
    """Upsert MotionIntelligenceSnapshot for today."""
    from app.models.advanced import MotionIntelligenceSnapshot

    stmt = pg_insert(MotionIntelligenceSnapshot).values(
        user_id=user_id,
        snapshot_date=result.analysis_date,
        movement_health_score=result.movement_health_score,
        stability_score=result.stability_score,
        mobility_score=result.mobility_score,
        asymmetry_score=result.asymmetry_score,
        overall_quality_trend=result.overall_quality_trend,
        sessions_analyzed=result.sessions_analyzed,
        days_analyzed=result.days_analyzed,
        exercise_profiles={k: v.to_dict() for k, v in result.exercise_profiles.items()},
        recommendations=result.recommendations,
        risk_alerts=result.risk_alerts,
        confidence=result.confidence,
    ).on_conflict_do_update(
        constraint="uq_motion_intelligence_user_date",
        set_={
            "movement_health_score": result.movement_health_score,
            "stability_score": result.stability_score,
            "mobility_score": result.mobility_score,
            "asymmetry_score": result.asymmetry_score,
            "overall_quality_trend": result.overall_quality_trend,
            "sessions_analyzed": result.sessions_analyzed,
            "days_analyzed": result.days_analyzed,
            "exercise_profiles": {k: v.to_dict() for k, v in result.exercise_profiles.items()},
            "recommendations": result.recommendations,
            "risk_alerts": result.risk_alerts,
            "confidence": result.confidence,
        },
    )
    await db.execute(stmt)
    await db.commit()


def build_motion_summary(result: MotionIntelligenceResult) -> str:
    """Compact text for coach context builder."""
    if result.sessions_analyzed == 0:
        return "Aucune session CV disponible."

    alert_text = f" Alertes: {result.risk_alerts[0]}" if result.risk_alerts else ""
    return (
        f"Santé du mouvement: {result.movement_health_score:.0f}/100 "
        f"(stabilité {result.stability_score:.0f}, mobilité {result.mobility_score:.0f}, "
        f"asymétrie {result.asymmetry_score:.0f}). "
        f"Trend: {result.overall_quality_trend}. "
        f"Confiance: {result.confidence:.0%}.{alert_text}"
    )
