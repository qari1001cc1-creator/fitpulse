# -*- coding: utf-8 -*-
"""FitPulse food database (built-in 100 foods) + USDA/TheMealDB live fetchers.
Built-in fallback keeps the app working even offline. Values are per serving."""

# (name, calories, protein_g, carbs_g, fat_g, meal_tags)
FOODS = [
    # Breakfast
    ("Oats (cooked 1 bowl)", 150, 5, 27, 3, "breakfast"),
    ("Egg (1 boiled)", 78, 6, 1, 5, "breakfast"),
    ("Egg White (3)", 51, 11, 1, 0, "breakfast"),
    ("Omelette (2 eggs)", 187, 13, 1, 14, "breakfast"),
    ("Bread (1 slice whole wheat)", 81, 4, 14, 1, "breakfast"),
    ("Brown Bread (1 slice)", 70, 3, 12, 1, "breakfast"),
    ("Banana (1 medium)", 105, 1, 27, 0, "breakfast,snack"),
    ("Milk (1 glass full cream)", 149, 8, 12, 8, "breakfast,snack"),
    ("Milk (skim, 1 glass)", 83, 8, 12, 0, "breakfast,snack"),
    ("Curd/Yogurt (1 bowl)", 100, 9, 7, 4, "breakfast,snack"),
    ("Greek Yogurt (100g)", 59, 10, 4, 0, "breakfast,snack"),
    ("Cornflakes (1 bowl)", 110, 2, 25, 0, "breakfast"),
    ("Peanut Butter (1 tbsp)", 94, 4, 3, 8, "breakfast,snack"),
    ("Honey (1 tbsp)", 64, 0, 17, 0, "breakfast"),
    ("Apple (1 medium)", 95, 0, 25, 0, "snack"),
    ("Orange (1 medium)", 62, 1, 15, 0, "snack"),
    ("Dates (3)", 67, 1, 18, 0, "snack"),
    ("Almonds (10)", 69, 3, 2, 6, "snack"),
    ("Walnuts (4 halves)", 65, 2, 1, 7, "snack"),
    ("Mixed Nuts (1 handful)", 173, 5, 6, 16, "snack"),
    # Rice & staples
    ("White Rice (cooked 1 cup)", 205, 4, 45, 0, "lunch,dinner"),
    ("Brown Rice (cooked 1 cup)", 218, 5, 46, 2, "lunch,dinner"),
    ("Roti/Chapati (1)", 104, 3, 20, 1, "lunch,dinner"),
    ("Paratha (1 plain)", 260, 5, 33, 11, "lunch,dinner"),
    ("Chapati Whole Wheat (1)", 100, 4, 19, 1, "lunch,dinner"),
    ("Pasta (cooked 1 cup)", 221, 8, 43, 1, "lunch,dinner"),
    ("Potato (boiled 1 medium)", 134, 3, 30, 0, "lunch,dinner"),
    ("Sweet Potato (1 medium)", 103, 2, 24, 0, "lunch,dinner"),
    ("Poha (1 bowl)", 250, 5, 45, 5, "breakfast,lunch"),
    ("Upma (1 bowl)", 180, 5, 30, 5, "breakfast"),
    ("Idli (2)", 116, 4, 25, 0, "breakfast"),
    ("Dosa (1 plain)", 133, 3, 25, 2, "breakfast"),
    # Proteins
    ("Chicken Breast (grilled 100g)", 165, 31, 0, 4, "lunch,dinner"),
    ("Chicken Leg (roasted 100g)", 184, 24, 0, 9, "lunch,dinner"),
    ("Chicken Curry (1 bowl)", 280, 22, 8, 17, "lunch,dinner"),
    ("Egg Curry (1 egg)", 120, 6, 2, 9, "lunch,dinner"),
    ("Fish (grilled 100g)", 206, 22, 0, 12, "lunch,dinner"),
    ("Salmon (100g)", 208, 20, 0, 13, "lunch,dinner"),
    ("Tuna (canned 100g)", 132, 28, 0, 1, "lunch,dinner"),
    ("Beef (lean 100g)", 250, 26, 0, 15, "lunch,dinner"),
    ("Mutton Curry (1 bowl)", 320, 22, 5, 24, "lunch,dinner"),
    ("Prawns (100g)", 99, 24, 0, 0, "lunch,dinner"),
    ("Tofu (100g)", 76, 8, 2, 5, "lunch,dinner"),
    ("Paneer (100g)", 265, 18, 4, 20, "lunch,dinner"),
    ("Chana Dal (cooked 1 cup)", 269, 15, 45, 4, "lunch,dinner"),
    ("Moong Dal (cooked 1 cup)", 212, 14, 39, 1, "lunch,dinner"),
    ("Rajma (cooked 1 cup)", 225, 15, 40, 1, "lunch,dinner"),
    ("Chickpeas/Chole (1 cup)", 269, 15, 45, 4, "lunch,dinner"),
    ("Lentils (cooked 1 cup)", 230, 18, 40, 1, "lunch,dinner"),
    ("Soy Chunks (50g)", 173, 26, 14, 0, "lunch,dinner"),
    ("Sausage (1)", 170, 7, 2, 14, "breakfast"),
    ("Salami (2 slices)", 120, 6, 1, 10, "lunch"),
    # Vegetables & salads
    ("Mixed Salad (1 bowl)", 45, 2, 9, 0, "lunch,dinner"),
    ("Broccoli (1 cup)", 31, 3, 6, 0, "lunch,dinner"),
    ("Spinach (1 cup)", 7, 1, 1, 0, "lunch,dinner"),
    ("Carrot (1 medium)", 25, 1, 6, 0, "snack,lunch"),
    ("Cucumber (1/2)", 16, 1, 4, 0, "snack,lunch"),
    ("Tomato (1 medium)", 22, 1, 5, 0, "lunch"),
    ("Onion (1/2 medium)", 30, 1, 7, 0, "lunch"),
    ("Cauliflower (1 cup)", 27, 2, 5, 0, "lunch,dinner"),
    ("Cabbage (1 cup)", 22, 1, 5, 0, "lunch,dinner"),
    ("Mushrooms (1 cup)", 15, 2, 2, 0, "lunch,dinner"),
    ("Peas (1/2 cup)", 67, 5, 12, 0, "lunch,dinner"),
    ("Corn (1/2 cup)", 66, 2, 16, 1, "lunch,dinner"),
    ("Bell Pepper (1)", 25, 1, 6, 0, "lunch,dinner"),
    ("Avocado (1/2)", 120, 1, 6, 11, "snack,lunch"),
    ("Olive Oil (1 tbsp)", 119, 0, 0, 14, "lunch,dinner"),
    ("Butter (1 tbsp)", 102, 0, 0, 12, "breakfast"),
    ("Ghee (1 tbsp)", 120, 0, 0, 14, "lunch,dinner"),
    # Snacks & drinks
    ("Samosa (1)", 262, 4, 30, 14, "snack"),
    ("Pakora (2)", 180, 4, 18, 10, "snack"),
    ("French Fries (medium)", 365, 4, 48, 17, "snack"),
    ("Biscuit (1)", 50, 1, 7, 2, "snack"),
    ("Chips (small pack)", 152, 2, 15, 10, "snack"),
    ("Popcorn (air-popped 1 cup)", 31, 1, 6, 0, "snack"),
    ("Ice Cream (1 scoop)", 137, 2, 16, 7, "snack"),
    ("Dark Chocolate (30g)", 170, 2, 13, 12, "snack"),
    ("Milk Chocolate (30g)", 161, 2, 18, 9, "snack"),
    ("Protein Bar (1)", 200, 20, 22, 7, "snack"),
    ("Protein Shake (1 scoop water)", 120, 24, 3, 2, "snack"),
    ("Lassi (sweet 1 glass)", 180, 7, 30, 3, "snack"),
    ("Buttermilk/Chaas (1 glass)", 40, 2, 5, 1, "snack"),
    ("Orange Juice (1 glass)", 112, 2, 26, 0, "breakfast"),
    ("Cola (1 can)", 140, 0, 39, 0, "snack"),
    ("Green Tea (1 cup)", 2, 0, 0, 0, "snack"),
    ("Coffee (black)", 2, 0, 0, 0, "snack"),
    ("Tea with Milk (1 cup)", 30, 1, 5, 1, "snack"),
    # Fast food
    ("Burger (cheeseburger)", 300, 15, 33, 12, "lunch,dinner"),
    ("Pizza (1 slice)", 285, 12, 36, 10, "lunch,dinner"),
    ("Shawarma (1)", 400, 20, 40, 17, "lunch,dinner"),
    ("Biryani (1 plate)", 580, 25, 65, 25, "lunch,dinner"),
    ("Haleem (1 bowl)", 350, 25, 30, 14, "lunch,dinner"),
    ("Karahi Chicken (1 bowl)", 450, 30, 10, 32, "lunch,dinner"),
    ("Nihari (1 bowl)", 350, 25, 12, 22, "lunch,dinner"),
    ("Dal Chawal (1 plate)", 420, 16, 78, 5, "lunch,dinner"),
    ("Kheer (1 bowl)", 250, 8, 40, 7, "snack"),
    ("Gulab Jamun (1)", 150, 1, 25, 6, "snack"),
]


