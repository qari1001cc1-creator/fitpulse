# -*- coding: utf-8 -*-
"""FitPulse central configuration. Reads .env fresh on every call."""
import os
from dotenv import dotenv_values, load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(BASE_DIR, ".env")
DATA_DIR = os.environ.get("FITPULSE_DATA_DIR") or os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

DB_PATH = os.path.join(DATA_DIR, "fitpulse.db")

load_dotenv(ENV_FILE)


def env_conf():
    try:
        return dotenv_values(ENV_FILE) or {}
    except Exception:
        return {}


def get(key, default=""):
    c = env_conf()
    v = c.get(key)
    if not v:
        v = os.environ.get(key, "")
    return (v or default).strip()


def port():
    try:
        return int(get("PORT", "8520"))
    except Exception:
        return 8520


def secret_key():
    return get("SECRET_KEY", "fitpulse-secret")


def openrouter_key():
    return get("OPENROUTER_API_KEY")


def openrouter_model():
    return get("OPENROUTER_MODEL", "deepseek/deepseek-chat-v3-0324:free")


def groq_key():
    return get("GROQ_API_KEY")


def groq_model():
    return get("GROQ_MODEL", "llama-3.3-70b-versatile")


def usda_key():
    return get("USDA_API_KEY")


def water_goal_ml():
    try:
        return int(get("WATER_GOAL_ML", "3000"))
    except Exception:
        return 3000
