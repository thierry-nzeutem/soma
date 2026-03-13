#!/usr/bin/env python3
"""
SOMA Backend -- Seed Data Script
Populates the database with realistic mock data via HTTP API calls.
Usage: python seed_data.py [--base-url http://localhost:8000]
"""

import argparse
import random
import sys
from datetime import datetime, timedelta, timezone

import requests

BASE_URL = "http://localhost:8000"
API = f"{BASE_URL}/api/v1"
USERNAME = "demo"
PASSWORD = "Demo1234!"
EMAIL = "demo@soma.app"

NOW = datetime.now(timezone.utc)
TODAY = NOW.replace(hour=0, minute=0, second=0, microsecond=0)

summary: dict[str, int] = {}


def iso(dt: datetime) -> str:
    return dt.isoformat()


session = requests.Session()


def post(path: str, json=None, **kw):
    return session.post(f"{API}{path}", json=json, **kw)


def put(path: str, json=None, **kw):
    return session.put(f"{API}{path}", json=json, **kw)


def patch(path: str, json=None, **kw):
    return session.patch(f"{API}{path}", json=json, **kw)


def get(path: str, **kw):
    return session.get(f"{API}{path}", **kw)


def seed_auth():
    print("\n[1/10] Auth -- register / login")
    r = post("/auth/register", json={"username": USERNAME, "password": PASSWORD, "email": EMAIL})
    if r.status_code == 409:
        print("  User already exists, logging in...")
        r = post("/auth/login", json={"username": USERNAME, "password": PASSWORD})
    if r.status_code not in (200, 201):
        print(f"  ERROR auth: {r.status_code} {r.text}")
        sys.exit(1)
    token = r.json()["access_token"]
    session.headers.update({"Authorization": f"Bearer {token}"})
    print(f"  Authenticated as {USERNAME}")


def seed_profile():
    print("\n[2/10] Profile -- update")
    payload = {
        "first_name": "Alex",
        "age": 32,
        "sex": "male",
        "height_cm": 178.0,
        "goal_weight_kg": 75.0,
        "primary_goal": "longevity",
        "activity_level": "active",
        "fitness_level": "intermediate",
        "dietary_regime": "omnivore",
        "intermittent_fasting": True,
        "fasting_protocol": "16:8",
        "meals_per_day": 3,
        "preferred_training_time": "morning",
        "home_equipment": ["dumbbells", "pull_up_bar", "resistance_bands"],
        "gym_access": True,
        "avg_energy_level": 7,
        "perceived_sleep_quality": 7,
        "theme_preference": "dark",
        "locale": "fr",
        "timezone": "Europe/Paris",
    }
    r = put("/profile", json=payload)
    if r.status_code == 200:
        print("  Profile updated")
    else:
        print(f"  WARN profile: {r.status_code} {r.text}")


def seed_body_metrics():
    print("\n[3/10] Body metrics -- 30 days")
    count = 0
    weight = 82.0
    bf = 18.5
    muscle = 35.0
    for d in range(30, 0, -1):
        dt = TODAY - timedelta(days=d)
        weight += random.uniform(-0.3, 0.15)
        bf += random.uniform(-0.15, 0.1)
        muscle += random.uniform(-0.05, 0.1)
        payload = {
            "weight_kg": round(weight, 1),
            "body_fat_pct": round(max(bf, 8), 1),
            "muscle_mass_kg": round(muscle, 1),
            "waist_cm": round(random.uniform(82, 86), 1),
            "measured_at": iso(dt.replace(hour=7, minute=random.randint(0, 30))),
        }
        r = post("/body-metrics", json=payload)
        if r.status_code == 201:
            count += 1
    summary["body_metrics"] = count
    print(f"  {count} body metrics created")


def seed_hydration():
    print("\n[4/10] Hydration -- 8 days")
    count = 0
    beverages = ["water", "water", "water", "tea", "coffee", "sparkling_water"]
    for d in range(8, 0, -1):
        dt = TODAY - timedelta(days=d)
        n_entries = random.randint(4, 6)
        hours = sorted(random.sample(range(7, 22), n_entries))
        for h in hours:
            payload = {
                "volume_ml": random.choice([200, 250, 300, 330, 500]),
                "logged_at": iso(dt.replace(hour=h, minute=random.randint(0, 59))),
                "beverage_type": random.choice(beverages),
            }
            r = post("/hydration/log", json=payload)
            if r.status_code == 201:
                count += 1
    summary["hydration_logs"] = count
    print(f"  {count} hydration entries created")


