"""Sleep Analysis Service — Architecture, Consistency & Problem Detection.

Trois fonctions pures et stateless :
  1. compute_sleep_architecture_score()  — ratios deep/REM/light vs distribution ideale
  2. compute_sleep_consistency_score()   — variance bedtime/wake_time sur N jours
  3. detect_sleep_problems()             — detection de patterns problematiques

Toutes les fonctions operent sur des listes de dicts representant des SleepSession.
Aucune dependance DB directe.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional


# ── Result dataclasses ──────────────────────────────────────────────────────

@dataclass
class SleepArchitectureResult:
    """Score basé sur la distribution des phases de sommeil."""
    deep_pct: float = 0.0
    rem_pct: float = 0.0
    light_pct: float = 0.0
    awake_pct: float = 0.0
    architecture_score: int = 0   # 0-100
    architecture_quality: str = "unknown"
    areas_to_improve: List[str] = field(default_factory=list)


@dataclass
class SleepConsistencyResult:
    """Score basé sur la régularité des horaires de sommeil."""
    avg_bedtime_hour: Optional[float] = None
    avg_wake_hour: Optional[float] = None
    bedtime_variance_min: float = 0.0
    wake_variance_min: float = 0.0
    consistency_score: int = 0    # 0-100
    consistency_label: str = "unknown"
    sessions_analyzed: int = 0


@dataclass
class SleepProblem:
    """Un problème de sommeil détecté."""
    problem_type: str             # 'chronic_insufficient', 'quality_degradation', etc.
    severity: str                 # 'low', 'moderate', 'high'
    description: str
    recommendation: str
    evidence_days: int = 0


@dataclass
class SleepAnalysisResult:
    """Résultat agrégé des 3 analyses."""
    architecture: Optional[SleepArchitectureResult] = None
    consistency: Optional[SleepConsistencyResult] = None
    problems: List[SleepProblem] = field(default_factory=list)


# ── Architecture scoring ────────────────────────────────────────────────────

# Références OMS / Walker (Why We Sleep) :
#   Deep : 15-25% du temps total
#   REM  : 20-25%
#   Light: 50-60%
#   Awake: < 5%

_IDEAL_DEEP_MIN = 15.0
_IDEAL_DEEP_MAX = 25.0
_IDEAL_REM_MIN = 20.0
_IDEAL_REM_MAX = 25.0
_IDEAL_LIGHT_MIN = 45.0
_IDEAL_LIGHT_MAX = 60.0
_IDEAL_AWAKE_MAX = 5.0


def _score_stage_pct(actual: float, ideal_min: float, ideal_max: float) -> float:
    """Score 0-100 pour un stage. 100 si dans la fourchette ideale, degressif sinon."""
    if ideal_min <= actual <= ideal_max:
        return 100.0
    if actual < ideal_min:
        deficit = ideal_min - actual
        return max(0.0, 100.0 - deficit * 5)
    # actual > ideal_max
    excess = actual - ideal_max
    return max(0.0, 100.0 - excess * 5)


def compute_sleep_architecture_score(
    duration_minutes: Optional[int] = None,
    deep_sleep_minutes: Optional[int] = None,
    rem_sleep_minutes: Optional[int] = None,
    light_sleep_minutes: Optional[int] = None,
    awake_minutes: Optional[int] = None,
) -> SleepArchitectureResult:
    """Analyse la distribution des phases de sommeil.

    Si les phases ne sont pas disponibles, retourne un score par defaut
    base uniquement sur la duree.
    """
    result = SleepArchitectureResult()

    total = duration_minutes or 0
    if total <= 0:
        return result

    deep = deep_sleep_minutes or 0
    rem = rem_sleep_minutes or 0
    light = light_sleep_minutes or 0
    awake = awake_minutes or 0

    # Si aucune phase disponible, score partiel base sur duree
    has_stages = (deep + rem + light) > 0
    if not has_stages:
        if total >= 480:
            result.architecture_score = 75
            result.architecture_quality = "estimated_good"
        elif total >= 420:
            result.architecture_score = 60
            result.architecture_quality = "estimated_fair"
        elif total >= 360:
            result.architecture_score = 45
            result.architecture_quality = "estimated_fair"
        else:
            result.architecture_score = 30
            result.architecture_quality = "estimated_poor"
        result.areas_to_improve.append("sleep_stages_unknown")
        return result

    # Calculer les pourcentages
    total_sleep = deep + rem + light + awake
    if total_sleep <= 0:
        total_sleep = total

    result.deep_pct = round((deep / total_sleep) * 100, 1)
    result.rem_pct = round((rem / total_sleep) * 100, 1)
    result.light_pct = round((light / total_sleep) * 100, 1)
    result.awake_pct = round((awake / total_sleep) * 100, 1)

    # Score composite
    deep_score = _score_stage_pct(result.deep_pct, _IDEAL_DEEP_MIN, _IDEAL_DEEP_MAX)
    rem_score = _score_stage_pct(result.rem_pct, _IDEAL_REM_MIN, _IDEAL_REM_MAX)
    light_score = _score_stage_pct(result.light_pct, _IDEAL_LIGHT_MIN, _IDEAL_LIGHT_MAX)

    # Penalite awake
    awake_penalty = 0.0
    if result.awake_pct > _IDEAL_AWAKE_MAX:
        awake_penalty = min(30.0, (result.awake_pct - _IDEAL_AWAKE_MAX) * 3)

    raw_score = (deep_score * 0.35 + rem_score * 0.35 + light_score * 0.30) - awake_penalty
    result.architecture_score = max(0, min(100, round(raw_score)))

    # Label
    if result.architecture_score >= 80:
        result.architecture_quality = "excellent"
    elif result.architecture_score >= 60:
        result.architecture_quality = "good"
    elif result.architecture_score >= 40:
        result.architecture_quality = "fair"
    else:
        result.architecture_quality = "poor"

    # Areas to improve
    if result.deep_pct < _IDEAL_DEEP_MIN:
        result.areas_to_improve.append("insufficient_deep_sleep")
    if result.rem_pct < _IDEAL_REM_MIN:
        result.areas_to_improve.append("insufficient_rem_sleep")
    if result.awake_pct > _IDEAL_AWAKE_MAX:
        result.areas_to_improve.append("excessive_wake_time")
    if total < 420:
        result.areas_to_improve.append("insufficient_duration")

    return result


# ── Consistency scoring ─────────────────────────────────────────────────────

def _time_to_minutes_from_midnight(dt: datetime) -> float:
    """Convertit un datetime en minutes depuis minuit.

    Gestion des heures apres minuit : si < 12h, ajoute 24h (ex: 01:00 = 1500 min).
    """
    minutes = dt.hour * 60 + dt.minute
    if minutes < 12 * 60:  # avant midi = apres minuit (sommeil)
        minutes += 24 * 60
    return float(minutes)


def _std_dev(values: List[float]) -> float:
    """Ecart-type simple."""
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return math.sqrt(variance)


def compute_sleep_consistency_score(
    sessions: List[dict],
) -> SleepConsistencyResult:
    """Analyse la regularite des horaires de sommeil.

    Args:
        sessions: Liste de dicts avec au minimum 'start_at' et 'end_at'
                  (datetime ou str ISO-8601).

    Seuils :
        stddev < 30 min = excellent (85-100)
        stddev < 60 min = good      (65-84)
        stddev < 90 min = moderate   (45-64)
        stddev >= 90 min = poor      (< 45)
    """
    result = SleepConsistencyResult()

    if len(sessions) < 3:
        result.consistency_label = "insufficient_data"
        result.sessions_analyzed = len(sessions)
        return result

    bedtimes: List[float] = []
    wake_times: List[float] = []

    for s in sessions:
        start = s.get("start_at")
        end = s.get("end_at")
        if not start or not end:
            continue

        if isinstance(start, str):
            start = datetime.fromisoformat(start.replace("Z", "+00:00"))
        if isinstance(end, str):
            end = datetime.fromisoformat(end.replace("Z", "+00:00"))

        bedtimes.append(_time_to_minutes_from_midnight(start))
        wake_times.append(end.hour * 60 + end.minute)

    if len(bedtimes) < 3:
        result.consistency_label = "insufficient_data"
        result.sessions_analyzed = len(bedtimes)
        return result

    result.sessions_analyzed = len(bedtimes)

    # Average times
    avg_bed = sum(bedtimes) / len(bedtimes)
    avg_wake = sum(wake_times) / len(wake_times)
    result.avg_bedtime_hour = round((avg_bed % (24 * 60)) / 60, 2)
    result.avg_wake_hour = round(avg_wake / 60, 2)

    # Variance
    bed_std = _std_dev(bedtimes)
    wake_std = _std_dev(wake_times)
    result.bedtime_variance_min = round(bed_std, 1)
    result.wake_variance_min = round(wake_std, 1)

    # Score based on average of both variances
    avg_variance = (bed_std + wake_std) / 2

    if avg_variance < 30:
        result.consistency_score = min(100, round(100 - avg_variance * 0.5))
        result.consistency_label = "excellent"
    elif avg_variance < 60:
        result.consistency_score = round(84 - (avg_variance - 30) * 0.63)
        result.consistency_label = "good"
    elif avg_variance < 90:
        result.consistency_score = round(64 - (avg_variance - 60) * 0.63)
        result.consistency_label = "moderate"
    else:
        result.consistency_score = max(0, round(44 - (avg_variance - 90) * 0.5))
        result.consistency_label = "poor"

    return result


# ── Problem detection ───────────────────────────────────────────────────────

def detect_sleep_problems(
    sessions: List[dict],
) -> List[SleepProblem]:
    """Detecte des patterns problematiques de sommeil sur 14-30 jours.

    Args:
        sessions: Liste de dicts avec 'start_at', 'end_at', 'duration_minutes',
                  'perceived_quality', 'deep_sleep_minutes', 'awake_minutes'.

    Patterns detectes :
        1. Sommeil chroniquement insuffisant (< 6h sur 7+ jours)
        2. Degradation de la qualite percue (tendance descendante)
        3. Coucher tardif (moyenne apres 00:30)
        4. Sommeil fragmente (awake_minutes eleve)
        5. Deep sleep insuffisant (< 10% de facon repetee)
    """
    problems: List[SleepProblem] = []

    if len(sessions) < 5:
        return problems

    # ── 1. Chronic insufficient sleep ──────────────────────────────────────
    durations = [s.get("duration_minutes", 0) or 0 for s in sessions]
    short_nights = sum(1 for d in durations if 0 < d < 360)  # < 6h
    if short_nights >= 7:
        problems.append(SleepProblem(
            problem_type="chronic_insufficient",
            severity="high",
            description=f"{short_nights} nuits de moins de 6 heures detectees.",
            recommendation="Viser 7-8 heures de sommeil par nuit. Fixer une heure de coucher reguliere.",
            evidence_days=short_nights,
        ))
    elif short_nights >= 4:
        problems.append(SleepProblem(
            problem_type="chronic_insufficient",
            severity="moderate",
            description=f"{short_nights} nuits de moins de 6 heures detectees.",
            recommendation="Augmenter progressivement la duree de sommeil de 15-30 min par semaine.",
            evidence_days=short_nights,
        ))

    # ── 2. Quality degradation trend ───────────────────────────────────────
    qualities = [s.get("perceived_quality") for s in sessions if s.get("perceived_quality") is not None]
    if len(qualities) >= 5:
        recent_half = qualities[:len(qualities) // 2]  # plus recent
        older_half = qualities[len(qualities) // 2:]    # plus ancien
        recent_avg = sum(recent_half) / len(recent_half)
        older_avg = sum(older_half) / len(older_half)
        if recent_avg < older_avg - 0.8:  # baisse significative
            problems.append(SleepProblem(
                problem_type="quality_degradation",
                severity="moderate",
                description=f"Qualite percue en baisse : {older_avg:.1f} → {recent_avg:.1f}/5.",
                recommendation="Identifier les facteurs perturbants : stress, ecrans, cafeine apres 14h.",
                evidence_days=len(qualities),
            ))

    # ── 3. Late bedtime pattern ────────────────────────────────────────────
    bedtime_hours: List[float] = []
    for s in sessions:
        start = s.get("start_at")
        if not start:
            continue
        if isinstance(start, str):
            start = datetime.fromisoformat(start.replace("Z", "+00:00"))
        h = start.hour + start.minute / 60
        # Normaliser : avant 12h = apres minuit
        if h < 12:
            h += 24
        bedtime_hours.append(h)

    if bedtime_hours:
        avg_bedtime = sum(bedtime_hours) / len(bedtime_hours)
        if avg_bedtime > 24.5:  # apres 00:30
            problems.append(SleepProblem(
                problem_type="late_bedtime",
                severity="moderate" if avg_bedtime > 25.0 else "low",
                description=f"Heure de coucher moyenne tardive : {int(avg_bedtime % 24)}h{int((avg_bedtime % 1) * 60):02d}.",
                recommendation="Avancer l'heure de coucher de 15 min chaque semaine pour atteindre 23h.",
                evidence_days=len(bedtime_hours),
            ))

    # ── 4. Fragmented sleep ────────────────────────────────────────────────
    awake_sessions = [
        s.get("awake_minutes", 0) or 0
        for s in sessions
        if s.get("awake_minutes") is not None and s.get("awake_minutes", 0) > 0
    ]
    if len(awake_sessions) >= 5:
        avg_awake = sum(awake_sessions) / len(awake_sessions)
        if avg_awake > 30:
            problems.append(SleepProblem(
                problem_type="fragmented_sleep",
                severity="high" if avg_awake > 45 else "moderate",
                description=f"Temps eveille moyen de {avg_awake:.0f} min pendant la nuit.",
                recommendation="Reduire les stimulants, maintenir la chambre sombre et fraiche (18-20°C).",
                evidence_days=len(awake_sessions),
            ))

    # ── 5. Insufficient deep sleep ─────────────────────────────────────────
    deep_pcts: List[float] = []
    for s in sessions:
        dur = s.get("duration_minutes", 0) or 0
        deep = s.get("deep_sleep_minutes", 0) or 0
        if dur > 0 and deep > 0:
            deep_pcts.append((deep / dur) * 100)

    if len(deep_pcts) >= 5:
        avg_deep_pct = sum(deep_pcts) / len(deep_pcts)
        if avg_deep_pct < 10:
            problems.append(SleepProblem(
                problem_type="insufficient_deep_sleep",
                severity="moderate",
                description=f"Sommeil profond moyen de {avg_deep_pct:.1f}% (ideal: 15-25%).",
                recommendation="Exercice physique regulier, eviter l'alcool le soir, temperature fraiche.",
                evidence_days=len(deep_pcts),
            ))

    return problems


# ── Helpers pour serialisation ──────────────────────────────────────────────

def architecture_to_dict(result: SleepArchitectureResult) -> dict:
    return asdict(result)

def consistency_to_dict(result: SleepConsistencyResult) -> dict:
    return asdict(result)

def problem_to_dict(problem: SleepProblem) -> dict:
    return asdict(problem)

def analysis_to_dict(result: SleepAnalysisResult) -> dict:
    return {
        "architecture": architecture_to_dict(result.architecture) if result.architecture else None,
        "consistency": consistency_to_dict(result.consistency) if result.consistency else None,
        "problems": [problem_to_dict(p) for p in result.problems],
    }
