# -*- coding: utf-8 -*-
"""FitPulse Daily Exercise Plan generator (MANDATORY feature).
Creates a 7-day personalized plan from profile (goal/experience/days/pref)
and stores it in daily_plans for the user. Today's plan is always available."""
import json
import database as db
import exercise_data


def _ex_by(pred, n):
    """Pick up to n exercises matching predicate."""
    pool = [e for e in exercise_data.rows() if pred(e)]
    out = []
    for i in range(min(n, len(pool))):
        e = pool[i]
        out.append({
            "id": e["name"], "name": e["name"], "category": e["category"],
            "muscle": e["muscle"], "equipment": e["equipment"],
            "image_url": e["image_url"], "video_url": e["video_url"],
            "sets": e["default_sets"], "reps": e["default_reps"],
            "difficulty": e["difficulty"], "instructions": e["instructions"],
        })
    return out


def _reps_for_goal(goal):
    if goal == "gain_muscle":
        return "8-12"
    if goal == "strength":
        return "5-8"
    if goal == "lose_weight":
        return "12-15"
    return "10-12"


def _sets_for_exp(experience):
    return 3 if experience == "beginner" else (4 if experience == "advanced" else 3)


def build_week(profile):
    """Generate 7 daily_plans rows for the user. Returns list of {date, title, items}."""
    goal = profile.get("goal") or "stay_fit"
    experience = profile.get("experience") or "beginner"
    days = int(profile.get("days_per_week") or 3)
    pref = profile.get("workout_pref") or "gym"
    reps = _reps_for_goal(goal)
    sets = _sets_for_exp(experience)

    beginner = experience in ("beginner", "intermediate")

    def strength(force, n):
        return _ex_by(lambda e: e["category"] == "Strength" and e["equipment"] == force and e["difficulty"] != "Advanced", n)

    def strength_any(n, skip_muscle=None):
        def pred(e):
            if e["category"] != "Strength":
                return False
            if skip_muscle and e["muscle"] == skip_muscle:
                return False
            return True
        return _ex_by(pred, n)

    def cardio(n):
        return _ex_by(lambda e: e["category"] == "Cardio", n)

    def core(n):
        return _ex_by(lambda e: e["muscle"] in ("Core", "Spine") or e["name"] in ("Plank", "Crunch"), n)

    def yoga(n):
        return _ex_by(lambda e: e["category"] == "Yoga", n)

    full_body = strength_any(6, skip_muscle="Cardio") + cardio(1)
    upper = strength_any(4) + core(1)
    lower = _ex_by(lambda e: e["category"] == "Strength" and e["muscle"] in ("Legs", "Calves", "Glutes", "Lower Back"), 5) + core(1)
    cardio_day = cardio(4) + core(1)

    days_map = {
        1: ("Full Body Day", full_body),
        2: ("Cardio & Core", cardio_day),
        3: ("Upper Body Day", upper),
        4: ("Lower Body Day", lower),
        5: ("Full Body Day", full_body),
        6: ("Active Recovery", yoga(4) + cardio(1)),
        7: ("Rest & Stretch", yoga(3)),
    }

    # choose which days are workout days based on days/week (Mon-Fri pref, weekends rest)
    workout_indexes = [1, 2, 3, 4, 5][:days]

    from datetime import date, timedelta
    start = date.today()
    plans = []
    used_weekday = []
    for offset in range(7):
        d = start + timedelta(days=offset)
        weekday = d.weekday() + 1  # 1=Mon..7=Sun
        is_workout = weekday in workout_indexes
        if is_workout:
            title, items = days_map[weekday]
        else:
            title = "Rest Day"
            items = yoga(2)
        for it in items:
            it["sets"] = sets
            if it["category"] == "Cardio":
                it["reps"] = "30-45 sec" if it["reps"].startswith("30") else it["reps"]
            else:
                it["reps"] = reps
        plans.append({"date": str(d), "title": title, "items": items, "is_workout": is_workout})
    return plans


def ensure_plan(user_id, profile):
    """Generate week plan if missing for today, else reuse stored. Returns today's plan dict."""
    today = db.today()
    existing = db.query_one(
        "SELECT exercises_json, title, done FROM daily_plans WHERE user_id=? AND plan_date=?",
        (user_id, today))
    if existing is None:
        # check if we have any plans at all for this user
        any_plan = db.query_one("SELECT COUNT(*) as c FROM daily_plans WHERE user_id=?", (user_id,))
        if any_plan and any_plan["c"] > 0:
            # regenerate to align with today but preserve history: generate & overwrite future/unknown
            plans = build_week(profile)
            for p in plans:
                exists = db.query_one("SELECT id FROM daily_plans WHERE user_id=? AND plan_date=?",
                                      (user_id, p["date"]))
                if not exists:
                    db.execute("INSERT INTO daily_plans (user_id, plan_date, title, exercises_json) VALUES (?,?,?,?)",
                               (user_id, p["date"], p["title"], json.dumps(p["items"])))
        else:
            plans = build_week(profile)
            for p in plans:
                db.execute("INSERT INTO daily_plans (user_id, plan_date, title, exercises_json) VALUES (?,?,?,?)",
                           (user_id, p["date"], p["title"], json.dumps(p["items"])))
        existing = db.query_one(
            "SELECT exercises_json, title, done FROM daily_plans WHERE user_id=? AND plan_date=?",
            (user_id, today))

    if existing is None:
        return None
    items = json.loads(existing["exercises_json"] or "[]")
    return {"date": today, "title": existing["title"], "done": existing["done"], "exercises": items}


def get_week(user_id):
    """All 7 stored plan days for the user (for the plans page)."""
    from datetime import date, timedelta
    rows = []
    for offset in range(7):
        d = (date.today() + timedelta(days=offset)).strftime("%Y-%m-%d")
        p = db.query_one("SELECT plan_date, title, exercises_json, done FROM daily_plans WHERE user_id=? AND plan_date=?",
                         (user_id, d))
        if p:
            rows.append({"date": p["plan_date"], "title": p["title"],
                         "done": p["done"],
                         "items": json.loads(p["exercises_json"] or "[]")})
        else:
            rows.append({"date": d, "title": "Not scheduled", "done": 0, "items": []})
    return rows


def mark_today_done(user_id, done=1):
    today = db.today()
    db.execute("UPDATE daily_plans SET done=? WHERE user_id=? AND plan_date=?", (1 if done else 0, user_id, today))
