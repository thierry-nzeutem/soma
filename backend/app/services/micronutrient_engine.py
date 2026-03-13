"""
Micronutrient Engine SOMA — LOT 3.

Estime les apports en micronutriments depuis le journal alimentaire.

Sources de données (par ordre de fiabilité) :
  1. food_item.micronutrients JSONB (si entrée liée à un FoodItem du catalogue)
  2. Estimation par groupe alimentaire (fallback pour entrées manuelles)

Micronutriments suivis :
  - Vitamine D (mcg)
  - Magnésium (mg)
  - Potassium (mg)
  - Sodium (mg)
  - Calcium (mg)
  - Fer (mg)
  - Zinc (mg)
  - Oméga-3 (g)

Toutes les fonctions de calcul sont pures et testables sans DB.
"""
from typing import Optional, List, Dict
from dataclasses import dataclass, field

# ── AJR (Apport Journalier Recommandé) ─────────────────────────────────────────

AJR_MALE = {
    "vitamin_d_mcg":    20.0,    # mcg/j (IOM 2011)
    "magnesium_mg":    420.0,    # mg/j
    "potassium_mg":   3400.0,    # mg/j (NASEM 2019)
    "sodium_mg":      2300.0,    # mg/j (limite)
    "calcium_mg":     1000.0,    # mg/j
    "iron_mg":           8.0,    # mg/j
    "zinc_mg":          11.0,    # mg/j
    "omega3_g":          1.6,    # g/j (AHA)
}

AJR_FEMALE = {
    "vitamin_d_mcg":    20.0,
    "magnesium_mg":    320.0,
    "potassium_mg":   2600.0,
    "sodium_mg":      2300.0,
    "calcium_mg":     1000.0,
    "iron_mg":          18.0,    # mg/j (plus élevé pour les femmes)
    "zinc_mg":           8.0,
    "omega3_g":          1.1,    # g/j
}

# Noms affichés
MICRO_LABELS: Dict[str, Dict[str, str]] = {
    "vitamin_d_mcg": {"name": "Vitamin D", "name_fr": "Vitamine D", "unit": "mcg"},
    "magnesium_mg":  {"name": "Magnesium", "name_fr": "Magnésium", "unit": "mg"},
    "potassium_mg":  {"name": "Potassium", "name_fr": "Potassium", "unit": "mg"},
    "sodium_mg":     {"name": "Sodium", "name_fr": "Sodium", "unit": "mg"},
    "calcium_mg":    {"name": "Calcium", "name_fr": "Calcium", "unit": "mg"},
    "iron_mg":       {"name": "Iron", "name_fr": "Fer", "unit": "mg"},
    "zinc_mg":       {"name": "Zinc", "name_fr": "Zinc", "unit": "mg"},
    "omega3_g":      {"name": "Omega-3", "name_fr": "Oméga-3", "unit": "g"},
}

# Aliments riches en chaque nutriment (pour les recommandations)
FOOD_SOURCES: Dict[str, List[str]] = {
    "vitamin_d_mcg": ["saumon", "maquereau", "thon", "jaune d'œuf", "champignons exposés UV"],
    "magnesium_mg":  ["amandes", "épinards", "légumineuses", "graines de citrouille", "avocat"],
    "potassium_mg":  ["banane", "patate douce", "avocat", "épinards", "tomate"],
    "sodium_mg":     ["sel de table", "charcuteries", "fromage", "plats préparés"],
    "calcium_mg":    ["lait", "yaourt", "fromage", "chou kale", "amandes"],
    "iron_mg":       ["viande rouge", "foie", "lentilles", "épinards", "graines de citrouille"],
    "zinc_mg":       ["huîtres", "viande rouge", "graines de citrouille", "légumineuses"],
    "omega3_g":      ["saumon", "maquereau", "sardines", "noix", "graines de lin"],
}

