# -*- coding: utf-8 -*-
"""FitPulse AI actions: detect user intent, execute app actions, build full app context."""
import re
import database as db
import fitness_engine as fe
import plan_generator as pg


def _grant_xp(uid, amount):
    import notifications as notif
    prof = db.query_one("SELECT * FROM profiles WHERE user_id=?", (uid,))
    if not prof:
        return []
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
    if fe.xp_into_level(new_xp)["level"] > fe.xp_into_level(old_xp)["level"]:
        notif.notify(uid, "Level up! ⚡", "You reached Level " + str(fe.xp_into_level(new_xp)["level"]) + "!", "level")
    return badges


def _stats(uid, profile):
    today = db.today()
    profile = profile or {}
    weight = db.query_one("SELECT weight_kg FROM weight_logs WHERE user_id=? ORDER BY log_date DESC LIMIT 1", (uid,))
    water = db.query_one("SELECT COALESCE(SUM(ml),0) AS total FROM water_logs WHERE user_id=? AND log_date=?", (uid, today))
    food = db.query_one("SELECT COALESCE(SUM(calories),0) AS cal FROM food_logs WHERE user_id=? AND log_date=?", (uid, today))
    workout_count = db.query_one("SELECT COUNT(*) AS c FROM workout_logs WHERE user_id=?", (uid,))["c"]
    dates = [w["done_at"] for w in db.query("SELECT done_at FROM workout_logs WHERE user_id=?", (uid,))]
    streak = fe.compute_streak(dates)
    xp = db.query_one("SELECT xp FROM profiles WHERE user_id=?", (uid,))
    xp = (xp or {}).get("xp") or 0
    lvl = fe.xp_into_level(xp)
    return {
        "current_weight": weight["weight_kg"] if weight else (profile.get("weight_kg") or 0),
        "start_weight": profile.get("weight_kg") or 0,
        "water_today": water["total"] if water else 0,
        "water_goal": fe.water_goal_ml(profile.get("weight_kg")),
        "calories_today": food["cal"] if food else 0,
        "calories_goal": profile.get("calories") or 0,
        "protein_goal": profile.get("protein") or 0,
        "workout_count": workout_count,
        "streak": streak,
        "xp": xp,
        "level": lvl["level"],
        "xp_into": lvl["into"],
    }


def build_app_context(uid, profile):
    """Gather everything about the user from the app into a readable dict."""
    today = db.today()
    stats = _stats(uid, profile)
    plan = pg.ensure_plan(uid, profile) or {}
    plan_lines = []
    if plan:
        plan_lines.append("Today's plan: %s%s" % (
            plan.get("title", ""), " [COMPLETED]" if plan.get("done") else " [not done yet]"))
        for i, ex in enumerate(plan.get("exercises", []), 1):
            plan_lines.append("  %d. %s - %s x %s (%s)" % (
                i, ex.get("name"), ex.get("sets"), ex.get("reps"), ex.get("category")))
    week_lines = ["Week plan:"]
    for d in pg.get_week(uid):
        week_lines.append("  %s: %s%s" % (d["date"], d["title"], " [done]" if d["done"] else ""))
    badges = [b["name"] for b in db.query("SELECT name FROM badges WHERE user_id=?", (uid,))]
    recent_weights = ["%s: %s kg" % (w["log_date"], w["weight_kg"]) for w in db.query(
        "SELECT log_date, weight_kg FROM weight_logs WHERE user_id=? ORDER BY log_date DESC LIMIT 5", (uid,))]
    workouts_today = db.query_one(
        "SELECT COUNT(*) AS c FROM workout_logs WHERE user_id=? AND date(done_at)=?", (uid, today))["c"]
    return {
        "name": (profile or {}).get("name") or "friend",
        "goal": (profile or {}).get("goal"),
        "stats": stats,
        "plan_today": plan_lines,
        "week": week_lines,
        "badges": badges,
        "recent_weights": recent_weights,
        "workouts_today": workouts_today,
        "water": "%s/%s ml" % (stats["water_today"], stats["water_goal"]),
        "calories_today": stats["calories_today"],
        "calories_goal": stats["calories_goal"],
    }


