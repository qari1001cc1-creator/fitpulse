# -*- coding: utf-8 -*-
"""FitPulse weekly meal planner: AI-generated with template fallback."""
import ai

MEAL_TEMPLATES = {
    "vegetarian": {
        "Day 1": "Breakfast: Oats + banana + milk | Lunch: Roti, dal, salad, curd | Snack: Greek yogurt + nuts | Dinner: Paneer bhurji + roti + salad",
        "Day 2": "Breakfast: 2 boiled eggs + toast + tea | Lunch: Rice, chana, veggies, salad | Snack: Apple + peanuts | Dinner: Dal khichdi + curd + salad",
        "Day 3": "Breakfast: Dosa + chutney + buttermilk | Lunch: Roti, rajma, salad, curd | Snack: Banana + almonds | Dinner: Veg stir-fry + rice + salad",
        "Day 4": "Breakfast: Omelette + bread + orange | Lunch: Rice, moong dal, salad | Snack: Smoothie (banana + milk) | Dinner: Chole + 2 roti + salad",
        "Day 5": "Breakfast: Upma + tea | Lunch: Roti, mixed veg, curd, salad | Snack: Corn + lemon | Dinner: Paneer tikka + salad + rice",
        "Day 6": "Breakfast: Idli + sambar | Lunch: Rice, dal, salad, curd | Snack: Dates + walnuts | Dinner: Mixed veg curry + roti + salad",
        "Day 7": "Breakfast: Fruit bowl + yogurt | Lunch: Roti, matar paneer, salad | Snack: Popcorn | Dinner: Veg soup + toast + salad",
    },
    "vegan": {
        "Day 1": "Breakfast: Oats with soy milk + fruit | Lunch: Quinoa + chickpeas + salad | Snack: Nuts + fruit | Dinner: Tofu stir-fry + rice + greens",
        "Day 2": "Breakfast: Smoothie + toast | Lunch: Lentil soup + bread + salad | Snack: Hummus + carrots | Dinner: Soy chunks curry + roti + salad",
        "Day 3": "Breakfast: Poha + peanuts | Lunch: Rice + rajma + salad | Snack: Banana + peanut butter | Dinner: Buddha bowl with tofu + veggies",
        "Day 4": "Breakfast: Chia pudding + fruit | Lunch: Chana masala + roti + salad | Snack: Almonds + dates | Dinner: Dal + brown rice + greens",
        "Day 5": "Breakfast: Overnight oats + berries | Lunch: Sweet potato + beans + salad | Snack: Apple + peanut butter | Dinner: Veg biryani + raita (soy)",
        "Day 6": "Breakfast: Fruit + nuts bowl | Lunch: Lentil tacos + salad | Snack: Rice cakes + hummus | Dinner: Tofu noodles + veggies",
        "Day 7": "Breakfast: Smoothie bowl | Lunch: Chickpea curry + rice + salad | Snack: Popcorn + tea | Dinner: Veg soup + whole wheat toast",
    },
    "non_veg": {
        "Day 1": "Breakfast: 3 egg omelette + toast | Lunch: Chicken breast + rice + salad | Snack: Greek yogurt + nuts | Dinner: Grilled fish + veggies + roti",
        "Day 2": "Breakfast: Oats + egg whites | Lunch: Chicken curry + roti + salad | Snack: Protein shake | Dinner: Tuna salad + bread",
        "Day 3": "Breakfast: Eggs + avocado toast | Lunch: Beef/lean mutton + rice + greens | Snack: Nuts + fruit | Dinner: Chicken tikka + salad + roti",
        "Day 4": "Breakfast: Scrambled eggs + bread | Lunch: Prawns + rice + veggies | Snack: Protein bar | Dinner: Chicken soup + toast",
        "Day 5": "Breakfast: Pancakes (whey) + fruit | Lunch: Grilled chicken + sweet potato | Snack: Almonds + dates | Dinner: Fish curry + rice + salad",
        "Day 6": "Breakfast: Egg sandwich | Lunch: Chicken biryani (light) + salad | Snack: Greek yogurt | Dinner: Egg curry + roti + salad",
        "Day 7": "Breakfast: Big protein breakfast | Lunch: Steak/grilled chicken + salad | Snack: Protein shake | Dinner: Chicken + veggies + rice",
    },
    "keto": {
        "Day 1": "Breakfast: 3 eggs + cheese + avocado | Lunch: Chicken + spinach + olive oil | Snack: Nuts + cheese | Dinner: Salmon + broccoli + butter",
        "Day 2": "Breakfast: Omelette with cheese | Lunch: Beef + cabbage + ghee | Snack: Avocado | Dinner: Chicken thigh + cauliflower rice",
        "Day 3": "Breakfast: Greek yogurt + seeds | Lunch: Paneer + leafy greens | Snack: Boiled eggs | Dinner: Fish + asparagus + butter",
        "Day 4": "Breakfast: Bullet coffee + eggs | Lunch: Mutton + salad + ghee | Snack: Cheese cubes | Dinner: Tofu + zucchini + olive oil",
        "Day 5": "Breakfast: Egg muffins | Lunch: Chicken + broccoli + cheese | Snack: Peanut butter | Dinner: Beef patty + salad",
        "Day 6": "Breakfast: Avocado + eggs | Lunch: Fish curry + greens | Snack: Nuts | Dinner: Chicken + green beans + butter",
        "Day 7": "Breakfast: Keto pancakes (almond flour) | Lunch: Roast chicken + salad | Snack: Cheese + olives | Dinner: Egg curry + spinach",
    },
    "halal": {
        "Day 1": "Breakfast: 3 egg omelette + toast | Lunch: Chicken breast + rice + salad | Snack: Greek yogurt + nuts | Dinner: Grilled fish + veggies + roti",
        "Day 2": "Breakfast: Oats + banana + milk | Lunch: Chicken curry + roti + salad | Snack: Protein shake | Dinner: Tuna salad + bread",
        "Day 3": "Breakfast: Eggs + avocado toast | Lunch: Beef + rice + greens | Snack: Nuts + fruit | Dinner: Chicken tikka + salad + roti",
        "Day 4": "Breakfast: Scrambled eggs + bread | Lunch: Prawns + rice + veggies | Snack: Protein bar | Dinner: Chicken soup + toast",
        "Day 5": "Breakfast: Pancakes (whey) + fruit | Lunch: Grilled chicken + sweet potato | Snack: Almonds + dates | Dinner: Fish curry + rice + salad",
        "Day 6": "Breakfast: Egg sandwich | Lunch: Chicken biryani (light) + salad | Snack: Greek yogurt | Dinner: Egg curry + roti + salad",
        "Day 7": "Breakfast: Big protein breakfast | Lunch: Steak/grilled chicken + salad | Snack: Protein shake | Dinner: Chicken + veggies + rice",
    },
}


def get_meal_plan(diet_pref, calories, protein, carbs, fat):
    """Returns a meal plan dict: ai_text (or None) + table (7 days)."""
    pref = (diet_pref or "halal").lower().replace("-", "_").replace(" ", "_")
    template = MEAL_TEMPLATES.get(pref, MEAL_TEMPLATES["halal"])
    try:
        ai_text = ai.generate_meal_plan(pref, calories, protein, carbs, fat)
    except Exception:
        ai_text = None
    return {"ai_text": ai_text, "table": template}