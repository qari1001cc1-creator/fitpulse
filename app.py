# -*- coding: utf-8 -*-
"""FitPulse - AI Fitness, Workout & Diet Tracker. Multi-user Flask app."""
import json
from datetime import date, timedelta
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, Response, flash
from werkzeug.security import generate_password_hash, check_password_hash

import config
import database as db
import exercise_data
import fitness_engine as fe
import plan_generator as pg
import meal_planner as mp
import food_data as fd
import ai as ai_mod
import ai_actions
import notifications as notif

app = Flask(__name__)
app.secret_key = config.secret_key()


@app.context_processor
def _inject_notif_count():
    uid = session.get("user_id")
    if uid:
        row = db.query_one("SELECT COUNT(*) AS c FROM notifications WHERE user_id=? AND read=0", (uid,))
        return {"notif_unread": row["c"] if row else 0}
    return {"notif_unread": 0}


# ---------- helpers ----------

def get_db():
    return db


def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    u = db.query_one("SELECT * FROM users WHERE id=?", (uid,))
    if not u:
        return None
    p = db.query_one("SELECT * FROM profiles WHERE user_id=?", (uid,))
    u["profile"] = p
    return u


def login_required(f):
    @wraps(f)
    def wrapper(*a, **kw):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return f(*a, **kw)
    return wrapper


def onboarding_required(f):
    @wraps(f)
    def wrapper(*a, **kw):
        u = current_user()
        if u and u.get("profile") and u["profile"].get("onboarding_done"):
            return f(*a, **kw)
        return redirect(url_for("onboarding"))
    return wrapper


def _user_stats(uid, profile):
    today = db.today()
    weight = db.query_one("SELECT weight_kg FROM weight_logs WHERE user_id=? ORDER BY log_date DESC LIMIT 1", (uid,))
    water_today = db.query_one("SELECT COALESCE(SUM(ml),0) AS total FROM water_logs WHERE user_id=? AND log_date=?", (uid, today))
    food_today = db.query_one("SELECT COALESCE(SUM(calories),0) AS cal FROM food_logs WHERE user_id=? AND log_date=?", (uid, today))
    workout_count = db.query_one("SELECT COUNT(*) AS c FROM workout_logs WHERE user_id=?", (uid,))["c"]
    workout_dates = [w["done_at"] for w in db.query("SELECT done_at FROM workout_logs WHERE user_id=?", (uid,))]
    streak = fe.compute_streak(workout_dates)
    xp = profile.get("xp") or 0 if profile else 0
    water_goal = fe.water_goal_ml(profile.get("weight_kg") if profile else None)
    return {
        "current_weight": weight["weight_kg"] if weight else (profile.get("weight_kg") if profile else 0),
        "water_today": water_today["total"] if water_today else 0,
        "water_goal": water_goal,
        "calories_today": food_today["cal"] if food_today else 0,
        "calories_goal": profile.get("calories") if profile else 0,
        "workout_count": workout_count,
        "streak": streak,
        "xp": xp,
        "level": fe.xp_into_level(xp),
    }


def _grant_and_add_xp(uid, amount):
    prof = db.query_one("SELECT * FROM profiles WHERE user_id=?", (uid,))
    if prof:
        old_xp = prof.get("xp") or 0
        new_xp = old_xp + amount
        db.execute("UPDATE profiles SET xp=? WHERE user_id=?", (new_xp, uid))
        profile = dict(prof)
        profile["xp"] = new_xp
        count = db.query_one("SELECT COUNT(*) AS c FROM workout_logs WHERE user_id=?", (uid,))
        dates = [w["done_at"] for w in db.query("SELECT done_at FROM workout_logs WHERE user_id=?", (uid,))]
        badges = fe.check_badges(db, uid, profile, count["c"] if count else 0, fe.compute_streak(dates))
        for b in badges:
            notif.notify(uid, "Badge earned! 🏆", "You unlocked the " + b + " badge. Keep it up!", "badge")
        old_level = fe.xp_into_level(old_xp)["level"]
        new_level = fe.xp_into_level(new_xp)["level"]
        if new_level > old_level:
            notif.notify(uid, "Level up! ⚡", "You reached Level " + str(new_level) + "!", "level")
        return badges
    return []


