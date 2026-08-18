# -*- coding: utf-8 -*-
"""FitPulse fitness engine: BMI/BMR/TDEE/macros + XP/levels/streaks/badges + quotes."""

ACTIVITY_MULT = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}


def calc_bmi(height_cm, weight_kg):
    try:
        h = float(height_cm) / 100.0
        w = float(weight_kg)
        return round(w / (h * h), 1)
    except Exception:
        return None


def bmi_category(bmi):
    if bmi is None:
        return "Unknown"
    if bmi < 18.5:
        return "Underweight"
    if bmi < 25:
        return "Healthy"
    if bmi < 30:
        return "Overweight"
    return "Obese"


def calc_bmr(weight_kg, height_cm, age, gender):
    """Mifflin-St Jeor equation."""
    w = float(weight_kg)
    h = float(height_cm)
    a = float(age)
    base = 10 * w + 6.25 * h - 5 * a
    return round(base + 5) if str(gender).lower() == "male" else round(base - 161)


def calc_tdee(bmr, activity_level):
    return round(bmr * ACTIVITY_MULT.get(activity_level, 1.375))


def goal_adjust(goal, tdee):
    g = str(goal or "stay_fit")
    if g == "lose_weight":
        return tdee - 500
    if g == "gain_muscle":
        return tdee + 300
    if g == "endurance":
        return tdee + 100
    return tdee


def calc_macros(calories, goal):
    g = str(goal or "stay_fit")
    if g == "lose_weight":
        protein_pct, carb_pct, fat_pct = 0.35, 0.35, 0.30
    elif g == "gain_muscle":
        protein_pct, carb_pct, fat_pct = 0.30, 0.45, 0.25
    else:
        protein_pct, carb_pct, fat_pct = 0.25, 0.45, 0.30
    protein = round(calories * protein_pct / 4)
    carbs = round(calories * carb_pct / 4)
    fat = round(calories * fat_pct / 9)
    return protein, carbs, fat


def water_goal_ml(weight_kg=None):
    """35 ml per kg bodyweight, min 2000 ml."""
    if weight_kg:
        return max(2000, int(float(weight_kg) * 35))
    return 3000


def level_for_xp(xp):
    """Level = floor(xp/100)+1. XP needed to next level."""
    xp = int(xp or 0)
    level = xp // 100 + 1
    return level


def xp_into_level(xp):
    xp = int(xp or 0)
    return {"level": xp // 100 + 1, "into": xp % 100, "needed": 100}


def compute_streak(workout_dates):
    """Consecutive-day streak from a set of YYYY-MM-DD dates (ending today/max)."""
    from datetime import date, timedelta
    days = sorted({str(d)[:10] for d in workout_dates})
    if not days:
        return 0
    dset = set(days)
    streak = 0
    cur = date.today()
    # allow today or yesterday as start (grace for 'not worked out yet today')
    if str(cur) not in dset and str(cur - timedelta(days=1)) in dset:
        cur = cur - timedelta(days=1)
    while str(cur) in dset:
        streak += 1
        cur = cur - timedelta(days=1)
    return streak


def compute_best_streak(workout_dates):
    days = sorted({str(d)[:10] for d in workout_dates})
    if not days:
        return 0
    best = 1
    run = 1
    from datetime import date
    from datetime import timedelta
    prev = None
    for d in days:
        cur = date.fromisoformat(d)
        if prev and (cur - prev).days == 1:
            run += 1
            best = max(best, run)
        else:
            run = 1
        prev = cur
    return best


def check_badges(db, user_id, profile, workout_count, streak):
    """Evaluate and grant badges. Returns list of newly earned badge names."""
    earned = []
    def grant(name):
        exists = db.query_one("SELECT id FROM badges WHERE user_id=? AND name=?", (user_id, name))
        if not exists:
            db.execute("INSERT INTO badges (user_id, name, earned_at) VALUES (?,?,?)",
                       (user_id, name, db.now()))
            earned.append(name)

    workout_count = workout_count or 0
    streak = streak or 0
    if workout_count >= 1:
        grant("First Workout")
    if workout_count >= 10:
        grant("10 Workouts Done")
    if workout_count >= 50:
        grant("Workout Machine")
    if streak >= 3:
        grant("3-Day Streak")
    if streak >= 7:
        grant("7-Day Streak")
    if streak >= 30:
        grant("30-Day Streak")
    if profile and (profile.get("xp") or 0) >= 500:
        grant("Level 5")
    if profile and (profile.get("xp") or 0) >= 1000:
        grant("Level 10")
    return earned


QUOTES = [
    "The body achieves what the mind believes.",
    "Sweat is fat crying.",
    "Don't wish for it, work for it.",
    "Exercise is a celebration of what your body can do.",
    "One workout at a time. One day at a time.",
    "Stronger than yesterday.",
    "The pain you feel today is the strength you feel tomorrow.",
    "Push yourself, because no one else is going to do it for you.",
    "Discipline is choosing what you want most over what you want now.",
    "Your only limit is you.",
    "Small steps every day add up to big results.",
    "Be stronger than your excuses.",
    "Motivation gets you started. Habit keeps you going.",
    "Fall in love with taking care of yourself.",
    "The last three or four reps is what makes the muscle grow.",
    "It never gets easier, you just get better.",
    "Good things come to those who sweat.",
    "Fitness is not about being better than someone else. It's about being better than you used to be.",
    "Do something today that your future self will thank you for.",
    "Consistency beats intensity.",
]


def daily_quote():
    import random
    return random.choice(QUOTES)


def est_calories_per_exercise(exercise_name, duration_min=15):
    """Rough calorie burn estimate (MET ~5-8 depending on category)."""
    name = str(exercise_name or "").lower()
    high = any(k in name for k in ["burpee", "jump", "rope", "mountain", "high knee", "cardio"])
    met = 8.0 if high else 5.5
    return int(met * 3.5 * 70 / 200 * max(duration_min, 5))