# Estimation de micronutriments par groupe alimentaire (pour 100g de portion)
# Valeurs moyennes approximatives — utilisées quand le FoodItem n'a pas de données micronutrients
FOOD_GROUP_ESTIMATES: Dict[str, Dict[str, float]] = {
    "protein": {        # viandes, poissons, œufs
        "vitamin_d_mcg": 1.0, "magnesium_mg": 25.0, "potassium_mg": 350.0,
        "sodium_mg": 80.0, "calcium_mg": 15.0, "iron_mg": 2.5, "zinc_mg": 3.5, "omega3_g": 0.3,
    },
    "dairy": {          # lait, yaourt, fromage
        "vitamin_d_mcg": 1.5, "magnesium_mg": 20.0, "potassium_mg": 200.0,
        "sodium_mg": 120.0, "calcium_mg": 200.0, "iron_mg": 0.1, "zinc_mg": 1.0, "omega3_g": 0.05,
    },
    "vegetable": {      # légumes feuilles, légumes variés
        "vitamin_d_mcg": 0.0, "magnesium_mg": 30.0, "potassium_mg": 400.0,
        "sodium_mg": 30.0, "calcium_mg": 50.0, "iron_mg": 1.5, "zinc_mg": 0.5, "omega3_g": 0.05,
    },
    "fruit": {
        "vitamin_d_mcg": 0.0, "magnesium_mg": 12.0, "potassium_mg": 200.0,
        "sodium_mg": 2.0, "calcium_mg": 15.0, "iron_mg": 0.3, "zinc_mg": 0.1, "omega3_g": 0.01,
    },
    "grain": {          # céréales, pain, pâtes, riz
        "vitamin_d_mcg": 0.0, "magnesium_mg": 40.0, "potassium_mg": 150.0,
        "sodium_mg": 5.0, "calcium_mg": 20.0, "iron_mg": 1.8, "zinc_mg": 1.5, "omega3_g": 0.02,
    },
    "fat": {            # huiles, noix, avocats
        "vitamin_d_mcg": 0.2, "magnesium_mg": 80.0, "potassium_mg": 350.0,
        "sodium_mg": 5.0, "calcium_mg": 80.0, "iron_mg": 2.0, "zinc_mg": 2.5, "omega3_g": 2.5,
    },
    "processed": {
        "vitamin_d_mcg": 0.3, "magnesium_mg": 15.0, "potassium_mg": 200.0,
        "sodium_mg": 600.0, "calcium_mg": 40.0, "iron_mg": 1.0, "zinc_mg": 0.8, "omega3_g": 0.05,
    },
}

# Statuts de suffisance
STATUS_THRESHOLDS = {
    "sufficient": 80.0,  # >= 80% de l'AJR  (pct_of_target est en %)
    "low":        50.0,  # 50-79%
    "deficient":   0.0,  # < 50%
}


# ── Dataclasses ────────────────────────────────────────────────────────────────

@dataclass
class MicronutrientResult:
    """Résultat pour un micronutriment."""
    key: str
    name: str
    name_fr: str
    unit: str
    consumed: Optional[float]
    target: float
    pct_of_target: Optional[float]
    status: str
    food_sources: List[str] = field(default_factory=list)


@dataclass
class MicronutrientAnalysis:
    """Résultat complet de l'analyse micronutritionnelle."""
    micronutrients: List[MicronutrientResult]
    overall_micro_score: float          # 0-100
    top_deficiencies: List[str]         # clés des nutriments en déficit
    data_quality: str                   # good | partial | estimated
    entries_with_micro_data_pct: float
    analysis_note: str


# ── Fonctions pures ────────────────────────────────────────────────────────────

def get_ajr(sex: Optional[str] = None) -> Dict[str, float]:
    """Retourne l'AJR adapté au sexe."""
    if sex and sex.lower() == "female":
        return AJR_FEMALE.copy()
    return AJR_MALE.copy()


def estimate_from_food_group(
    food_group: Optional[str],
    quantity_g: Optional[float],
) -> Dict[str, float]:
    """
    Estime les micronutriments d'une entrée depuis son groupe alimentaire.
    Retourne un dict {nutriment: valeur} normalisé pour la quantité en grammes.
    """
    if not food_group or not quantity_g or quantity_g <= 0:
        return {}
    estimates = FOOD_GROUP_ESTIMATES.get(food_group, {})
    ratio = quantity_g / 100.0
    return {k: round(v * ratio, 3) for k, v in estimates.items()}


