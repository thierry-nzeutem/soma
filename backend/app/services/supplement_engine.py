"""
Supplement Engine SOMA — LOT 3.

Génère des suggestions de compléments alimentaires basées sur :
  - Analyses micronutritionnelles (déficiences détectées)
  - Objectif utilisateur (muscle_gain → créatine)
  - Pattern d'entraînement (charge élevée → magnésium, oméga-3)
  - Profil alimentaire (végétarien → B12, fer)

Approche : règles expertes avec scoring de confiance.
Chaque règle est transparente et indique son fondement (evidence_type).

Toutes les fonctions sont pures et testables sans DB.
"""
from typing import Optional, List, Dict
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.services.micronutrient_engine import MicronutrientAnalysis, STATUS_THRESHOLDS


# ── Dataclass suggestion ────────────────────────────────────────────────────────

@dataclass
class SupplementSuggestion:
    """Suggestion de complément générée par le moteur."""
    supplement_name: str
    goal: str
    reason: str
    observed_data_basis: str
    confidence_level: float          # 0.0 - 1.0
    evidence_type: str               # data_observed | hypothesis | pattern
    suggested_dose: str
    suggested_timing: str
    trial_duration_weeks: int
    precautions: str


# ── Règles expertes ─────────────────────────────────────────────────────────────

def _suggest_vitamin_d(micro_analysis: Optional[MicronutrientAnalysis]) -> Optional[SupplementSuggestion]:
    """Vitamine D : suggérée si déficit détecté ou données insuffisantes."""
    if not micro_analysis:
        return None
    vd_result = next((r for r in micro_analysis.micronutrients if r.key == "vitamin_d_mcg"), None)
    if not vd_result:
        return None
    if vd_result.status not in ("deficient", "low", "unknown"):
        return None

    confidence = 0.85 if vd_result.status == "deficient" else (0.70 if vd_result.status == "low" else 0.50)
    evidence = "data_observed" if vd_result.status != "unknown" else "hypothesis"

    return SupplementSuggestion(
        supplement_name="Vitamine D3",
        goal="Optimisation vitamine D",
        reason=f"Apport en vitamine D {vd_result.status} "
               f"({vd_result.pct_of_target:.0f}% de l'AJR)" if vd_result.pct_of_target else
               "Apport en vitamine D non mesurable via les données actuelles.",
        observed_data_basis=f"Vitamine D estimée : {vd_result.consumed or 0:.1f} mcg / {vd_result.target:.0f} mcg cible",
        confidence_level=confidence,
        evidence_type=evidence,
        suggested_dose="1000-2000 UI/jour (25-50 mcg)",
        suggested_timing="Avec le repas principal (lipides facilitent l'absorption)",
        trial_duration_weeks=8,
        precautions="Ne pas dépasser 4000 UI/j sans bilan sanguin. Contrôler 25-OH-D3 après 3 mois.",
    )


def _suggest_magnesium(
    micro_analysis: Optional[MicronutrientAnalysis],
    training_load: Optional[float],
) -> Optional[SupplementSuggestion]:
    """Magnésium : suggéré si déficit + charge d'entraînement élevée."""
    if not micro_analysis:
        return None
    mg_result = next((r for r in micro_analysis.micronutrients if r.key == "magnesium_mg"), None)
    if not mg_result:
        return None
    if mg_result.status not in ("deficient", "low"):
        return None

    high_load = training_load and training_load > 300
    confidence = 0.80 if (mg_result.status == "deficient" and high_load) else 0.65

    load_note = " La charge d'entraînement élevée augmente les besoins en magnésium." if high_load else ""

    return SupplementSuggestion(
        supplement_name="Magnésium Bisglycinate",
        goal="Récupération musculaire et qualité du sommeil",
        reason=f"Apport en magnésium {mg_result.status} "
               f"({mg_result.pct_of_target:.0f}% AJR).{load_note}" if mg_result.pct_of_target else
               "Apport magnésium insuffisant détecté.",
        observed_data_basis=f"Magnésium estimé : {mg_result.consumed or 0:.0f} mg / {mg_result.target:.0f} mg AJR. "
                            f"Charge entraînement : {training_load or 0:.0f}",
        confidence_level=confidence,
        evidence_type="data_observed",
        suggested_dose="200-400 mg/jour",
        suggested_timing="Le soir avant le coucher (favorise le sommeil et la récupération)",
        trial_duration_weeks=4,
        precautions="Privilégier bisglycinate (meilleure biodisponibilité). "
                    "Réduire si selles molles.",
    )


