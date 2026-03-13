"""
Context Builder — SOMA LOT 9.

Assemble le contexte envoyé au LLM (Claude Coach).
Le LLM ne lit jamais directement la base de données.
Ce module est la seule passerelle entre la DB et le LLM.

Limite : ≤ 1500 tokens estimés (≈ 6000 caractères).
"""
import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional
import uuid

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.metrics import DailyMetrics
from app.models.scores import LongevityScore, ReadinessScore
from app.models.vision_session import VisionSession
from app.models.workout import WorkoutSession
from app.models.insights import Insight
from app.services.metabolic_twin_service import MetabolicState, get_or_compute_metabolic_state

logger = logging.getLogger(__name__)

# Limite caractères pour le contexte envoyé au LLM (≈ 1500 tokens)
_MAX_CONTEXT_CHARS = 6_000


# ── Structure de données ──────────────────────────────────────────────────────

@dataclass
class UserProfileContext:
    age: Optional[int] = None
    sex: Optional[str] = None
    primary_goal: Optional[str] = None
    activity_level: Optional[str] = None
    fitness_level: Optional[str] = None
    dietary_regime: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None


@dataclass
class NutritionContext:
    calories_consumed: Optional[float] = None
    calories_target: Optional[float] = None
    protein_g: Optional[float] = None
    protein_target_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    fiber_g: Optional[float] = None
    hydration_ml: Optional[float] = None
    hydration_target_ml: Optional[float] = None


@dataclass
class TrainingContext:
    workout_count_today: int = 0
    training_load_7d: Optional[float] = None
    recommended_intensity: Optional[str] = None
    last_workout_type: Optional[str] = None
    vision_sessions_7d: int = 0
    avg_quality_score_7d: Optional[float] = None


@dataclass
class SleepContext:
    sleep_minutes: Optional[int] = None
    sleep_score: Optional[float] = None
    sleep_quality_label: Optional[str] = None