def search_foods(q, limit=12):
    q = q.lower().strip()
    if not q:
        return []
    scored = []
    for f in FOODS:
        name, cal, p, c, fa, tags = f
        if q in name.lower():
            scored.append((2, f))
        elif q in tags:
            scored.append((1, f))
        elif any(w in name.lower() for w in q.split()):
            scored.append((0.5, f))
    scored.sort(key=lambda x: -x[0])
    return [_food_dict(f) for _, f in scored[:limit]]


def _food_dict(f):
    name, cal, p, c, fa, tags = f
    return {"name": name, "calories": cal, "protein": p, "carbs": c, "fat": fa, "tags": tags}


def all_foods():
    return [_food_dict(f) for f in FOODS]


def usda_search(q):
    """USDA FoodData Central live search. Returns list of dicts or [] on failure."""
    import requests
    import config
    key = config.usda_key()
    if not key:
        return []
    url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    try:
        r = requests.get(url, params={"query": q, "pageSize": 5, "api_key": key}, timeout=10)
        if r.status_code != 200:
            return []
        out = []
        for item in r.json().get("foods", [])[:5]:
            nutrients = {n.get("nutrientName", ""): n for n in item.get("foodNutrients", [])}
            def val(keyname):
                n = nutrients.get(keyname)
                return round(n.get("value", 0)) if n else 0
            out.append({
                "name": item.get("description", q),
                "calories": val("Energy"),
                "protein": val("Protein"),
                "carbs": val("Carbohydrate, by difference"),
                "fat": val("Total lipid (fat)"),
                "tags": "usda",
            })
        return out
    except Exception:
        return []


def themdb_search(q):
    """TheMealDB recipe search - returns meals with image + video URL."""
    import requests
    import json
    try:
        r = requests.get("https://www.themealdb.com/api/json/v1/1/search.php", params={"s": q}, timeout=10)
        if r.status_code != 200:
            return []
        out = []
        for m in r.json().get("meals", [])[:6]:
            out.append({
                "name": m.get("strMeal", q),
                "image": m.get("strMealThumb", ""),
                "video": m.get("strYoutube", ""),
                "category": m.get("strCategory", ""),
                "area": m.get("strArea", ""),
            })
        return out
    except Exception:
        return []


def search_combined(q):
    """Local foods first, then USDA + TheMealDB. Returns dict."""
    return {
        "foods": search_foods(q),
        "usda": usda_search(q),
        "recipes": themdb_search(q),
    }