def _suggest_omega3(micro_analysis: Optional[MicronutrientAnalysis]) -> Optional[SupplementSuggestion]:
    """Oméga-3 : suggéré si apport insuffisant, particulièrement pour objectif longévité."""
    if not micro_analysis:
        return None
    om_result = next((r for r in micro_analysis.micronutrients if r.key == "omega3_g"), None)
    if not om_result:
        return None
    if om_result.status not in ("deficient", "low"):
        return None

    confidence = 0.75 if om_result.status == "deficient" else 0.60

    return SupplementSuggestion(
        supplement_name="Oméga-3 (EPA+DHA)",
        goal="Santé cardiovasculaire et anti-inflammation",
        reason=f"Apport en oméga-3 {om_result.status}. "
               f"Les EPA/DHA sont essentiels à la santé cardiovasculaire et réduisent l'inflammation.",
        observed_data_basis=f"Oméga-3 estimé : {om_result.consumed or 0:.2f} g / {om_result.target:.1f} g AJR",
        confidence_level=confidence,
        evidence_type="data_observed",
        suggested_dose="1-2 g EPA+DHA/jour",
        suggested_timing="Avec les repas pour réduire les reflux",
        trial_duration_weeks=12,
        precautions="Peut interagir avec anticoagulants. Vérifier la pureté (mercure). "
                    "Préférer la forme triglycéride.",
    )


def _suggest_creatine(
    primary_goal: Optional[str],
    fitness_level: Optional[str],
    workout_type: Optional[str],
) -> Optional[SupplementSuggestion]:
    """Créatine : suggérée pour muscle_gain ou performance avec entraînement force."""
    if primary_goal not in ("muscle_gain", "performance"):
        return None
    if fitness_level not in ("intermediate", "advanced", "athlete"):
        return None
    if workout_type and workout_type not in ("strength", "mixed", "hiit", None):
        return None

    return SupplementSuggestion(
        supplement_name="Créatine Monohydrate",
        goal="Force et hypertrophie musculaire",
        reason="Objectif gain musculaire / performance + entraînement force. "
               "La créatine est le complément le mieux documenté pour la force et la puissance.",
        observed_data_basis=f"Objectif : {primary_goal}. Niveau : {fitness_level}. "
                            f"Type d'entraînement : {workout_type or 'force'}.",
        confidence_level=0.90,
        evidence_type="pattern",
        suggested_dose="3-5 g/jour (pas de phase de charge nécessaire)",
        suggested_timing="N'importe quand — post-entraînement légèrement préférable",
        trial_duration_weeks=8,
        precautions="S'hydrater suffisamment. Éviter si insuffisance rénale. "
                    "Monohydrate = forme la plus testée et la moins chère.",
    )


def _suggest_protein(
    protein_pct_target: Optional[float],
    primary_goal: Optional[str],
    dietary_regime: Optional[str],
) -> Optional[SupplementSuggestion]:
    """Whey protein : suggéré si apport protéique < 70% de la cible."""
    if protein_pct_target is None or protein_pct_target >= 0.70:
        return None

    is_vegan = dietary_regime and "vegan" in dietary_regime.lower()
    source = "Protéines végétales (pois/chanvre)" if is_vegan else "Whey Protéine (isolat)"

    return SupplementSuggestion(
        supplement_name=source,
        goal="Atteindre l'apport protéique cible",
        reason=f"Apport protéique à {round((protein_pct_target or 0) * 100)}% de la cible — "
               "difficile d'atteindre les besoins uniquement via l'alimentation.",
        observed_data_basis=f"Apport protéique : {round((protein_pct_target or 0) * 100)}% de la cible quotidienne.",
        confidence_level=0.80,
        evidence_type="data_observed",
        suggested_dose="20-30 g par prise (1-2 shakes/jour selon besoin)",
        suggested_timing="Post-entraînement ou en collation",
        trial_duration_weeks=4,
        precautions="Préférer un isolat (< 1% lactose). "
                    "Complémentaire à l'alimentation, non substitutif.",
    )