@dataclass
class CoachContext:
    """Contexte complet assemblé pour le LLM."""
    user: UserProfileContext = field(default_factory=UserProfileContext)
    today_date: str = ""
    readiness_score: Optional[float] = None
    readiness_level: Optional[str] = None
    nutrition: NutritionContext = field(default_factory=NutritionContext)
    training: TrainingContext = field(default_factory=TrainingContext)
    sleep: SleepContext = field(default_factory=SleepContext)
    metabolic: Optional[MetabolicState] = None
    active_alerts: list[str] = field(default_factory=list)
    top_insights: list[str] = field(default_factory=list)
    biological_age: Optional[float] = None
    longevity_score: Optional[float] = None
    # LOT 11 — Advanced Intelligence summaries (compact strings)
    twin_summary: Optional[str] = None
    bio_age_summary: Optional[str] = None
    adaptive_nutrition_summary: Optional[str] = None
    motion_summary: Optional[str] = None
    # LOT 13-16 — Personalized Learning + Injury + Biomarkers + Coach Platform
    learning_summary: Optional[str] = None
    injury_risk_summary: Optional[str] = None
    biomarker_summary: Optional[str] = None
    athlete_context: Optional[str] = None
    # LOT 18 — Twin key signals (top 3 composantes avec valeur + statut)
    twin_key_signals: Optional[str] = None

    def to_prompt_text(self) -> str:
        """
        Sérialise le contexte en texte structuré pour le LLM.
        Respecte la limite de ~1500 tokens.
        """
        lines: list[str] = []

        # ── En-tête ────────────────────────────────────────────────────────
        lines.append(f"=== PROFIL UTILISATEUR ({self.today_date}) ===")
        u = self.user
        parts = []
        if u.age:
            parts.append(f"{u.age} ans")
        if u.sex:
            parts.append(u.sex)
        if u.height_cm and u.weight_kg:
            parts.append(f"{u.height_cm}cm / {u.weight_kg}kg")
        if u.primary_goal:
            parts.append(f"objectif={u.primary_goal}")
        if u.activity_level:
            parts.append(f"activité={u.activity_level}")
        if u.dietary_regime:
            parts.append(f"régime={u.dietary_regime}")
        lines.append(", ".join(parts) if parts else "(profil incomplet)")
        lines.append("")

        # ── Récupération ───────────────────────────────────────────────────
        lines.append("=== RÉCUPÉRATION ===")
        if self.readiness_score is not None:
            lines.append(f"Readiness : {self.readiness_score:.0f}/100 ({self.readiness_level or '?'})")
        m = self.metabolic
        if m:
            if m.fatigue_score is not None:
                lines.append(f"Fatigue : {m.fatigue_score:.0f}/100")
            if m.stress_load is not None:
                lines.append(f"Stress global : {m.stress_load:.0f}/100")
            if m.glycogen_status != "unknown":
                lines.append(f"Glycogène : {m.glycogen_status}"
                             + (f" ({m.estimated_glycogen_g:.0f}g)" if m.estimated_glycogen_g else ""))
            if m.plateau_risk:
                lines.append("⚠ Risque de plateau détecté (14j)")
        lines.append("")

        # ── Sommeil ────────────────────────────────────────────────────────
        lines.append("=== SOMMEIL ===")
        s = self.sleep
        if s.sleep_minutes:
            h, mn = divmod(s.sleep_minutes, 60)
            lines.append(f"Durée : {h}h{mn:02d}")
        if s.sleep_score is not None:
            lines.append(f"Score sommeil : {s.sleep_score:.0f}/100")
        if s.sleep_quality_label:
            lines.append(f"Qualité : {s.sleep_quality_label}")
        lines.append("")

        # ── Nutrition ──────────────────────────────────────────────────────
        lines.append("=== NUTRITION ===")
        n = self.nutrition
        if n.calories_consumed is not None:
            tgt = f"/{n.calories_target:.0f}" if n.calories_target else ""
            lines.append(f"Calories : {n.calories_consumed:.0f}{tgt} kcal")
        if n.protein_g is not None:
            tgt = f"/{n.protein_target_g:.0f}" if n.protein_target_g else ""
            lines.append(f"Protéines : {n.protein_g:.0f}{tgt} g")
        if n.carbs_g is not None:
            lines.append(f"Glucides : {n.carbs_g:.0f} g")
        if n.fat_g is not None:
            lines.append(f"Lipides : {n.fat_g:.0f} g")
        if n.hydration_ml is not None:
            tgt = f"/{n.hydration_target_ml:.0f}" if n.hydration_target_ml else ""
            lines.append(f"Hydratation : {n.hydration_ml:.0f}{tgt} ml")
        if m:
            if m.protein_status != "unknown":
                lines.append(f"Statut protéines : {m.protein_status}")
            if m.hydration_status != "unknown":
                lines.append(f"Statut hydratation : {m.hydration_status}")
            if m.energy_balance_kcal is not None:
                sign = "+" if m.energy_balance_kcal >= 0 else ""
                lines.append(f"Bilan énergétique : {sign}{m.energy_balance_kcal:.0f} kcal")
        lines.append("")

        # ── Entraînement ───────────────────────────────────────────────────
        lines.append("=== ENTRAÎNEMENT ===")
        t = self.training
        lines.append(f"Séances aujourd'hui : {t.workout_count_today}")
        if t.training_load_7d is not None:
            lines.append(f"Charge 7j : {t.training_load_7d:.0f}")
        if t.recommended_intensity:
            lines.append(f"Intensité recommandée : {t.recommended_intensity}")
        if t.vision_sessions_7d:
            lines.append(f"Sessions vision 7j : {t.vision_sessions_7d}"
                         + (f" (qualité moy. {t.avg_quality_score_7d:.0f}/100)"
                            if t.avg_quality_score_7d else ""))
        lines.append("")

        # ── Longévité ──────────────────────────────────────────────────────
        if self.longevity_score is not None or self.biological_age is not None:
            lines.append("=== LONGÉVITÉ ===")
            if self.longevity_score is not None:
                lines.append(f"Score longévité : {self.longevity_score:.0f}/100")
            if self.biological_age is not None:
                lines.append(f"Âge métabolique estimé : {self.biological_age:.1f} ans")
            if m and m.metabolic_age is not None:
                lines.append(f"Âge métabolique (twin) : {m.metabolic_age:.1f} ans")
            lines.append("")

        # ── Alertes ────────────────────────────────────────────────────────
        if self.active_alerts:
            lines.append("=== ALERTES ACTIVES ===")
            for a in self.active_alerts[:3]:
                lines.append(f"⚠ {a}")
            lines.append("")

        # ── Insights clés ──────────────────────────────────────────────────
        if self.top_insights:
            lines.append("=== INSIGHTS RÉCENTS ===")
            for ins in self.top_insights[:3]:
                lines.append(f"• {ins}")
            lines.append("")

        # ── LOT 11 : Intelligence avancée ──────────────────────────────────
        if self.twin_summary:
            lines.append("=== JUMEAU NUMÉRIQUE ===")
            lines.append(self.twin_summary)
            lines.append("")

        if self.twin_key_signals:
            lines.append("=== SIGNAUX CLÉS JUMEAU ===")
            lines.append(self.twin_key_signals)
            lines.append("")

        if self.bio_age_summary:
            lines.append("=== ÂGE BIOLOGIQUE ===")
            lines.append(self.bio_age_summary)
            lines.append("")

        if self.adaptive_nutrition_summary:
            lines.append("=== NUTRITION ADAPTATIVE ===")
            lines.append(self.adaptive_nutrition_summary)
            lines.append("")

        if self.motion_summary:
            lines.append("=== MOUVEMENT & BIOMÉCANIQUE ===")
            lines.append(self.motion_summary)
            lines.append("")

        # LOT 13-16 : Profil Appris + Risque Blessure + Biomarqueurs + Coach
        if self.learning_summary:
            lines.append("=== PROFIL APPRIS ===")
            lines.append(self.learning_summary)
            lines.append("")

        if self.injury_risk_summary:
            lines.append("=== RISQUE BLESSURE ===")
            lines.append(self.injury_risk_summary)
            lines.append("")

        if self.biomarker_summary:
            lines.append("=== BIOMARQUEURS LAB ===")
            lines.append(self.biomarker_summary)
            lines.append("")

        if self.athlete_context:
            lines.append("=== CONTEXTE ATHÈTE (COACH) ===")
            lines.append(self.athlete_context)
            lines.append("")

        text = "\n".join(lines)
        # Tronquage de sécurité
        if len(text) > _MAX_CONTEXT_CHARS:
            text = text[:_MAX_CONTEXT_CHARS] + "\n[contexte tronqué]"
        return text