# ---------- landing & auth ----------

@app.route("/")
def landing():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return render_template("landing.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or not password:
            flash("Please fill all fields.", "error")
        elif len(password) < 4:
            flash("Password must be at least 4 characters.", "error")
        elif db.query_one("SELECT id FROM users WHERE email=?", (email,)):
            flash("Email already registered. Try logging in.", "error")
        else:
            uid = db.execute("INSERT INTO users (email, password_hash, name, created_at) VALUES (?,?,?,?)",
                             (email, generate_password_hash(password), name, db.now()))
            session["user_id"] = uid
            return redirect(url_for("onboarding"))
    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        u = db.query_one("SELECT * FROM users WHERE email=?", (email,))
        if u and check_password_hash(u["password_hash"], password):
            session["user_id"] = u["id"]
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


# ---------- onboarding ----------

@app.route("/onboarding", methods=["GET", "POST"])
@login_required
def onboarding():
    uid = session["user_id"]
    prof = db.query_one("SELECT * FROM profiles WHERE user_id=?", (uid,))
    if prof and prof.get("onboarding_done"):
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        age = request.form.get("age")
        gender = request.form.get("gender")
        height = request.form.get("height_cm")
        weight = request.form.get("weight_kg")
        goal = request.form.get("goal")
        activity = request.form.get("activity_level")
        experience = request.form.get("experience")
        days = request.form.get("days_per_week")
        pref = request.form.get("workout_pref")
        diet = request.form.get("diet_pref")

        if not all([age, gender, height, weight, goal, activity, experience, days, pref, diet]):
            flash("Please complete all steps of the wizard.", "error")
            return render_template("onboarding.html", profile=None)

        try:
            age = int(age); height = float(height); weight = float(weight); days = int(days)
        except ValueError:
            flash("Please enter valid numbers.", "error")
            return render_template("onboarding.html", profile=None)

        bmi = fe.calc_bmi(height, weight)
        bmr = fe.calc_bmr(weight, height, age, gender)
        tdee = fe.calc_tdee(bmr, activity)
        calories = fe.goal_adjust(goal, tdee)
        protein, carbs, fat = fe.calc_macros(calories, goal)

        if prof:
            db.execute(
                "UPDATE profiles SET age=?, gender=?, height_cm=?, weight_kg=?, goal=?, activity_level=?, "
                "experience=?, days_per_week=?, workout_pref=?, diet_pref=?, bmi=?, bmr=?, tdee=?, calories=?, "
                "protein=?, carbs=?, fat=?, onboarding_done=1 WHERE user_id=?",
                (age, gender, height, weight, goal, activity, experience, days, pref, diet,
                 bmi, bmr, tdee, calories, protein, carbs, fat, uid))
        else:
            db.execute(
                "INSERT INTO profiles (user_id, age, gender, height_cm, weight_kg, goal, activity_level, "
                "experience, days_per_week, workout_pref, diet_pref, bmi, bmr, tdee, calories, protein, carbs, fat, onboarding_done) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1)",
                (uid, age, gender, height, weight, goal, activity, experience, days, pref, diet,
                 bmi, bmr, tdee, calories, protein, carbs, fat))
        db.execute("INSERT OR IGNORE INTO app_settings (user_id, notifications, unit_system) VALUES (?,1,'kg')", (uid,))
        profile = db.query_one("SELECT * FROM profiles WHERE user_id=?", (uid,))
        pg.ensure_plan(uid, profile)
        return redirect(url_for("dashboard"))
    return render_template("onboarding.html", profile=None)


# ---------- dashboard ----------

@app.route("/dashboard")
@login_required
@onboarding_required
def dashboard():
    uid = session["user_id"]
    u = current_user()
    profile = u["profile"]
    today = db.today()

    # ensure today's plan exists
    today_plan = pg.ensure_plan(uid, profile)

    stats = _user_stats(uid, profile)
    week = pg.get_week(uid)
    today_row = next((w for w in week if w["date"] == today), None)

    weight_trend = [w["weight_kg"] for w in db.query(
        "SELECT weight_kg FROM weight_logs WHERE user_id=? ORDER BY log_date ASC", (uid,))][-10:]

    recent_logs = db.query("SELECT exercise, sets, reps, done_at FROM workout_logs WHERE user_id=? ORDER BY id DESC LIMIT 5", (uid,))

    recent_badges = db.query("SELECT name, earned_at FROM badges WHERE user_id=? ORDER BY id DESC LIMIT 4", (uid,))
    profile.update({"name": u["name"]})

    return render_template("dashboard.html",
                           user=u, profile=profile, stats=stats,
                           today_plan=today_plan, today_row=today_row, week=week,
                           weight_trend=json.dumps(weight_trend),
                           recent_logs=recent_logs, badges=recent_badges,
                           quote=fe.daily_quote())


# ---------- workout ----------

@app.route("/workout")
@login_required
@onboarding_required
def workout():
    uid = session["user_id"]
    u = current_user()
    today_plan = pg.ensure_plan(u["profile"]["user_id"] and uid, u["profile"])
    exercises = db.query("SELECT * FROM exercise_library ORDER BY category, name")
    return render_template("workout.html", user=u, today_plan=today_plan, exercises=exercises)


@app.route("/workout/start", methods=["POST"])
@login_required
@onboarding_required
def workout_start():
    """Log one completed exercise from today's plan."""
    uid = session["user_id"]
    name = request.form.get("exercise", "").strip()
    sets = int(request.form.get("sets") or 3)
    reps = request.form.get("reps", "10-12")
    duration = int(request.form.get("duration_min") or 15)
    weight = float(request.form.get("weight_kg") or 0)
    cal = fe.est_calories_per_exercise(name, duration)
    db.execute(
        "INSERT INTO workout_logs (user_id, exercise, sets, reps, weight_kg, duration_min, calories, done_at) "
        "VALUES (?,?,?,?,?,?,?,?)",
        (uid, name, sets, reps, weight, duration, cal, db.now()))
    badges = _grant_and_add_xp(uid, 10)
    # recompute streak for badges
    dates = [w["done_at"] for w in db.query("SELECT done_at FROM workout_logs WHERE user_id=?", (uid,))]
    cnt = db.query_one("SELECT COUNT(*) AS c FROM workout_logs WHERE user_id=?", (uid,))["c"]
    p = db.query_one("SELECT * FROM profiles WHERE user_id=?", (uid,))
    fe.check_badges(db, uid, p, cnt, fe.compute_streak(dates))
    notif.notify(uid, "Workout logged! 🔥", name + " · " + str(sets) + " sets × " + str(reps) +
                 " (+10 XP)", "workout", url="/workout")
    flash("Workout logged! +10 XP 🔥", "success")
    if badges:
        flash("Badge earned: " + ", ".join(badges), "success")
    return redirect(url_for("workout"))


@app.route("/plan/done", methods=["POST"])
@login_required
@onboarding_required
def plan_done():
    uid = session["user_id"]
    done = request.form.get("done", "1") == "1"
    pg.mark_today_done(uid, 1 if done else 0)
    if done:
        _grant_and_add_xp(uid, 20)
        notif.notify(uid, "Daily plan completed! 🎉", "Today's plan is done. +20 XP", "plan", url="/dashboard")
        flash("Daily plan completed! +20 XP 🎉", "success")
    else:
        flash("Plan marked incomplete.", "info")
    return redirect(url_for("dashboard"))


# ---------- library ----------

@app.route("/library")
@login_required
@onboarding_required
def library():
    uid = session["user_id"]
    u = current_user()
    cat = request.args.get("cat", "").strip()
    muscle = request.args.get("muscle", "").strip()
    q = request.args.get("q", "").strip().lower()
    rows = db.query("SELECT * FROM exercise_library ORDER BY category, name")
    if cat:
        rows = [r for r in rows if r["category"] == cat]
    if muscle:
        rows = [r for r in rows if r["muscle"] == muscle]
    if q:
        rows = [r for r in rows if q in r["name"].lower() or q in r["muscle"].lower()]
    cats = sorted({r["category"] for r in db.query("SELECT category FROM exercise_library")})
    muscles = sorted({r["muscle"] for r in db.query("SELECT muscle FROM exercise_library")})
    return render_template("library.html", user=u, exercises=rows, cats=cats, muscles=muscles,
                           cat=cat, muscle=muscle, q=q)


@app.route("/library/<int:ex_id>")
@login_required
@onboarding_required
def exercise_detail(ex_id):
    uid = session["user_id"]
    u = current_user()
    ex = db.query_one("SELECT * FROM exercise_library WHERE id=?", (ex_id,))
    if not ex:
        flash("Exercise not found.", "error")
        return redirect(url_for("library"))
    return render_template("exercise_detail.html", user=u, ex=ex)


# ---------- diet ----------

@app.route("/diet")
@login_required
@onboarding_required
def diet():
    uid = session["user_id"]
    u = current_user()
    profile = u["profile"]
    today = db.today()
    stats = _user_stats(uid, profile)
    logs = db.query("SELECT * FROM food_logs WHERE user_id=? AND log_date=? ORDER BY id DESC", (uid, today))
    meals = {}
    for l in logs:
        meals.setdefault(l["meal"], []).append(l)
    macros_today = db.query_one(
        "SELECT COALESCE(SUM(protein),0) p, COALESCE(SUM(carbs),0) c, COALESCE(SUM(fat),0) f FROM food_logs WHERE user_id=? AND log_date=?",
        (uid, today))
    plan = mp.get_meal_plan(profile.get("diet_pref"), profile.get("calories"), profile.get("protein"), profile.get("carbs"), profile.get("fat"))
    return render_template("diet.html", user=u, profile=profile, stats=stats,
                           meals=meals, macros=macros_today, plan=plan)


@app.route("/diet/search")
@login_required
def diet_search():
    q = request.args.get("q", "").strip()
    return jsonify(fd.search_combined(q))


@app.route("/diet/add", methods=["POST"])
@login_required
@onboarding_required
def diet_add():
    uid = session["user_id"]
    meal = request.form.get("meal", "snack")
    food = request.form.get("food", "").strip()
    cal = int(request.form.get("calories") or 0)
    p = float(request.form.get("protein") or 0)
    c = float(request.form.get("carbs") or 0)
    fa = float(request.form.get("fat") or 0)
    if food and cal:
        db.execute("INSERT INTO food_logs (user_id, meal, food, calories, protein, carbs, fat, log_date) VALUES (?,?,?,?,?,?,?,?)",
                   (uid, meal, food, cal, p, c, fa, db.today()))
        _grant_and_add_xp(uid, 5)
        notif.notify(uid, "Food logged 🍽️", food + " · " + str(cal) + " kcal (+5 XP)", "diet", url="/diet")
        flash("Food logged! +5 XP", "success")
    else:
        flash("Please select a food.", "error")
    return redirect(url_for("diet"))


# ---------- weight ----------

@app.route("/weight")
@login_required
@onboarding_required
def weight():
    uid = session["user_id"]
    u = current_user()
    profile = u["profile"]
    logs = db.query("SELECT * FROM weight_logs WHERE user_id=? ORDER BY log_date ASC", (uid,))
    series = [{"date": l["log_date"], "weight": l["weight_kg"]} for l in logs]
    return render_template("weight.html", user=u, profile=profile, series=json.dumps(series),
                           stats=_user_stats(uid, profile))


@app.route("/weight/add", methods=["POST"])
@login_required
@onboarding_required
def weight_add():
    uid = session["user_id"]
    w = request.form.get("weight_kg", "").strip()
    if not w:
        flash("Enter your weight.", "error")
        return redirect(url_for("weight"))
    try:
        w = float(w)
    except ValueError:
        flash("Invalid weight.", "error")
        return redirect(url_for("weight"))
    db.execute("INSERT INTO weight_logs (user_id, weight_kg, log_date) VALUES (?,?,?)", (uid, w, db.today()))
    db.execute("UPDATE profiles SET weight_kg=? WHERE user_id=?", (w, uid))
    _grant_and_add_xp(uid, 5)
    notif.notify(uid, "Weight logged ⚖️", "Your weight is now " + str(w) + " kg (+5 XP)", "weight", url="/weight")
    flash("Weight logged! +5 XP", "success")
    return redirect(url_for("weight"))


# ---------- water ----------

@app.route("/water/add", methods=["POST"])
@login_required
@onboarding_required
def water_add():
    uid = session["user_id"]
    ml = int(request.form.get("ml") or 250)
    db.execute("INSERT INTO water_logs (user_id, ml, log_date) VALUES (?,?,?)", (uid, ml, db.today()))
    stats = _user_stats(uid, db.query_one("SELECT * FROM profiles WHERE user_id=?", (uid,)))
    if stats["water_today"] + ml >= stats["water_goal"]:
        _grant_and_add_xp(uid, 10)
        notif.notify(uid, "Water goal reached! 💧", "You hit your daily water target. +10 XP", "water", url="/dashboard")
        flash("Water goal reached! +10 XP 💧", "success")
    else:
        notif.notify(uid, "Water logged 💧", "+" + str(ml) + " ml water added", "water", url="/dashboard")
        flash("+%d ml water 💧" % ml, "success")
    return redirect(request.referrer or url_for("dashboard"))


# ---------- assistant (AI + voice) ----------

@app.route("/assistant")
@login_required
@onboarding_required
def assistant():
    uid = session["user_id"]
    u = current_user()
    chats = db.query("SELECT * FROM ai_chats WHERE user_id=? ORDER BY id DESC LIMIT 20", (uid,))
    chats.reverse()
    settings = db.query_one("SELECT * FROM app_settings WHERE user_id=?", (uid,)) or {}
    return render_template("assistant.html", user=u, chats=chats, settings=settings)


@app.route("/api/chat", methods=["POST"])
@login_required
@onboarding_required
def api_chat():
    uid = session["user_id"]
    u = current_user()
    if request.is_json:
        msg = (request.json or {}).get("message", "")
    else:
        msg = request.form.get("message", "")
    msg = str(msg).strip()
    if not msg:
        return jsonify({"reply": "Please type or say something!"})
    profile = dict(u["profile"] or {})
    profile["name"] = u["name"]
    action = ai_actions.detect_action(msg)
    action_result = None
    if action:
        action_result = ai_actions.execute_action(uid, action)
        u = current_user()
        profile = dict(u["profile"] or {})
        profile["name"] = u["name"]
    ctx = ai_actions.build_app_context(uid, profile)
    reply = None
    if action:
        reply = ai_actions.friendly_reply(uid, ctx, action, action_result)
    if not reply:
        reply = ai_mod.assistant_reply(msg, profile, app_context=ai_actions.context_to_text(ctx),
                                       action_result=action_result)
    db.execute("INSERT INTO ai_chats (user_id, message, reply, created_at) VALUES (?,?,?,?)",
               (uid, msg, reply, db.now()))
    return jsonify({"reply": reply})


@app.route("/api/plan", methods=["GET"])
@login_required
def api_plan_today():
    uid = session["user_id"]
    u = current_user()
    plan = pg.ensure_plan(uid, u["profile"])
    if not plan:
        return jsonify({"error": "No plan"}), 404
    return jsonify(plan)


# ---------- reports ----------

@app.route("/reports")
@login_required
@onboarding_required
def reports():
    uid = session["user_id"]
    u = current_user()
    profile = u["profile"]
    today = date.today()
    start = today - timedelta(days=6)

    workouts = db.query("SELECT * FROM workout_logs WHERE user_id=? AND done_at>=?", (uid, start.strftime("%Y-%m-%d")))
    weight_rows = db.query("SELECT * FROM weight_logs WHERE user_id=? AND log_date>=? ORDER BY log_date ASC", (uid, start.strftime("%Y-%m-%d")))
    water_rows = db.query("SELECT * FROM water_logs WHERE user_id=? AND log_date>=?", (uid, start.strftime("%Y-%m-%d")))
    food_rows = db.query("SELECT * FROM food_logs WHERE user_id=? AND log_date>=?", (uid, start.strftime("%Y-%m-%d")))

    days_workout = len({w["done_at"][:10] for w in workouts})
    total_duration = sum(w["duration_min"] or 0 for w in workouts)
    total_calories = sum(w["calories"] or 0 for w in workouts)
    avg_water = round(sum(w["ml"] for w in water_rows) / 7)
    avg_cal = round(sum(f["calories"] for f in food_rows) / 7)
    weight_change = None
    if len(weight_rows) >= 1:
        first = weight_rows[0]["weight_kg"]
        last = weight_rows[-1]["weight_kg"]
        weight_change = round(last - first, 1)

    badges = db.query("SELECT name, earned_at FROM badges WHERE user_id=? ORDER BY id ASC", (uid,))
    badges_total = db.query_one("SELECT COUNT(*) AS c FROM badges WHERE user_id=?", (uid,))["c"]

    return render_template("reports.html", user=u, profile=profile,
                           stats=_user_stats(uid, profile),
                           days_workout=days_workout, total_duration=total_duration,
                           total_calories=total_calories, avg_water=avg_water, avg_cal=avg_cal,
                           weight_change=weight_change, badges=badges, badges_total=badges_total,
                           week_workouts=[{"date": w["done_at"][:10], "cal": w["calories"] or 0} for w in workouts])


@app.route("/reports/export")
@login_required
@onboarding_required
def reports_export():
    uid = session["user_id"]
    u = current_user()
    lines = ["FITPULSE WEEKLY REPORT", "======================"]
    lines.append("User: %s" % u["name"])
    lines.append("Generated: %s" % db.today())
    lines.append("")
    lines.append("-- Workout Logs (last 7 days) --")
    for w in db.query("SELECT exercise, sets, reps, duration_min, calories, done_at FROM workout_logs WHERE user_id=? ORDER BY done_at DESC LIMIT 20", (uid,)):
        lines.append("%s | %s x %s | %s min | %s kcal" % (w["done_at"][:10], w["exercise"], w["reps"], w["duration_min"] or "-", w["calories"] or 0))
    lines.append("")
    lines.append("-- Weight Logs (last 10) --")
    for w in db.query("SELECT weight_kg, log_date FROM weight_logs WHERE user_id=? ORDER BY log_date DESC LIMIT 10", (uid,)):
        lines.append("%s | %s kg" % (w["log_date"], w["weight_kg"]))
    lines.append("")
    lines.append("-- Badges --")
    for b in db.query("SELECT name, earned_at FROM badges WHERE user_id=? ORDER BY id", (uid,)):
        lines.append("%s | %s" % (b["name"], b["earned_at"]))
    text = "\n".join(lines)
    return Response(text, mimetype="text/plain",
                    headers={"Content-Disposition": "attachment; filename=fitpulse-report.txt"})


# ---------- profile & settings ----------

@app.route("/profile")
@login_required
@onboarding_required
def profile():
    uid = session["user_id"]
    u = current_user()
    profile = u["profile"]
    settings = db.query_one("SELECT * FROM app_settings WHERE user_id=?", (uid,)) or {}
    badges = db.query("SELECT name, earned_at FROM badges WHERE user_id=?", (uid,))
    return render_template("profile.html", user=u, profile=profile, settings=settings, badges=badges,
                           stats=_user_stats(uid, profile))


@app.route("/profile/update", methods=["POST"])
@login_required
def profile_update():
    uid = session["user_id"]
    p = db.query_one("SELECT * FROM profiles WHERE user_id=?", (uid,))
    if not p:
        return redirect(url_for("onboarding"))
    age = request.form.get("age") or p["age"]
    height = request.form.get("height_cm") or p["height_cm"]
    weight = request.form.get("weight_kg") or p["weight_kg"]
    goal = request.form.get("goal") or p["goal"]
    activity = request.form.get("activity_level") or p["activity_level"]
    experience = request.form.get("experience") or p["experience"]
    days = request.form.get("days_per_week") or p["days_per_week"]
    pref = request.form.get("workout_pref") or p["workout_pref"]
    diet = request.form.get("diet_pref") or p["diet_pref"]
    try:
        age = int(age); height = float(height); weight = float(weight); days = int(days)
    except ValueError:
        flash("Invalid values.", "error")
        return redirect(url_for("profile"))
    bmi = fe.calc_bmi(height, weight)
    bmr = fe.calc_bmr(weight, height, age, p.get("gender") or "male")
    tdee = fe.calc_tdee(bmr, activity)
    calories = fe.goal_adjust(goal, tdee)
    protein, carbs, fat = fe.calc_macros(calories, goal)
    db.execute(
        "UPDATE profiles SET age=?, height_cm=?, weight_kg=?, goal=?, activity_level=?, experience=?, "
        "days_per_week=?, workout_pref=?, diet_pref=?, bmi=?, bmr=?, tdee=?, calories=?, protein=?, carbs=?, fat=? WHERE user_id=?",
        (age, height, weight, goal, activity, experience, days, pref, diet,
         bmi, bmr, tdee, calories, protein, carbs, fat, uid))
    profile = db.query_one("SELECT * FROM profiles WHERE user_id=?", (uid,))
    pg.ensure_plan(uid, profile)
    flash("Profile updated and plan regenerated.", "success")
    return redirect(url_for("profile"))


@app.route("/settings/update", methods=["POST"])
@login_required
def settings_update():
    uid = session["user_id"]
    notif = 1 if request.form.get("notifications") == "1" else 0
    tts = 1 if request.form.get("tts") == "1" else 0
    unit = request.form.get("unit_system", "kg")
    db.execute("INSERT INTO app_settings (user_id, notifications, unit_system, tts) VALUES (?,?,?,?) "
               "ON CONFLICT(user_id) DO UPDATE SET notifications=excluded.notifications, unit_system=excluded.unit_system, tts=excluded.tts",
               (uid, notif, unit, tts))
    flash("Settings saved.", "success")
    return redirect(url_for("profile"))


# ---------- notifications ----------

@app.route("/notifications")
@login_required
def notifications_page():
    uid = session["user_id"]
    u = current_user()
    items = db.query("SELECT * FROM notifications WHERE user_id=? ORDER BY id DESC LIMIT 100", (uid,))
    return render_template("notifications.html", user=u, items=items)


@app.route("/api/notifications/unread")
@login_required
def notifications_unread():
    return jsonify({"count": notif.unread_count(session["user_id"])})


@app.route("/api/notifications/read", methods=["POST"])
@login_required
def notifications_read():
    nid = request.form.get("id")
    notif.mark_read(session["user_id"], int(nid) if nid else None)
    return jsonify({"ok": True})


@app.route("/api/push/vapid")
def push_vapid():
    try:
        from webpush_lib import vapid_public_b64url
        return jsonify({"public": vapid_public_b64url()})
    except Exception:
        return jsonify({"public": ""})


@app.route("/api/push/subscribe", methods=["POST"])
@login_required
def push_subscribe():
    data = request.get_json(silent=True) or {}
    endpoint = (data.get("endpoint") or "").strip()
    if endpoint:
        notif.subscribe(session["user_id"], endpoint, data.get("keys", {}).get("p256dh", ""),
                        data.get("keys", {}).get("auth", ""))
    return jsonify({"ok": True})


# ---------- misc ----------

@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", code=404, msg="Page not found"), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("error.html", code=500, msg="Something went wrong on the server."), 500


def _startup():
    try:
        import hf_backup
        hf_backup.start()
    except Exception as e:  # pragma: no cover
        print("backup init error:", e)
    db.init_db()
    try:
        import seed
        seed.seed_exercises()
        seed.seed_demo()
    except Exception as e:  # pragma: no cover
        print("startup seed error:", e)


_startup()

if __name__ == "__main__":
    print("FitPulse running at http://127.0.0.1:%s" % config.port())
    app.run(host="0.0.0.0", port=config.port(), debug=False, threaded=True)