def seed_sleep():
    print("\n[5/10] Sleep -- 14 nights")
    count = 0
    notes_pool = [
        "Bonne nuit, endormissement rapide",
        "Reveil nocturne vers 3h",
        "Sommeil profond, reposant",
        "Difficile de trouver le sommeil",
        "Reve intense, reveil frais",
        None,
        None,
    ]
    for d in range(14, 0, -1):
        night = TODAY - timedelta(days=d)
        bed_hour = random.choice([22, 22, 23, 23, 23, 0])
        bed_min = random.randint(0, 45)
        start = night.replace(hour=bed_hour, minute=bed_min)
        if bed_hour == 0:
            start += timedelta(days=1)
        duration_h = random.uniform(6.0, 8.5)
        end = start + timedelta(hours=duration_h)
        payload = {
            "start_at": iso(start),
            "end_at": iso(end),
            "perceived_quality": random.randint(2, 5),
            "deep_sleep_minutes": random.randint(40, 110),
            "rem_sleep_minutes": random.randint(60, 120),
            "notes": random.choice(notes_pool),
        }
        r = post("/sleep", json=payload)
        if r.status_code == 201:
            count += 1
    summary["sleep_sessions"] = count
    print(f"  {count} sleep sessions created")


def seed_health_samples():
    print("\n[6/10] Health samples -- 30 days")
    count = 0
    for d in range(30, 0, -1):
        dt = TODAY - timedelta(days=d)
        samples = [
            {"sample_type": "steps", "value": random.randint(4000, 14000),
             "unit": "count", "recorded_at": iso(dt.replace(hour=23)), "source": "apple_health"},
            {"sample_type": "heart_rate", "value": random.randint(58, 85),
             "unit": "bpm", "recorded_at": iso(dt.replace(hour=12)), "source": "apple_health"},
            {"sample_type": "resting_heart_rate", "value": random.randint(52, 62),
             "unit": "bpm", "recorded_at": iso(dt.replace(hour=7)), "source": "apple_health"},
            {"sample_type": "hrv", "value": random.randint(30, 75),
             "unit": "ms", "recorded_at": iso(dt.replace(hour=7, minute=5)), "source": "apple_health"},
            {"sample_type": "active_calories", "value": random.randint(200, 650),
             "unit": "kcal", "recorded_at": iso(dt.replace(hour=23, minute=30)), "source": "apple_health"},
        ]
        if d % 5 == 0:
            samples.append({"sample_type": "vo2_max", "value": round(random.uniform(42, 48), 1),
                            "unit": "ml/kg/min", "recorded_at": iso(dt.replace(hour=18)), "source": "apple_health"})
        r = post("/health/samples", json=samples)
        if r.status_code == 200:
            body = r.json()
            count += body.get("added", 0)
    summary["health_samples"] = count
    print(f"  {count} health samples created")


def seed_workouts():
    print("\n[7/10] Workouts -- 12 sessions")
    count = 0
    session_types = [
        ("strength", "gym", 55), ("strength", "home", 45), ("cardio", "outdoor", 40),
        ("hiit", "gym", 30), ("flexibility", "home", 25), ("cardio", "outdoor", 50),
        ("strength", "gym", 60), ("strength", "gym", 50), ("cardio", "outdoor", 35),
        ("hiit", "home", 25), ("flexibility", "home", 30), ("strength", "gym", 55),
    ]
    days = sorted(random.sample(range(1, 31), 12), reverse=True)
    for i, d in enumerate(days):
        stype, loc, dur = session_types[i]
        dt = TODAY - timedelta(days=d)
        start = dt.replace(hour=random.choice([7, 8, 17, 18]), minute=0)
        payload = {
            "started_at": iso(start), "session_type": stype, "location": loc,
            "status": "planned", "notes": f"Session {stype} #{i+1}",
            "energy_before": random.randint(5, 9),
        }
        r = post("/sessions", json=payload)
        if r.status_code != 201:
            continue
        sid = r.json().get("id")
        if random.random() < 0.8 and sid:
            end = start + timedelta(minutes=dur)
            update = {
                "ended_at": iso(end), "duration_minutes": dur, "status": "completed",
                "rpe_score": random.randint(5, 9), "calories_burned_kcal": random.randint(150, 500),
                "energy_after": random.randint(4, 8), "notes": f"Completed {stype} session",
            }
            patch(f"/sessions/{sid}", json=update)
        count += 1
    summary["workout_sessions"] = count
    print(f"  {count} workout sessions created")