def _suggest_iron(
    micro_analysis: Optional[MicronutrientAnalysis],
    sex: Optional[str],
) -> Optional[SupplementSuggestion]:
    """Fer : suggéré uniquement pour les femmes avec déficit détecté."""
    if not micro_analysis:
        return None
    if sex and sex.lower() != "female":
        return None

    fe_result = next((r for r in micro_analysis.micronutrients if r.key == "iron_mg"), None)
    if not fe_result or fe_result.status != "deficient":
        return None

    return SupplementSuggestion(
        supplement_name="Fer (bisglycinate ou liposomal)",
        goal="Correction déficit en fer",
        reason=f"Apport en fer déficient ({fe_result.pct_of_target:.0f}% AJR). "
               "Les femmes ont des besoins en fer plus élevés." if fe_result.pct_of_target else
               "Déficit en fer détecté.",
        observed_data_basis=f"Fer estimé : {fe_result.consumed or 0:.1f} mg / {fe_result.target:.0f} mg AJR",
        confidence_level=0.70,
        evidence_type="data_observed",
        suggested_dose="18-25 mg/jour (selon bilan sanguin)",
        suggested_timing="À jeun ou avec vitamine C (améliore l'absorption). Éviter avec café/thé.",
        trial_duration_weeks=8,
        precautions="Ne pas supplémenter sans bilan sanguin (ferritine, NFS). "
                    "Excès de fer = toxique. Préférer bisglycinate (moins de troubles digestifs).",
    )


def _suggest_zinc(micro_analysis: Optional[MicronutrientAnalysis]) -> Optional[SupplementSuggestion]:
    """Zinc : suggéré si déficit + régime faible en viande."""
    if not micro_analysis:
        return None
    zn_result = next((r for r in micro_analysis.micronutrients if r.key == "zinc_mg"), None)
    if not zn_result or zn_result.status not in ("deficient", "low"):
        return None

    return SupplementSuggestion(
        supplement_name="Zinc Bisglycinate",
        goal="Immunité et récupération",
        reason=f"Apport en zinc {zn_result.status}. "
               "Le zinc est crucial pour l'immunité, la synthèse protéique et la testostérone.",
        observed_data_basis=f"Zinc estimé : {zn_result.consumed or 0:.1f} mg / {zn_result.target:.0f} mg AJR",
        confidence_level=0.65,
        evidence_type="data_observed",
        suggested_dose="15-25 mg/jour",
        suggested_timing="Avec les repas pour éviter les nausées",
        trial_duration_weeks=6,
        precautions="Ne pas dépasser 40 mg/jour. Un excès de zinc bloque l'absorption du cuivre.",
    )


# ── Moteur principal ───────────────────────────────────────────────────────────

def generate_supplement_recommendations(
    primary_goal: Optional[str] = None,
    fitness_level: Optional[str] = None,
    sex: Optional[str] = None,
    dietary_regime: Optional[str] = None,
    workout_type: Optional[str] = None,
    training_load: Optional[float] = None,
    micro_analysis: Optional[MicronutrientAnalysis] = None,
    # Apport protéique réel vs cible (ratio 0-1)
    protein_ratio: Optional[float] = None,
) -> List[SupplementSuggestion]:
    """
    Génère la liste de suggestions de compléments pertinents.

    Les suggestions sont ordonnées par confiance décroissante.
    Maximum 5 suggestions retournées (les plus pertinentes).
    """
    candidates: List[SupplementSuggestion] = []

    # Évaluation de chaque règle
    for fn, args in [
        (_suggest_vitamin_d,   (micro_analysis,)),
        (_suggest_magnesium,   (micro_analysis, training_load)),
        (_suggest_omega3,      (micro_analysis,)),
        (_suggest_creatine,    (primary_goal, fitness_level, workout_type)),
        (_suggest_protein,     (protein_ratio, primary_goal, dietary_regime)),
        (_suggest_iron,        (micro_analysis, sex)),
        (_suggest_zinc,        (micro_analysis,)),
    ]:
        result = fn(*args)
        if result:
            candidates.append(result)

    # Tri par confiance décroissante, limité à 5
    candidates.sort(key=lambda x: x.confidence_level, reverse=True)
    return candidates[:5]


def build_analysis_basis(
    micro_analysis: Optional[MicronutrientAnalysis],
    training_load: Optional[float],
    primary_goal: Optional[str],
) -> str:
    """Construit un résumé de la base d'analyse pour la réponse API."""
    parts = []
    if micro_analysis:
        parts.append(
            f"Analyse micronutritionnelle ({micro_analysis.data_quality}) : "
            f"score global {micro_analysis.overall_micro_score:.0f}/100."
        )
    if training_load:
        parts.append(f"Charge d'entraînement : {training_load:.0f}.")
    if primary_goal:
        parts.append(f"Objectif : {primary_goal}.")
    return " ".join(parts) if parts else "Analyse basée sur le profil utilisateur."
