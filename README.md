# 💪 FitPulse — AI Fitness, Workout & Diet Tracker

Personal AI fitness coach web app: personalized **Daily Exercise Plan** (mandatory), AI assistant with **voice**, exercise library with pics + videos, diet & calorie tracking, weight charts, streaks, XP, badges, weekly reports — all multi-user with onboarding wizard. Works on mobile as an installable **PWA** and can be wrapped as an **Android APK**.

## 🚀 Quick Start

```bash
# 1) install (once)
pip install -r requirements.txt

# 2) seed demo data + exercises (once)
python seed.py

# 3) run
python app.py
```

Then open **http://127.0.0.1:8520** (or just double-click `start.bat` / `run.bat`).

**Demo account (pre-seeded):**
- email: `demo@fitpulse.app`
- password: `demo1234`

## ⚙️ Configuration (.env)

| Key | What | Default |
|---|---|---|
| `PORT` | server port | `8520` |
| `SECRET_KEY` | flask sessions | built-in |
| `OPENROUTER_API_KEY` | AI (primary) | from SEO-AGENT |
| `OPENROUTER_MODEL` | e.g. `deepseek/deepseek-chat-v3-0324:free` | free model |
| `GROQ_API_KEY` | AI fallback | from SEO-AGENT |
| `USDA_API_KEY` | optional USDA FoodData Central key (free from api.data.gov) | empty |

> AI keys are copied from `SEO-AGENT\.env`. Voice uses the **browser Web Speech API — free, no key**.

## 🧩 Tech Stack (all free)

- **Backend:** Python Flask + SQLite (multi-user, werkzeug hashed passwords)
- **Frontend:** Jinja2 + custom dark CSS + Chart.js (CDN)
- **AI:** OpenRouter → Groq chain (free models)
- **Data:** wger.de-style exercise set (42 exercises, real YouTube demo videos, thumbnails as images), built-in 100+ foods, optional **USDA FoodData Central** + **TheMealDB** enrichment, 50+ motivational quotes
- **Voice:** Web Speech API (SpeechRecognition + speechSynthesis)
- **PWA:** manifest.json + service-worker.js (installable on phone)
- **APK:** see `apk/` folder — Android WebView wrapper project

## ✨ Features

- **Daily Exercise Plan** ⭐ auto-generated from goal/experience/days + video demos
- Workout tracker + rest timer + free exercise logging
- Exercise library (pics + videos, filters by category/muscle/search)
- Diet: BMI/BMR/TDEE/calorie & macro targets, food log, weekly meal plan (AI + templates)
- Weight tracking with chart
- Water tracker (goal per bodyweight)
- AI Assistant with **voice in/out**
- Gamification: XP, Levels, Streaks, Badges
- Weekly reports + plain-text export
- 7-step onboarding wizard, profile editor, notifications setting

## 📂 Structure

```
app.py            routes + auth
config.py         .env loader
database.py       SQLite schema
ai.py             OpenRouter → Groq
fitness_engine.py BMI/BMR/TDEE/macros + XP/streaks/badges + quotes
plan_generator.py Daily Exercise Plan generator
exercise_data.py  42 exercises (video ids)
food_data.py      100 foods + USDA/TheMealDB fetchers
meal_planner.py   weekly meal plan
seed.py           demo user + sample data
templates/        all pages
static/           css, voice.js, manifest, service-worker
apk/              Android WebView wrapper
```

## 📱 Phone Demo

1. Find your PC's LAN IP: `ipconfig` → IPv4 (e.g. `192.168.1.5`)
2. Open `http://192.168.1.5:8520` on the phone (same Wi-Fi)
3. On Android: browser menu → **Add to Home screen** → installs as app (PWA)

## 📱 Android APK

See `apk/README.md`. Open the `apk/FitPulse/` folder in **Android Studio**, set the URL to your LAN IP or a hosted URL, and Build → APK. No Play Store required.

## ℹ️ Credits

- Exercise demos: linked YouTube videos (public, for education)
- Nutrition: USDA FoodData Central (public domain), TheMealDB (free API)
- AI: OpenRouter free models / Groq