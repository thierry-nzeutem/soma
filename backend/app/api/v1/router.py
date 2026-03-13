from fastapi import APIRouter
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.users import router as profile_router, body_router
from app.api.v1.endpoints.health import router as health_router, sleep_router, hydration_router
from app.api.v1.endpoints.dashboard import router as dashboard_router
from app.api.v1.endpoints.workouts import exercises_router, sessions_router
from app.api.v1.endpoints.nutrition import (
    food_router, entries_router, summary_router, photos_router,
)
from app.api.v1.endpoints.scores import scores_router
from app.api.v1.endpoints.metrics import metrics_router
from app.api.v1.endpoints.insights import insights_router
from app.api.v1.endpoints.health_plan import health_plan_router
from app.api.v1.endpoints.home import home_router
from app.api.v1.endpoints.vision import vision_router
from app.api.v1.endpoints.coach import coach_router
from app.api.v1.endpoints.predictions import predictions_router

# ── LOT 18 : Productization & Daily Experience ────────────────────────────────
from app.api.v1.endpoints.daily import daily_router
from app.api.v1.endpoints.onboarding import onboarding_router
from app.api.v1.endpoints.analytics_events import analytics_router

# ── LOT 19 : Product Analytics Dashboard ──────────────────────────────────────
from app.api.v1.endpoints.analytics_dashboard import analytics_dashboard_router
# -- Withings-inspired features (body composition, fitness, activity, HR, sleep quality, reports) --
from app.api.v1.endpoints.body_composition import body_composition_router
from app.api.v1.endpoints.fitness import fitness_router
from app.api.v1.endpoints.activity import activity_router
from app.api.v1.endpoints.heart_rate import heart_rate_router
from app.api.v1.endpoints.sleep_quality import sleep_quality_router
from app.api.v1.endpoints.reports import reports_router

# ── LOT 11 : Advanced Intelligence domains ────────────────────────────────────
from app.domains.twin.endpoints import twin_router
from app.domains.biological_age.endpoints import bio_age_router
from app.domains.adaptive_nutrition.endpoints import adaptive_nutrition_router
from app.domains.motion.endpoints import motion_router

# ── LOT 13 : Personalized Learning Engine ─────────────────────────────────────
from app.domains.learning.endpoints import learning_router

# ── LOT 15 : Injury Prevention Engine ─────────────────────────────────────────
from app.domains.injury.endpoints import injury_router

# ── LOT 16 : Longevity Lab Biomarkers ─────────────────────────────────────────
from app.domains.biomarkers.endpoints import biomarkers_router

# ── LOT 14 : Coach Pro / Multi-Athletes Platform ───────────────────────────────
from app.domains.coach_platform.endpoints import coach_platform_router

api_router = APIRouter(prefix="/api/v1")

# ── Auth ──────────────────────────────────────────────────────────────────────
api_router.include_router(auth_router)

# ── Profil & métriques corporelles ────────────────────────────────────────────
api_router.include_router(profile_router)
api_router.include_router(body_router)

# ── Santé (health sync, sleep, hydration) ─────────────────────────────────────
api_router.include_router(health_router)
api_router.include_router(sleep_router)
api_router.include_router(hydration_router)

# ── Dashboard journalier ───────────────────────────────────────────────────────
api_router.include_router(dashboard_router)

# ── Workout (exercices + sessions) ────────────────────────────────────────────
api_router.include_router(exercises_router)
api_router.include_router(sessions_router)

# ── Nutrition (aliments, journal, photos + LOT 3: targets, micronutriments, suppléments) ──
api_router.include_router(food_router)
api_router.include_router(entries_router)
api_router.include_router(summary_router)
api_router.include_router(photos_router)

# ── Scores (readiness + LOT 3: longévité) ─────────────────────────────────────
api_router.include_router(scores_router)

# ── LOT 3 : Intelligence santé ────────────────────────────────────────────────
api_router.include_router(metrics_router)      # GET /metrics/daily, /metrics/history
api_router.include_router(insights_router)     # GET /insights, POST /insights/run, PATCH
api_router.include_router(health_plan_router)  # GET /health/plan/today

# ── LOT 5 : Home Summary (agrégateur mobile) ──────────────────────────────────
api_router.include_router(home_router)         # GET /home/summary

# ── LOT 7 : Computer Vision ────────────────────────────────────────────────────
api_router.include_router(vision_router)       # POST /vision/sessions, GET /vision/sessions