def extract_micros_from_food_item(
    micronutrients_jsonb: Optional[dict],
    quantity_g: Optional[float],
) -> Dict[str, float]:
    """
    Extrait les micronutriments depuis le JSONB d'un FoodItem (pour 100g).
    Normalise à la quantité réelle consommée.
    """
    if not micronutrients_jsonb or not quantity_g or quantity_g <= 0:
        return {}
    ratio = quantity_g / 100.0
    result = {}
    for key in MICRO_LABELS:
        if key in micronutrients_jsonb and micronutrients_jsonb[key] is not None:
            result[key] = round(float(micronutrients_jsonb[key]) * ratio, 3)
    return result


def classify_status(pct: Optional[float]) -> str:
    """Retourne le statut de suffisance (sufficient / low / deficient / unknown)."""
    if pct is None:
        return "unknown"
    if pct >= STATUS_THRESHOLDS["sufficient"]:
        return "sufficient"
    if pct >= STATUS_THRESHOLDS["low"]:
        return "low"
    return "deficient"


def compute_overall_micro_score(results: List[MicronutrientResult]) -> float:
    """
    Score micronutritionnel global (0-100).
    Moyenne des % d'AJR atteints, capped à 100%.
    Nutriments inconnus comptent 0 (manque de données).
    """
    if not results:
        return 0.0
    total = 0.0
    n = 0
    for r in results:
        if r.pct_of_target is not None:
            total += min(100.0, r.pct_of_target)
            n += 1
    if n == 0:
        return 0.0
    return round(total / n, 1)


def analyze_micronutrients(
    entries: list,   # List of objects with: calories, quantity_g, food_group, micronutrients (from food_item)
    sex: Optional[str] = None,
    days: int = 1,   # Nombre de jours agrégés (pour normaliser les totaux)
) -> MicronutrientAnalysis:
    """
    Analyse les micronutriments depuis une liste d'entrées nutritionnelles.

    Chaque entry doit exposer :
      - quantity_g (Optional[float])
      - food_group (Optional[str]) — depuis food_item si disponible
      - food_item_micronutrients (Optional[dict]) — JSONB depuis le catalog
      - calories (Optional[float])

    Retourne une MicronutrientAnalysis complète.
    """
    ajr = get_ajr(sex)
    totals: Dict[str, float] = {k: 0.0 for k in MICRO_LABELS}
    entries_with_micro = 0
    total_entries = len(entries)

    for entry in entries:
        quantity_g = getattr(entry, "quantity_g", None) or 100.0
        food_group = getattr(entry, "food_group", None)
        micro_jsonb = getattr(entry, "food_item_micronutrients", None)

        if micro_jsonb:
            # Source primaire : données du catalogue
            micros = extract_micros_from_food_item(micro_jsonb, quantity_g)
            entries_with_micro += 1
        else:
            # Fallback : estimation par groupe alimentaire
            micros = estimate_from_food_group(food_group, quantity_g)

        for key, val in micros.items():
            if key in totals:
                totals[key] += val

    # Normaliser si plusieurs jours
    if days > 1:
        totals = {k: v / days for k, v in totals.items()}

    # Construire les résultats
    results: List[MicronutrientResult] = []
    for key, label_info in MICRO_LABELS.items():
        consumed = round(totals[key], 2) if totals[key] > 0 else None
        target = ajr[key]
        pct = round((consumed / target) * 100, 1) if (consumed and target) else None
        status = classify_status(pct)

        results.append(MicronutrientResult(
            key=key,
            name=label_info["name"],
            name_fr=label_info["name_fr"],
            unit=label_info["unit"],
            consumed=consumed,
            target=target,
            pct_of_target=pct,
            status=status,
            food_sources=FOOD_SOURCES.get(key, []),
        ))

    # Score global
    score = compute_overall_micro_score(results)

    # Déficits
    top_deficiencies = [
        r.name_fr for r in results
        if r.status in ("deficient", "low")
    ][:4]

    # Qualité des données
    micro_pct = round((entries_with_micro / max(1, total_entries)) * 100, 1)
    if micro_pct >= 50:
        quality = "good"
    elif micro_pct >= 20:
        quality = "partial"
    else:
        quality = "estimated"

    note = (
        "Analyse basée sur des données réelles du catalogue alimentaire."
        if quality == "good"
        else "Estimation basée sur les groupes alimentaires (données micronutriments limitées)."
    )

    return MicronutrientAnalysis(
        micronutrients=results,
        overall_micro_score=score,
        top_deficiencies=top_deficiencies,
        data_quality=quality,
        entries_with_micro_data_pct=micro_pct,
        analysis_note=note,
    )