def context_to_text(ctx):
    s = []
    s.append("Name: %s" % ctx["name"])
    s.append("Goal: %s" % ctx["goal"])
    st = ctx["stats"]
    s.append("XP: %s (level %s, %s/100 into level), streak: %s days, total workouts: %s" % (
        st["xp"], st["level"], st["xp_into"], st["streak"], st["workout_count"]))
    s.append("Weight now: %s kg (started %s kg)" % (st["current_weight"], st["start_weight"]))
    s.append("Water today: %s ml / %s ml" % (st["water_today"], st["water_goal"]))
    s.append("Calories today: %s / %s kcal, protein goal %s g" % (
        st["calories_today"], st["calories_goal"], st["protein_goal"]))
    s.append("Workouts done today: %s" % ctx["workouts_today"])
    s.append("Badges: %s" % (", ".join(ctx["badges"]) if ctx["badges"] else "none yet"))
    if ctx["recent_weights"]:
        s.append("Recent weight logs: " + ", ".join(ctx["recent_weights"]))
    s.extend(ctx["plan_today"])
    s.extend(ctx["week"])
    return "\n".join(s)


def friendly_reply(uid, ctx, action, action_result):
    """Accurate, friendly reply for app actions (numbers straight from the app)."""
    name = ctx["name"]
    st = ctx["stats"]
    typ = (action or {}).get("action")
    if typ == "complete_plan":
        if action_result and "already completed" in action_result:
            return "Hey %s, your daily plan is already marked done today. Great consistency — keep it up! 🎉" % name
        return (action_result or "Daily plan completed! +20 XP") + " Well done, " + name + "! 💪"
    if typ == "log_water":
        return (action_result or "Water logged!") + " Keep hydrating, " + name + "! 💧"
    if typ == "log_weight":
        return (action_result or "Weight logged!") + " Keep tracking, " + name + "! ⚖️"
    if typ == "query_stats":
        goal = (ctx["goal"] or "stay_fit").replace("_", " ").title()
        lines = [
            "Here's your FitPulse snapshot, %s! 📊" % name,
            "🎯 Goal: %s" % goal,
            "⚡ XP: %s · Level %s (%s/100 to next level)" % (st["xp"], st["level"], st["xp_into"]),
            "🔥 Streak: %s days · Total workouts: %s" % (st["streak"], st["workout_count"]),
            "⚖️ Weight: %s kg (started %s kg)" % (st["current_weight"], st["start_weight"]),
            "💧 Water today: %s / %s ml" % (st["water_today"], st["water_goal"]),
            "🍽️ Calories today: %s / %s kcal" % (st["calories_today"], st["calories_goal"]),
            "🏆 Badges: %s" % (", ".join(ctx["badges"]) if ctx["badges"] else "none yet — keep going!"),
        ]
        return "\n".join(lines)
    if typ == "show_plan":
        lines = ["Here's your plan, %s! 🗓️" % name]
        lines.extend(ctx["plan_today"])
        lines.append("")
        lines.extend(ctx["week"])
        return "\n".join(lines)
    return None


# ---------- intent detection ----------

