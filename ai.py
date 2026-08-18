# -*- coding: utf-8 -*-
"""FitPulse AI layer: OpenRouter -> Groq -> friendly fallback."""
import json
import requests
import config


def _call_openrouter(messages, timeout=60):
    key = config.openrouter_key()
    if not key:
        return None
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": "Bearer " + key,
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8520",
        "X-Title": "FitPulse",
    }
    payload = {"model": config.openrouter_model(), "messages": messages, "temperature": 0.7, "max_tokens": 900}
    r = requests.post(url, headers=headers, json=payload, timeout=timeout)
    if r.status_code == 200:
        return r.json()["choices"][0]["message"]["content"]
    return None


def _call_groq(messages, timeout=60):
    key = config.groq_key()
    if not key:
        return None
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": "Bearer " + key, "Content-Type": "application/json"}
    payload = {"model": config.groq_model(), "messages": messages, "temperature": 0.7, "max_tokens": 900}
    r = requests.post(url, headers=headers, json=payload, timeout=timeout)
    if r.status_code == 200:
        return r.json()["choices"][0]["message"]["content"]
    return None


def chat(messages, system=None):
    """Try OpenRouter then Groq. Returns text or None."""
    msgs = ([{"role": "system", "content": system}] if system else []) + messages
    for fn in (_call_openrouter, _call_groq):
        try:
            out = fn(msgs)
            if out and out.strip():
                return out.strip()
        except Exception:
            continue
    return None


def assistant_reply(user_text, profile=None, app_context=None, action_result=None):
    """FitPulse personal AI assistant reply with live app context."""
    stats = ""
    if profile:
        stats = (
            "User profile - name: %s, goal: %s, age: %s, gender: %s, height: %scm, weight: %skg, "
            "activity: %s, experience: %s, days/week: %s, training place: %s, diet: %s, "
            "daily calories target: %s, protein: %s g, carbs: %s g, fat: %s g, BMI: %s, TDEE: %s kcal"
        ) % (
            profile.get("name") or "friend",
            profile.get("goal"), profile.get("age"), profile.get("gender"),
            profile.get("height_cm"), profile.get("weight_kg"),
            profile.get("activity_level"), profile.get("experience"),
            profile.get("days_per_week"), profile.get("workout_pref"),
            profile.get("diet_pref"), profile.get("calories"),
            profile.get("protein"), profile.get("carbs"), profile.get("fat"),
            profile.get("bmi"), profile.get("tdee"),
        )
    system = (
        "You are FitPulse AI, a friendly, warm personal fitness coach inside a fitness app. "
        "Reply in the SAME language the user uses (if they write Urdu/Hindi roman, reply the same way). "
        "Use the user's first name and keep a natural, encouraging, friendly tone (3-6 lines max). "
        "You have LIVE access to the user's real app data below (their plan, scores, XP, streak, weight, "
        "water, calories, badges, week routine). Use it to answer their questions about their details, "
        "scores, routines, progress, or anything in the app. Quote the real numbers, never invent them. "
        "Never round, guess, or make up numbers, XP, or points that are not written in LIVE USER APP DATA "
        "or ACTION JUST PERFORMED — if you are not 100% sure of a number, do not mention it. "
        "If the user asked you to complete/log something in the app and it is listed under 'ACTION JUST "
        "PERFORMED', cheerfully confirm what was done and mention any XP gained. "
        "If the user asks for a workout, suggest 4-6 exercises with sets/reps suited to their profile. "
        "Never give medical diagnoses; advise seeing a doctor for injuries.\n" + stats +
        "\n\nLIVE USER APP DATA:\n" + (app_context or "no data available") +
        "\n\nACTION JUST PERFORMED:\n" + (action_result or "none")
    )
    fallback = (
        "Great question! Based on your profile, stay consistent with your plan, "
        "track your daily plan, hit your water goal, and check your weekly report. "
        "If you want a specific workout or diet advice, ask me in detail!"
    )
    out = chat([{"role": "user", "content": user_text}], system=system)
    return out or fallback


def generate_meal_plan(diet_pref, calories, protein, carbs, fat):
    """AI-generated 7-day meal plan. Returns text. Falls back to templates."""
    system = (
        "You are a nutritionist AI. Create a simple 7-day meal plan table for a person. "
        "Daily target: %s kcal, protein %s g, carbs %s g, fat %s g. Diet preference: %s. "
        "Format: Day 1 (Breakfast: ...; Lunch: ...; Snack: ...; Dinner: ...) one line per day. "
        "Use common, easy foods. Keep it compact (max 12 lines)."
    ) % (calories, protein, carbs, fat, diet_pref)
    out = chat([{"role": "user", "content": "Give me my 7-day meal plan."}], system=system)
    if out and len(out) > 40:
        return out
    return None
