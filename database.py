# -*- coding: utf-8 -*-
"""FitPulse SQLite storage layer (multi-user)."""
import sqlite3
import threading
import config

_lock = threading.Lock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS profiles (
    user_id INTEGER PRIMARY KEY,
    age INTEGER, gender TEXT, height_cm REAL, weight_kg REAL,
    goal TEXT, activity_level TEXT, experience TEXT, days_per_week INTEGER,
    workout_pref TEXT, diet_pref TEXT, unit_system TEXT DEFAULT 'kg',
    bmi REAL, bmr REAL, tdee REAL, calories INTEGER,
    protein INTEGER, carbs INTEGER, fat INTEGER, xp INTEGER DEFAULT 0,
    onboarding_done INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS exercise_library (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT, category TEXT, muscle TEXT, equipment TEXT,
    image_url TEXT, video_url TEXT, difficulty TEXT,
    instructions TEXT, default_sets INTEGER, default_reps TEXT
);
CREATE TABLE IF NOT EXISTS daily_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER, plan_date TEXT, title TEXT, exercises_json TEXT,
    done INTEGER DEFAULT 0, UNIQUE(user_id, plan_date)
);
CREATE TABLE IF NOT EXISTS workout_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER, exercise TEXT, sets INTEGER, reps TEXT,
    weight_kg REAL, duration_min INTEGER, calories INTEGER, done_at TEXT
);
CREATE TABLE IF NOT EXISTS weight_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER, weight_kg REAL, log_date TEXT
);
CREATE TABLE IF NOT EXISTS water_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER, ml INTEGER, log_date TEXT
);
CREATE TABLE IF NOT EXISTS food_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER, meal TEXT, food TEXT, calories INTEGER,
    protein REAL, carbs REAL, fat REAL, log_date TEXT
);
CREATE TABLE IF NOT EXISTS ai_chats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER, message TEXT, reply TEXT, created_at TEXT
);
CREATE TABLE IF NOT EXISTS badges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER, name TEXT, earned_at TEXT, UNIQUE(user_id, name)
);
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER, title TEXT, body TEXT, ntype TEXT,
    icon TEXT, read INTEGER DEFAULT 0, created_at TEXT
);
CREATE TABLE IF NOT EXISTS push_subs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER, endpoint TEXT UNIQUE, p256dh TEXT, auth TEXT, created_at TEXT
);
CREATE TABLE IF NOT EXISTS app_settings (
    user_id INTEGER PRIMARY KEY,
    notifications INTEGER DEFAULT 1,
    unit_system TEXT DEFAULT 'kg',
    tts INTEGER DEFAULT 0
);
"""


def connect():
    return sqlite3.connect(config.DB_PATH)


def init_db():
    with _lock:
        con = connect()
        con.executescript(SCHEMA)
        cols = [r[1] for r in con.execute("PRAGMA table_info(app_settings)")]
        if "tts" not in cols:
            con.execute("ALTER TABLE app_settings ADD COLUMN tts INTEGER DEFAULT 0")
        con.commit()
        con.close()


def execute(sql, params=()):
    with _lock:
        con = connect()
        try:
            cur = con.execute(sql, params)
            con.commit()
            lastrowid = cur.lastrowid
            return lastrowid
        finally:
            con.close()


def query(sql, params=()):
    with _lock:
        con = connect()
        try:
            con.row_factory = sqlite3.Row
            rows = con.execute(sql, params).fetchall()
            return [dict(r) for r in rows]
        finally:
            con.close()


def query_one(sql, params=()):
    rows = query(sql, params)
    return rows[0] if rows else None


def now():
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def today():
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d")