# ── LOT 9 : Coach IA + Metabolic Twin ─────────────────────────────────────────
api_router.include_router(coach_router)        # POST /coach/ask, /coach/thread, GET /coach/history

# ── LOT 10 : Predictive Health Engine ─────────────────────────────────────────
api_router.include_router(predictions_router)  # GET /health/predictions, /health/injury-risk, /health/overtraining

# ── LOT 11 : Advanced Intelligence (Digital Twin, Biological Age, Adaptive Nutrition, Motion) ──
api_router.include_router(twin_router)               # GET /twin/today, /twin/summary, /twin/history
api_router.include_router(bio_age_router)            # GET /longevity/biological-age, /longevity/history, /longevity/levers
api_router.include_router(adaptive_nutrition_router) # GET /nutrition/adaptive-targets, /nutrition/adaptive-plan; POST /nutrition/adaptive-plan/recompute
api_router.include_router(motion_router)             # GET /vision/motion-summary, /vision/motion-history, /vision/asymmetry-risk

# ── LOT 13 : Personalized Learning Engine ─────────────────────────────────────
api_router.include_router(learning_router)           # GET /learning/profile, /learning/insights; POST /learning/recompute

# ── LOT 15 : Injury Prevention Engine ─────────────────────────────────────────
api_router.include_router(injury_router)             # GET /injury/risk, /injury/history, /injury/recommendations

# ── LOT 16 : Longevity Lab Biomarkers ─────────────────────────────────────────
api_router.include_router(biomarkers_router)         # POST /labs/result, GET /labs/results, /labs/analysis, /labs/longevity-impact

# ── LOT 14 : Coach Pro / Multi-Athletes Platform ───────────────────────────────
api_router.include_router(coach_platform_router)     # POST /coach-platform/coach/register, GET /coach-platform/athletes, etc.

# ── LOT 18 : Productization & Daily Experience Engine ─────────────────────────
api_router.include_router(daily_router)              # GET /daily/briefing
api_router.include_router(onboarding_router)         # POST /profile/onboarding
api_router.include_router(analytics_router)          # POST /analytics/event

# ── LOT 19 : Product Analytics Dashboard ──────────────────────────────────────
api_router.include_router(analytics_dashboard_router)  # GET /analytics/summary, /events, /funnel/onboarding, /retention/cohorts, /features, /coach, /performance

# -- Withings-inspired features --
api_router.include_router(body_composition_router)  # GET /body/composition/trend, /body/weight/trend
api_router.include_router(fitness_router)            # GET /fitness/cardio-fitness, /fitness/cardio-fitness/history
api_router.include_router(activity_router)           # GET /activity/day, /activity/period
api_router.include_router(heart_rate_router)         # GET /heart-rate/analytics, /heart-rate/timeline, /heart-rate/all-data
api_router.include_router(sleep_quality_router)      # GET /sleep/quality-score
api_router.include_router(reports_router)            # GET /reports/health

# ── HRV & Stress + Gamification + Cycle ───────────────────────────────────────
from app.api.v1.endpoints.hrv import hrv_router
from app.api.v1.endpoints.gamification import gamification_router
from app.api.v1.endpoints.cycle import cycle_router

api_router.include_router(hrv_router)           # GET /hrv/score, /hrv/history
api_router.include_router(gamification_router)  # GET /gamification/streaks, /gamification/achievements, /gamification/profile
api_router.include_router(cycle_router)         # POST /cycle/entry, GET /cycle/entries, /cycle/summary

# ── Subscription & Entitlements ────────────────────────────────────────────
from app.api.v1.endpoints.entitlements import entitlements_router
from app.api.v1.endpoints.billing import billing_router

api_router.include_router(entitlements_router)    # GET /me/entitlements
api_router.include_router(billing_router)          # POST /billing/webhook, /checkout, /portal

# ── Admin, Feature Usage, Profile Full ────────────────────────────────────────
from app.api.v1.endpoints.feature_usage import feature_usage_router
from app.api.v1.endpoints.admin import admin_router
from app.api.v1.endpoints.profile_full import profile_full_router

api_router.include_router(feature_usage_router)  # POST /me/feature-usage, GET /admin/feature-usage
api_router.include_router(admin_router)           # /admin/settings, /admin/users, /admin/stats
api_router.include_router(profile_full_router)    # GET /me/profile (consolide)