# ── Assemblage DB ─────────────────────────────────────────────────────────────

async def build_coach_context(
    db: AsyncSession,
    user_id: uuid.UUID,
    profile,
    target_date: Optional[date] = None,
) -> CoachContext:
    """
    Lit toutes les sources de données et assemble un CoachContext.
    Seule fonction qui touche la DB côté contexte.
    """
    target_date = target_date or date.today()
    ctx = CoachContext(today_date=target_date.isoformat())

    # ── Profil utilisateur ─────────────────────────────────────────────────
    if profile:
        ctx.user = UserProfileContext(
            age=profile.age,
            sex=profile.sex,
            primary_goal=profile.primary_goal,
            activity_level=profile.activity_level,
            fitness_level=profile.fitness_level,
            dietary_regime=profile.dietary_regime,
            height_cm=profile.height_cm,
            weight_kg=getattr(profile, "weight_kg", None),
        )

    # ── Métriques du jour ─────────────────────────────────────────────────
    m_res = await db.execute(
        select(DailyMetrics).where(
            and_(
                DailyMetrics.user_id == user_id,
                DailyMetrics.metrics_date == target_date,
            )
        )
    )
    metrics = m_res.scalar_one_or_none()

    if metrics:
        ctx.nutrition = NutritionContext(
            calories_consumed=metrics.calories_consumed,
            calories_target=metrics.calories_target,
            protein_g=metrics.protein_g,
            protein_target_g=metrics.protein_target_g,
            carbs_g=metrics.carbs_g,
            fat_g=metrics.fat_g,
            fiber_g=metrics.fiber_g,
            hydration_ml=metrics.hydration_ml,
            hydration_target_ml=metrics.hydration_target_ml,
        )
        ctx.sleep = SleepContext(
            sleep_minutes=metrics.sleep_minutes,
            sleep_score=metrics.sleep_score,
            sleep_quality_label=metrics.sleep_quality_label,
        )
        ctx.training.workout_count_today = metrics.workout_count or 0
        ctx.training.training_load_7d = metrics.training_load

    # ── Readiness ─────────────────────────────────────────────────────────
    r_res = await db.execute(
        select(ReadinessScore).where(
            and_(
                ReadinessScore.user_id == user_id,
                ReadinessScore.score_date == target_date,
            )
        )
    )
    readiness = r_res.scalar_one_or_none()
    if readiness:
        ctx.readiness_score = readiness.overall_readiness
        ctx.training.recommended_intensity = readiness.recommended_intensity
        # Niveau textuel
        score = readiness.overall_readiness or 0
        if score >= 80:
            ctx.readiness_level = "excellent"
        elif score >= 60:
            ctx.readiness_level = "bon"
        elif score >= 40:
            ctx.readiness_level = "moyen"
        else:
            ctx.readiness_level = "faible"

    # ── Longévité ─────────────────────────────────────────────────────────
    lon_res = await db.execute(
        select(LongevityScore)
        .where(LongevityScore.user_id == user_id)
        .order_by(LongevityScore.score_date.desc())
        .limit(1)
    )
    lon = lon_res.scalar_one_or_none()
    if lon:
        ctx.longevity_score = lon.longevity_score
        ctx.biological_age = lon.biological_age_estimate

    # ── Vision (7 derniers jours) ─────────────────────────────────────────
    since_7 = target_date - timedelta(days=7)
    vis_res = await db.execute(
        select(VisionSession).where(
            and_(
                VisionSession.user_id == user_id,
                VisionSession.session_date >= since_7,
            )
        )
    )
    vision_sessions = vis_res.scalars().all()
    ctx.training.vision_sessions_7d = len(vision_sessions)
    if vision_sessions:
        scores = [v.quality_score for v in vision_sessions if v.quality_score is not None]
        ctx.training.avg_quality_score_7d = sum(scores) / len(scores) if scores else None

    # ── Insights non-lus (≤ 3) ────────────────────────────────────────────
    ins_res = await db.execute(
        select(Insight).where(
            and_(
                Insight.user_id == user_id,
                Insight.is_read.is_(False),
                Insight.is_dismissed.is_(False),
            )
        )
        .order_by(Insight.created_at.desc())
        .limit(5)
    )
    insights = ins_res.scalars().all()
    ctx.top_insights = [ins.message for ins in insights[:3]]

    # ── Metabolic Twin ────────────────────────────────────────────────────
    try:
        metabolic = await get_or_compute_metabolic_state(
            db, user_id, profile, target_date
        )
        ctx.metabolic = metabolic
    except Exception as exc:
        logger.warning("Erreur calcul metabolic twin : %s", exc)

    # ── LOT 11 : Advanced Intelligence summaries ──────────────────────────

    # Digital Twin V2 — load most recent snapshot
    try:
        from app.models.advanced import DigitalTwinSnapshot, BiologicalAgeSnapshot, MotionIntelligenceSnapshot
        twin_row = (await db.execute(
            select(DigitalTwinSnapshot)
            .where(DigitalTwinSnapshot.user_id == user_id)
            .order_by(DigitalTwinSnapshot.snapshot_date.desc())
            .limit(1)
        )).scalar_one_or_none()
        if twin_row and twin_row.overall_status:
            components = twin_row.components or {}
            readiness_val = components.get("training_readiness", {}).get("value", "?")
            fatigue_val = components.get("fatigue", {}).get("value", "?")
            glycogen_stat = components.get("glycogen", {}).get("status", "?")
            concern = f" ⚠ {twin_row.primary_concern}" if twin_row.primary_concern else ""
            ctx.twin_summary = (
                f"Statut {twin_row.overall_status}, "
                f"Readiness {readiness_val}/100, Fatigue {fatigue_val}/100, "
                f"Glycogène {glycogen_stat}.{concern}"
            )
            # LOT 18 — Top 3 composantes clés avec valeur + statut
            _priority_keys = [
                "training_readiness", "fatigue", "glycogen",
                "inflammation", "sleep_quality", "metabolic_flexibility",
            ]
            _signals: list[str] = []
            for _key in _priority_keys:
                _comp = components.get(_key)
                if isinstance(_comp, dict):
                    _val = _comp.get("value", "?")
                    _stat = _comp.get("status", "?")
                    _label = _key.replace("_", " ").title()
                    _signals.append(f"• {_label}: {_val}/100 ({_stat})")
                if len(_signals) >= 3:
                    break
            if _signals:
                ctx.twin_key_signals = "\n".join(_signals)
    except Exception as exc:
        logger.warning("Erreur chargement Digital Twin : %s", exc)

    # Biological Age — load most recent snapshot
    try:
        bio_row = (await db.execute(
            select(BiologicalAgeSnapshot)
            .where(BiologicalAgeSnapshot.user_id == user_id)
            .order_by(BiologicalAgeSnapshot.snapshot_date.desc())
            .limit(1)
        )).scalar_one_or_none()
        if bio_row and bio_row.biological_age:
            sign = "+" if (bio_row.biological_age_delta or 0) >= 0 else ""
            levers = bio_row.levers or []
            top_lever = levers[0].get("title", "") if levers else ""
            ctx.bio_age_summary = (
                f"Âge biologique {bio_row.biological_age:.1f} ans "
                f"(delta {sign}{bio_row.biological_age_delta or 0:.1f} ans, "
                f"trend: {bio_row.trend_direction or 'stable'})."
                + (f" Levier: {top_lever}." if top_lever else "")
            )
    except Exception as exc:
        logger.warning("Erreur chargement Biological Age : %s", exc)

    # Motion Intelligence — load most recent snapshot
    try:
        motion_row = (await db.execute(
            select(MotionIntelligenceSnapshot)
            .where(MotionIntelligenceSnapshot.user_id == user_id)
            .order_by(MotionIntelligenceSnapshot.snapshot_date.desc())
            .limit(1)
        )).scalar_one_or_none()
        if motion_row and motion_row.sessions_analyzed:
            alerts = motion_row.risk_alerts or []
            alert_text = f" ⚠ {alerts[0]}" if alerts else ""
            ctx.motion_summary = (
                f"Santé mouvement {motion_row.movement_health_score:.0f}/100, "
                f"stabilité {motion_row.stability_score:.0f}, "
                f"mobilité {motion_row.mobility_score:.0f}, "
                f"asymétrie {motion_row.asymmetry_score:.0f}. "
                f"Trend: {motion_row.overall_quality_trend or 'stable'}.{alert_text}"
            )
    except Exception as exc:
        logger.warning("Erreur chargement Motion Intelligence : %s", exc)

    # Adaptive Nutrition — compute fresh (stateless)
    try:
        from app.domains.adaptive_nutrition.endpoints import _load_adaptive_inputs
        from app.domains.adaptive_nutrition.service import (
            compute_adaptive_plan, build_adaptive_nutrition_summary
        )
        adaptive_inputs = await _load_adaptive_inputs(db, user_id, target_date)
        adaptive_plan = compute_adaptive_plan(**adaptive_inputs)
        ctx.adaptive_nutrition_summary = build_adaptive_nutrition_summary(adaptive_plan)
    except Exception as exc:
        logger.warning("Erreur calcul Adaptive Nutrition : %s", exc)


    # ── LOT 13 : Personalized Learning Profile ──────────────────────────────
    try:
        from app.domains.learning.service import (
            compute_user_learning_profile, build_learning_summary,
            WeightCalorieObservation, ReadinessObservation,
        )
        from datetime import timedelta as _td
        _since = target_date - _td(days=90)
        _dm_res = await db.execute(
            select(DailyMetrics)
            .where(DailyMetrics.user_id == user_id, DailyMetrics.metrics_date >= _since)
            .order_by(DailyMetrics.metrics_date)
        )
        _dm_rows = _dm_res.scalars().all()
        _wc_obs = [
            WeightCalorieObservation(
                obs_date=m.metrics_date,
                weight_kg=m.weight_kg,
                calories_consumed=m.total_calories or m.calories_consumed or 2000,
            )
            for m in _dm_rows if m.weight_kg and (m.total_calories or m.calories_consumed)
        ]
        _r_res = await db.execute(
            select(ReadinessScore)
            .where(ReadinessScore.user_id == user_id, ReadinessScore.score_date >= _since)
            .order_by(ReadinessScore.score_date)
        )
        _r_rows = _r_res.scalars().all()
        _ro_obs = [
            ReadinessObservation(obs_date=r.score_date, readiness_score=r.overall_readiness or 60.0)
            for r in _r_rows
        ]
        _learning = compute_user_learning_profile(weight_calorie_obs=_wc_obs, readiness_obs=_ro_obs)
        ctx.learning_summary = build_learning_summary(_learning)
    except Exception as exc:
        logger.warning("Erreur calcul Learning Profile : %s", exc)

    # ── LOT 15 : Injury Prevention ────────────────────────────────────
    try:
        from app.domains.injury.service import compute_injury_prevention_analysis, build_injury_summary
        from app.models.advanced import (
            MotionIntelligenceSnapshot as _MIS,
            DigitalTwinSnapshot as _DTS,
        )
        _twin_r = (await db.execute(
            select(_DTS).where(_DTS.user_id == user_id)
            .order_by(_DTS.snapshot_date.desc()).limit(1)
        )).scalar_one_or_none()
        _motion_r = (await db.execute(
            select(_MIS).where(_MIS.user_id == user_id)
            .order_by(_MIS.snapshot_date.desc()).limit(1)
        )).scalar_one_or_none()
        _fatigue_v = None
        if _twin_r and _twin_r.components:
            _fc = _twin_r.components.get("fatigue", {})
            _fatigue_v = _fc.get("value") if isinstance(_fc, dict) else None
        _injury = compute_injury_prevention_analysis(
            fatigue_score=_fatigue_v,
            asymmetry_score=_motion_r.asymmetry_score if _motion_r else None,
        )
        ctx.injury_risk_summary = build_injury_summary(_injury)
    except Exception as exc:
        logger.warning("Erreur calcul Injury Prevention : %s", exc)

    # ── LOT 16 : Biomarkers (from in-memory store) ──────────────────────
    try:
        from app.domains.biomarkers.service import (
            compute_biomarker_analysis, build_biomarker_summary, _lab_store,
            BiomarkerResult as _BR,
        )
        from datetime import date as _date_cls
        _user_id_str = str(user_id)
        _lab_results = [
            _BR(
                marker_name=_r["marker_name"],
                value=_r["value"],
                unit=_r["unit"],
                lab_date=_date_cls.fromisoformat(_r["lab_date"]),
            )
            for _r in _lab_store.get(_user_id_str, [])
        ]
        if _lab_results:
            _bio = compute_biomarker_analysis(_lab_results)
            ctx.biomarker_summary = build_biomarker_summary(_bio)
    except Exception as exc:
        logger.warning("Erreur calcul Biomarkers : %s", exc)

    return ctx