def detect_action(text):
    """Return an action dict for supported intents, else None."""
    t = (text or "").lower().strip()
    if not t:
        return None
    is_question = t.startswith(("how ", "what ", "when ", "why ", "can you tell", "kya", "kaise", "kese", "kesay"))

    # complete today's plan / task
    done_kw = ["complete", "completed", "done", "finish", "finished", "khatam", "khatm", "kar liya", "kr liya",
               "kar diya", "kr diya", "ho gaya", "ho gya", "ho gai", "mukammal", "tamam", "accomplish", "tick", "mark"]
    task_kw = ["task", "plan", "workout", "kasrat", "routine", "exercise", "challenge", "aaj ka", "aj ka", "session"]
    ask_kw = ["give me a", "make a", "create", "suggest", "new plan", "new workout", "plan bnao", "plan banaye",
              "kya plan", "what plan", "plan chahiye", "workout chahiye"]
    has_done = any(w in t for w in done_kw)
    has_task = any(w in t for w in task_kw)
    if has_done and has_task and not is_question and not any(w in t for w in ask_kw):
        return {"action": "complete_plan"}

    # log water
    if ("water" in t or "pani" in t or "paani" in t) and any(
            w in t for w in ["log", "add", "record", "piya", "pee", "drank", "glass", "i drink", "recorded"]):
        return {"action": "log_water", "amount": 250}

    # log weight (number required)
    if "weight" in t or "wazan" in t:
        nums = re.findall(r"\d+(?:\.\d+)?", t)
        if nums and any(w in t for w in ["log", "record", "add", "update", "register", "noted", "save"]):
            return {"action": "log_weight", "weight": float(nums[0])}

    # query stats / scores / progress
    if any(w in t for w in ["stats", "score", "scores", "scoreboard", "xp", "level", "streak", "progress",
                            "report", "badge", "badges", "rank", "points", "records", "rekord", "how am i",
                            "achievement", "my data", "my details", "my numbers"]):
        return {"action": "query_stats"}

    # show today's plan / routine
    plan_ref = ["today", "aaj", "aj", "task", "routine", "schedule", "exercises", "today's"]
    plan_ask = ["show", "dikha", "dikhao", "bata", "bataye", "batana", "tell", "what", "kya", "list",
                "today's", "aaj ka", "aj ka", "kya karna", "kya karun", "what should", "what's"]
    if any(w in t for w in plan_ref) and any(w in t for w in plan_ask):
        return {"action": "show_plan"}
    return None


# ---------- action execution ----------

def execute_action(uid, action):
    """Perform the app action. Returns a confirmation string or None (pure query)."""
    import notifications as notif
    typ = (action or {}).get("action")
    if not typ:
        return None
    if typ == "complete_plan":
        prof = db.query_one("SELECT * FROM profiles WHERE user_id=?", (uid,))
        plan = pg.ensure_plan(uid, prof) or {}
        if plan.get("done"):
            return "Your daily plan '%s' is already completed today. Great consistency!" % plan.get("title")
        if plan.get("exercises"):
            for ex in plan["exercises"]:
                dur = 15
                cal = fe.est_calories_per_exercise(ex.get("name") or "Workout", dur)
                db.execute(
                    "INSERT INTO workout_logs (user_id, exercise, sets, reps, weight_kg, duration_min, calories, done_at) "
                    "VALUES (?,?,?,?,?,?,?,?)",
                    (uid, ex.get("name"), ex.get("sets") or 3, ex.get("reps") or "10-12", 0, dur, cal, db.now()))
        pg.mark_today_done(uid, 1)
        badges = _grant_xp(uid, 20)
        title = plan.get("title") or "today's plan"
        notif.notify(uid, "Daily plan completed! 🎉", title + " is done. +20 XP", "plan", url="/dashboard")
        msg = "Daily plan '%s' marked as completed! +20 XP. Awesome work!" % title
        if badges:
            msg += " You earned badge(s): " + ", ".join(badges) + "."
        return msg
    if typ == "log_water":
        ml = int(action.get("amount") or 250)
        db.execute("INSERT INTO water_logs (user_id, ml, log_date) VALUES (?,?,?)", (uid, ml, db.today()))
        prof = db.query_one("SELECT * FROM profiles WHERE user_id=?", (uid,))
        st = _stats(uid, prof)
        if st["water_today"] >= st["water_goal"]:
            _grant_xp(uid, 10)
            notif.notify(uid, "Water goal reached! 💧", "You hit your daily water target. +10 XP", "water", url="/dashboard")
            return "Logged %s ml water. You reached your daily water goal! +10 XP" % ml
        notif.notify(uid, "Water logged 💧", "+%s ml water added" % ml, "water", url="/dashboard")
        return "Logged %s ml water. You've had %s / %s ml today." % (ml, st["water_today"], st["water_goal"])
    if typ == "log_weight":
        w = float(action.get("weight"))
        db.execute("INSERT INTO weight_logs (user_id, weight_kg, log_date) VALUES (?,?,?)", (uid, w, db.today()))
        db.execute("UPDATE profiles SET weight_kg=? WHERE user_id=?", (w, uid))
        _grant_xp(uid, 5)
        notif.notify(uid, "Weight logged ⚖️", "Your weight is now %s kg (+5 XP)" % w, "weight", url="/weight")
        return "Logged your weight: %s kg. +5 XP" % w
    return None
