# -*- coding: utf-8 -*-
"""FitPulse seed: exercise library (42), demo account + realistic sample data.
Run once:  python seed.py
"""
import json
from datetime import date, timedelta
import random
from werkzeug.security import generate_password_hash
import database as db
import exercise_data
import fitness_engine
import plan_generator

DEMO_EMAIL = "demo@fitpulse.app"
DEMO_PASS = "demo1234"
DEMO_NAME = "Ahmed Demo"


def seed_exercises():
    if db.query_one("SELECT COUNT(*) AS c FROM exercise_library")["c"] > 0:
        return False
    for e in exercise_data.rows():
        db.execute(
            "INSERT INTO exercise_library (name, category, muscle, equipment, image_url, video_url, difficulty, instructions, default_sets, default_reps) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (e["name"], e["category"], e["muscle"], e["equipment"], e["image_url"],
             e["video_url"], e["difficulty"], e["instructions"], e["default_sets"], e["default_reps"]))
    return True


def seed_demo():
    ex = db.query_one("SELECT * FROM users WHERE email=?", (DEMO_EMAIL,))
    if ex:
        return False

    uid = db.execute("INSERT INTO users (email, password_hash, name, created_at) VALUES (?,?,?,?)",
                     (DEMO_EMAIL, generate_password_hash(DEMO_PASS), DEMO_NAME, db.now()))
    age = 24
    gender = "male"
    height = 172.0
    weight = 84.0
    goal = "lose_weight"
    activity = "moderate"
    experience = "intermediate"
    days = 4
    pref = "gym"
    diet = "halal"

    bmi = fitness_engine.calc_bmi(height, weight)
    bmr = fitness_engine.calc_bmr(weight, height, age, gender)
    tdee = fitness_engine.calc_tdee(bmr, activity)
    calories = fitness_engine.goal_adjust(goal, tdee)
    protein, carbs, fat = fitness_engine.calc_macros(calories, goal)

    db.execute(
        "INSERT INTO profiles (user_id, age, gender, height_cm, weight_kg, goal, activity_level, experience, "
        "days_per_week, workout_pref, diet_pref, unit_system, bmi, bmr, tdee, calories, protein, carbs, fat, xp, onboarding_done) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1)",
        (uid, age, gender, height, weight, goal, activity, experience, days, pref, diet,
         "kg", bmi, bmr, tdee, calories, protein, carbs, fat, 850))
    db.execute("INSERT INTO app_settings (user_id, notifications, unit_system) VALUES (?,1,'kg')", (uid,))

    # Sample exercise logs: 4 workout days/week for ~5 weeks, ending today
    random.seed(42)
    exercises = [e["name"] for e in db.query("SELECT name FROM exercise_library LIMIT 20")]
    today = date.today()
    for back in range(0, 35):
        d = today - timedelta(days=back)
        if d.weekday() in (0, 2, 4, 5):
            for _ in range(random.randint(4, 6)):
                name = random.choice(exercises)
                sets = random.randint(3, 4)
                reps = random.choice(["10-12", "12-15", "8-10"])
                w = random.choice([0, 0, 5, 10, 20, 40])
                db.execute(
                    "INSERT INTO workout_logs (user_id, exercise, sets, reps, weight_kg, duration_min, calories, done_at) "
                    "VALUES (?,?,?,?,?,?,?,?)",
                    (uid, name, sets, reps, w, random.randint(10, 45),
                     fitness_engine.est_calories_per_exercise(name, random.randint(15, 40)),
                     d.strftime("%Y-%m-%d %H:%M:%S")))

    # Weight log: decline from 84 -> 81.4 over last 5 weeks (every 3 days)
    base = 84.0
    for back in range(0, 34, 3):
        d = today - timedelta(days=back)
        wgt = round(base - back * 0.06, 1)
        db.execute("INSERT INTO weight_logs (user_id, weight_kg, log_date) VALUES (?,?,?)", (uid, wgt, str(d)))

    # Water logs
    for back in range(0, 14):
        d = today - timedelta(days=back)
        db.execute("INSERT INTO water_logs (user_id, ml, log_date) VALUES (?,?,?)",
                   (uid, random.randint(1800, 3000), str(d)))

    # Food logs
    import food_data as fd
    meals = ["breakfast", "lunch", "dinner"]
    for back in range(0, 14):
        d = today - timedelta(days=back)
        for meal in meals:
            picks = fd.search_foods(meal, limit=6)
            if picks:
                f = random.choice(picks)
                db.execute(
                    "INSERT INTO food_logs (user_id, meal, food, calories, protein, carbs, fat, log_date) "
                    "VALUES (?,?,?,?,?,?,?,?)",
                    (uid, meal, f["name"], f["calories"], f["protein"], f["carbs"], f["fat"], str(d)))

    # Some AI chat history
    db.execute("INSERT INTO ai_chats (user_id, message, reply, created_at) VALUES (?,?,?,?)",
               (uid, "How can I lose weight faster?",
                "Stay consistent with your daily plan, hit your protein goal, walk 8-10k steps, and sleep 7-8 hours. Calorie deficit drives fat loss - you're on track!",
                db.now()))

    # Some badges
    for b in ["First Workout", "10 Workouts Done", "3-Day Streak"]:
        db.execute("INSERT INTO badges (user_id, name, earned_at) VALUES (?,?,?)", (uid, b, db.now()))

    # Generate weekly daily plan
    profile = db.query_one("SELECT * FROM profiles WHERE user_id=?", (uid,))
    plan_generator.ensure_plan(uid, profile)

    return True


def run():
    db.init_db()
    e = seed_exercises()
    d = seed_demo()
    print("Exercises seeded:", "yes" if e else "already present")
    print("Demo user seeded:", "yes" if d else "already present")
    print("Demo login:", DEMO_EMAIL, "/", DEMO_PASS)


if __name__ == "__main__":
    run()