def seed_nutrition():
    print("\n[8/10] Nutrition -- 7 days")
    count = 0
    breakfasts = [
        ("Tartines beurre confiture + cafe", 380, 8, 55, 14, 2),
        ("Yaourt granola fruits rouges", 320, 12, 45, 10, 4),
        ("Oeufs brouilles pain complet", 410, 22, 35, 20, 3),
        ("Porridge avoine banane miel", 350, 10, 58, 8, 5),
        ("Smoothie proteine fruits", 280, 25, 35, 5, 3),
    ]
    lunches = [
        ("Poulet grille riz basmati legumes", 620, 42, 65, 15, 6),
        ("Salade nicoise complete", 480, 28, 30, 25, 5),
        ("Pates bolognaise maison", 580, 30, 70, 16, 4),
        ("Bowl saumon avocat quinoa", 650, 35, 50, 28, 7),
        ("Steak hache puree haricots verts", 550, 32, 45, 22, 5),
    ]
    dinners = [
        ("Saumon four legumes rotis", 520, 38, 25, 28, 6),
        ("Soupe lentilles pain", 380, 18, 50, 8, 10),
        ("Omelette champignons salade", 420, 25, 15, 28, 4),
        ("Filet cabillaud riz brocoli", 450, 35, 40, 12, 5),
        ("Ratatouille oeuf au plat", 380, 16, 30, 20, 7),
    ]
    snacks = [
        ("Pomme + beurre amande", 200, 5, 25, 10, 3),
        ("Barre proteinee", 180, 15, 20, 5, 2),
        ("Fromage blanc miel", 150, 12, 15, 4, 0),
        None, None,
    ]
    for d in range(7, 0, -1):
        dt = TODAY - timedelta(days=d)
        meals = [
            ("breakfast", 8, random.choice(breakfasts)),
            ("lunch", 12, random.choice(lunches)),
            ("dinner", 19, random.choice(dinners)),
        ]
        snack = random.choice(snacks)
        if snack:
            meals.append(("snack", 16, snack))
        for meal_type, hour, (name, cal, prot, carb, fat, fiber) in meals:
            payload = {
                "logged_at": iso(dt.replace(hour=hour, minute=random.randint(0, 30))),
                "meal_type": meal_type, "meal_name": name,
                "calories": cal + random.randint(-20, 20),
                "protein_g": round(prot + random.uniform(-2, 2), 1),
                "carbs_g": round(carb + random.uniform(-3, 3), 1),
                "fat_g": round(fat + random.uniform(-2, 2), 1),
                "fiber_g": round(fiber + random.uniform(-0.5, 0.5), 1),
                "data_quality": "estimated",
            }
            r = post("/nutrition/entries", json=payload)
            if r.status_code == 201:
                count += 1
    summary["nutrition_entries"] = count
    print(f"  {count} nutrition entries created")


def seed_insights():
    print("\n[9/10] Insights -- trigger engine")
    r = get("/metrics/daily")
    print(f"  Metrics daily: {r.status_code}")
    r = post("/insights/run")
    if r.status_code == 200:
        total = r.json().get("total", 0)
        summary["insights"] = total
        print(f"  {total} insights generated")
    else:
        print(f"  WARN insights: {r.status_code} {r.text[:200]}")
        summary["insights"] = 0


def print_summary():
    print("\n" + "=" * 60)
    print("SEED DATA SUMMARY")
    print("=" * 60)
    for key, val in summary.items():
        label = key.replace("_", " ").title()
        print(f"  {label:.<35s} {val}")
    total = sum(summary.values())
    total_label = "TOTAL"
    print(f"  {total_label:.<35s} {total}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Seed SOMA backend with mock data")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Backend base URL")
    args = parser.parse_args()

    global BASE_URL, API
    BASE_URL = args.base_url
    API = f"{BASE_URL}/api/v1"

    print(f"Seeding SOMA backend at {BASE_URL}...")

    seed_auth()
    seed_profile()
    seed_body_metrics()
    seed_hydration()
    seed_sleep()
    seed_health_samples()
    seed_workouts()
    seed_nutrition()
    seed_insights()
    print_summary()

    print("\nDone! Backend is ready for development.")


if __name__ == "__main__":
    main()
