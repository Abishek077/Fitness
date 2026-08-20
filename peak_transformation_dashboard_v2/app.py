import os
import csv
import io
from datetime import date, datetime, timedelta

from flask import Flask, render_template, request, jsonify, send_file
import mysql.connector
from mysql.connector import Error
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import cm

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this-secret-key")

DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", "12345678"),
    "database": os.getenv("MYSQL_DATABASE", "peak_transformation"),
}

START_DATE = date(2026, 8, 20)
END_DATE = date(2026, 12, 31)

PROFILE = {
    "name": "Abishek Raghav",
    "age": 25,
    "sex": "male",
    "height_cm": 165.1,
    "starting_weight_kg": 76.0,
    "target_weight_kg": 68.0,
    "daily_step_target": 9000,
    "water_target_l": 4.0,
}

ACTIVITIES = [
    ("hot_water", "Morning Hot Water"),
    ("ice_facewash", "Ice Water Face Wash"),
    ("black_coffee", "Black Coffee"),
    ("workout", "Workout Completed"),
    ("steps_done", "Step Target"),
    ("diet", "Diet Followed"),
    ("water", "Water Target"),
    ("creatine", "Creatine"),
    ("psyllium", "Psyllium Husk"),
    ("shilajit", "Shilajit"),
    ("yoga", "10-Min Yoga / Mind Relax"),
    ("multivitamin", "Multivitamin"),
    ("fish_oil", "Fish Oil"),
    ("calcium_magnesium", "Calcium + Magnesium"),
    ("brushing", "Night Brushing"),
]

ACTIVITY_FIELDS = [k for k, _ in ACTIVITIES]

WORKOUTS = {
    "Monday": [
        ("Bench Press", "3 × 6–8"),
        ("Incline Dumbbell Press", "3 × 8–10"),
        ("Shoulder Press", "3 × 8–10"),
        ("Lateral Raise", "3 × 12–15"),
        ("Triceps Rope Pushdown", "3 × 10–12"),
        ("Overhead Triceps Extension", "2 × 12–15"),
        ("Incline Walk", "10–15 min"),
    ],
    "Tuesday": [
        ("Lat Pulldown", "3 × 8–10"),
        ("Seated Cable Row", "3 × 8–10"),
        ("Chest-Supported Row", "3 × 10–12"),
        ("Face Pull", "3 × 12–15"),
        ("Incline Dumbbell Curl", "3 × 10–12"),
        ("Hammer Curl", "2 × 10–12"),
        ("Incline Walk", "10 min"),
    ],
    "Wednesday": [
        ("Squat / Leg Press", "3 × 6–10"),
        ("Romanian Deadlift", "3 × 8–10"),
        ("Leg Press", "3 × 10–12"),
        ("Leg Curl", "3 × 10–12"),
        ("Calf Raise", "3 × 12–15"),
        ("Plank", "3 × 30–60 sec"),
        ("Hanging / Knee Leg Raise", "3 × 10–15"),
        ("Easy Walk", "10 min"),
    ],
    "Thursday": [
        ("Bench Press", "3 × 5–6"),
        ("Barbell / Cable Row", "3 × 6–8"),
        ("Overhead Press", "3 × 6–8"),
        ("Lat Pulldown", "3 × 8–10"),
        ("Lateral Raise", "2 × 12–15"),
        ("Triceps Pushdown", "2 × 10–12"),
        ("Dumbbell Curl", "2 × 10–12"),
    ],
    "Friday": [
        ("Incline Dumbbell Press", "3 × 10–12"),
        ("Cable Fly", "3 × 12–15"),
        ("Wide-Grip Row", "3 × 10–12"),
        ("Lateral Raise", "3 × 12–15"),
        ("Rear Delt Fly", "3 × 12–15"),
        ("Biceps Curl", "3 × 10–15"),
        ("Triceps Extension", "3 × 10–15"),
        ("Incline Walk", "10–15 min"),
    ],
    "Saturday": [
        ("Brisk Walking", "45–60 min"),
        ("Steps", "9,000–10,000"),
        ("Stretching / Mobility", "10–15 min"),
    ],
    "Sunday": [
        ("Rest / Recovery", "No heavy workout"),
        ("Light Mobility", "Optional"),
    ],
}

workout_images = {
    "Monday": "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?auto=format&fit=crop&w=1400&q=90",
    "Tuesday": "https://images.unsplash.com/photo-1581009146145-b5ef050c2e1e?auto=format&fit=crop&w=1400&q=90",
    "Wednesday": "https://images.unsplash.com/photo-1434596922112-19c563067271?auto=format&fit=crop&w=1400&q=90",
    "Thursday": "https://images.unsplash.com/photo-1583454110551-21f2fa2afe61?auto=format&fit=crop&w=1400&q=90",
    "Friday": "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?auto=format&fit=crop&w=1400&q=90",
    "Saturday": "https://images.unsplash.com/photo-1552674605-db6ffd4facb5?auto=format&fit=crop&w=1400&q=90",
    "Sunday": "https://images.unsplash.com/photo-1506126613408-eca07ce68773?auto=format&fit=crop&w=1400&q=90",
}

diet_images = {
    "Breakfast": "https://images.unsplash.com/photo-1494859802809-d069c3b71a8a?auto=format&fit=crop&w=1400&q=90",
    "Mid Morning": "https://images.unsplash.com/photo-1488477181946-6428a0291777?auto=format&fit=crop&w=1400&q=90",
    "Lunch": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=1400&q=90",
    "Evening Snack": "https://images.unsplash.com/photo-1599599810694-b5ac3b7f4b01?auto=format&fit=crop&w=1400&q=90",
    "Dinner": "https://images.unsplash.com/photo-1532550907401-a500c9a57435?auto=format&fit=crop&w=1400&q=90",
}

FOOD_DB = {
    "super you whey protein": {"cal": 120, "protein": 27, "carbs": 3, "fat": 1, "fiber": 0},
    "whey protein": {"cal": 120, "protein": 24, "carbs": 3, "fat": 1.5, "fiber": 0},
    "oats": {"cal": 190, "protein": 6.5, "carbs": 32, "fat": 3.5, "fiber": 5},
    "medium banana": {"cal": 105, "protein": 1.3, "carbs": 27, "fat": 0.4, "fiber": 3.1},
    "chia seeds": {"cal": 50, "protein": 1.7, "carbs": 4, "fat": 3.1, "fiber": 3.4},
    "whole egg": {"cal": 72, "protein": 6.3, "carbs": 0.4, "fat": 4.8, "fiber": 0},
    "egg whites": {"cal": 34, "protein": 7.2, "carbs": 0.5, "fat": 0.1, "fiber": 0},
    "cooked rice": {"cal": 130, "protein": 2.7, "carbs": 28, "fat": 0.3, "fiber": 0.4},
    "vegetables / salad": {"cal": 40, "protein": 2, "carbs": 7, "fat": 0.3, "fiber": 3},
    "curd": {"cal": 90, "protein": 5, "carbs": 6, "fat": 4.5, "fiber": 0},
    "soya chunks": {"cal": 170, "protein": 26, "carbs": 15, "fat": 0.5, "fiber": 6.5},
    "fruit / buttermilk": {"cal": 80, "protein": 2, "carbs": 15, "fat": 1, "fiber": 2},
    "chicken breast": {"cal": 275, "protein": 52, "carbs": 0, "fat": 6, "fiber": 0},
    "milk": {"cal": 120, "protein": 6.4, "carbs": 9.6, "fat": 6.4, "fiber": 0},
    "black coffee": {"cal": 5, "protein": 0.3, "carbs": 0, "fat": 0, "fiber": 0},
    "apple": {"cal": 95, "protein": 0.5, "carbs": 25, "fat": 0.3, "fiber": 4.4},
    "paneer": {"cal": 265, "protein": 18, "carbs": 1.2, "fat": 20, "fiber": 0},
    "dal": {"cal": 120, "protein": 7, "carbs": 18, "fat": 2, "fiber": 5},
    "roti": {"cal": 120, "protein": 3.5, "carbs": 22, "fat": 2.5, "fiber": 2.5},
    "peanut butter": {"cal": 95, "protein": 4, "carbs": 3, "fat": 8, "fiber": 1},
    "almonds": {"cal": 80, "protein": 3, "carbs": 3, "fat": 7, "fiber": 1.5},
}

FOOD_SERVING_GRAMS = {
    "super you whey protein": 30, "whey protein": 30, "oats": 50,
    "medium banana": 118, "chia seeds": 10, "whole egg": 50,
    "egg whites": 66, "cooked rice": 100, "vegetables / salad": 100,
    "curd": 150, "soya chunks": 50, "fruit / buttermilk": 150,
    "chicken breast": 250, "milk": 200, "black coffee": 240,
    "apple": 180, "paneer": 100, "dal": 100, "roti": 40,
    "peanut butter": 16, "almonds": 14,
}

DIET = [
    ("Breakfast", "SuperYou whey protein", "1 serving (~27 g protein)"),
    ("Breakfast", "Oats", "50 g"),
    ("Breakfast", "Medium banana", "1"),
    ("Breakfast", "Chia seeds", "10 g"),
    ("Lunch", "Whole egg", "1"),
    ("Lunch", "Egg whites", "2"),
    ("Lunch", "Cooked rice", "250 g"),
    ("Lunch", "Vegetables / salad", "150–250 g"),
    ("Lunch", "Curd", "150 g, unsweetened"),
    ("Evening", "Soya chunks", "50 g dry"),
    ("Evening", "Fruit / buttermilk", "1 serving if hungry"),
    ("Dinner", "Chicken breast", "250 g cooked"),
    ("Dinner", "Cooked rice", "150–200 g"),
    ("Dinner", "Milk", "200 ml"),
    ("Dinner", "Vegetables / salad", "150–250 g"),
    ("Daily", "Water", "~3–4 L; adjust for thirst, heat and training"),
]

DIET_GROUPS = {}
for _meal, _food, _portion in DIET:
    if _meal != "Daily":
        DIET_GROUPS.setdefault(_meal, []).append((_food, _portion))


def lookup_food_macros(name, portion_multiplier=1.0):
    key = name.strip().lower()
    base = FOOD_DB.get(key)
    if base is None:
        for k, v in FOOD_DB.items():
            if k in key or key in k:
                base = v
                break
    if base is None:
        return None
    return {
        "calories": round(base["cal"] * portion_multiplier, 1),
        "protein": round(base["protein"] * portion_multiplier, 1),
        "carbs": round(base["carbs"] * portion_multiplier, 1),
        "fat": round(base["fat"] * portion_multiplier, 1),
        "fiber": round(base["fiber"] * portion_multiplier, 1),
    }


def lookup_food_macros_by_grams(name, grams):
    key = name.strip().lower()
    matched_key = key if key in FOOD_DB else next(
        (k for k in FOOD_DB if k in key or key in k), None
    )
    if matched_key is None:
        return None
    serving_grams = FOOD_SERVING_GRAMS[matched_key]
    return lookup_food_macros(matched_key, grams / serving_grams)


def macros_by_calories(name, calories):
    """Scale a FOOD_DB entry's macros to match a user-entered calorie amount."""
    key = name.strip().lower()
    base = FOOD_DB.get(key)
    if base is None:
        for k, v in FOOD_DB.items():
            if k in key or key in k:
                base = v
                break
    if base is None or not base["cal"]:
        return None
    ratio = calories / base["cal"]
    return {
        "calories": round(calories, 1),
        "protein": round(base["protein"] * ratio, 1),
        "carbs": round(base["carbs"] * ratio, 1),
        "fat": round(base["fat"] * ratio, 1),
        "fiber": round(base["fiber"] * ratio, 1),
    }


def estimate_diet_totals():
    totals = {"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0}
    multipliers = {
        "super you whey protein": 1.0, "oats": 1.0, "medium banana": 1.0,
        "chia seeds": 1.0, "whole egg": 1.0, "egg whites": 1.0,
        "cooked rice": 2.5, "vegetables / salad": 1.0, "curd": 1.0,
        "soya chunks": 1.0, "fruit / buttermilk": 1.0, "chicken breast": 1.0, "milk": 1.0,
    }
    for meal, food, _ in DIET:
        if meal == "Daily":
            continue
        key = food.lower()
        mult = multipliers.get(key, 1.0)
        if meal == "Dinner" and key == "cooked rice":
            mult = 1.75
        m = lookup_food_macros(food, mult)
        if m:
            for k in totals:
                totals[k] += m[k]
    for k in totals:
        totals[k] = round(totals[k], 1)
    return totals


def estimate_diet_meal_totals():
    totals_by_meal = {}
    for meal, food, _ in DIET:
        if meal == "Daily":
            continue
        key = food.lower()
        multiplier = {
            "super you whey protein": 1.0, "oats": 1.0, "medium banana": 1.0,
            "chia seeds": 1.0, "whole egg": 1.0, "egg whites": 1.0,
            "cooked rice": 2.5 if meal == "Lunch" else 1.75,
            "vegetables / salad": 2.0, "curd": 1.0, "soya chunks": 1.0,
            "fruit / buttermilk": 1.0, "chicken breast": 1.0, "milk": 1.0,
        }.get(key, 1.0)
        macros = lookup_food_macros(food, multiplier)
        if macros:
            meal_totals = totals_by_meal.setdefault(
                meal, {"calories": 0, "protein": 0, "carbs": 0, "fat": 0, "fiber": 0}
            )
            for nutrient in meal_totals:
                meal_totals[nutrient] += macros[nutrient]
    for meal_totals in totals_by_meal.values():
        for nutrient in meal_totals:
            meal_totals[nutrient] = round(meal_totals[nutrient], 1)
    return totals_by_meal


def sum_food_totals(food_by_date):
    totals = {key: 0 for key in ("calories", "protein", "carbs", "fat", "fiber")}
    for daily_totals in food_by_date.values():
        for nutrient in totals:
            totals[nutrient] += daily_totals.get(nutrient, 0)
    return {nutrient: round(value, 1) for nutrient, value in totals.items()}


def db():
    return mysql.connector.connect(**DB_CONFIG)


def init_db():
    conn = None
    cur = None
    try:
        conn = db()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS daily_logs (
                log_date DATE PRIMARY KEY,
                weight_kg DECIMAL(5,2) NULL,
                calories DECIMAL(7,2) NULL,
                steps INT DEFAULT 0,
                steps_done TINYINT(1) DEFAULT 0,
                notes VARCHAR(1000) DEFAULT '',
                hot_water TINYINT(1) DEFAULT 0,
                ice_facewash TINYINT(1) DEFAULT 0,
                black_coffee TINYINT(1) DEFAULT 0,
                workout TINYINT(1) DEFAULT 0,
                diet TINYINT(1) DEFAULT 0,
                water TINYINT(1) DEFAULT 0,
                creatine TINYINT(1) DEFAULT 0,
                psyllium TINYINT(1) DEFAULT 0,
                shilajit TINYINT(1) DEFAULT 0,
                yoga TINYINT(1) DEFAULT 0,
                multivitamin TINYINT(1) DEFAULT 0,
                fish_oil TINYINT(1) DEFAULT 0,
                calcium_magnesium TINYINT(1) DEFAULT 0,
                brushing TINYINT(1) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        try:
            cur.execute("ALTER TABLE daily_logs ADD COLUMN steps_done TINYINT(1) DEFAULT 0")
            conn.commit()
        except Error:
            pass

        cur.execute("""
            CREATE TABLE IF NOT EXISTS food_log (
                id INT AUTO_INCREMENT PRIMARY KEY,
                log_date DATE NOT NULL,
                food_name VARCHAR(255) NOT NULL,
                grams DECIMAL(7,2) NOT NULL,
                calories DECIMAL(7,2) NOT NULL,
                protein DECIMAL(6,2) DEFAULT 0,
                carbs DECIMAL(6,2) DEFAULT 0,
                fat DECIMAL(6,2) DEFAULT 0,
                fiber DECIMAL(6,2) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX (log_date)
            )
        """)
        try:
            cur.execute("ALTER TABLE food_log ADD COLUMN grams DECIMAL(7,2) NOT NULL DEFAULT 0")
            conn.commit()
        except Error:
            pass
        conn.commit()
    except Error as e:
        print("Database initialization error:", e)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def get_log(d):
    conn = db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM daily_logs WHERE log_date=%s", (d,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


def save_log(data):
    fields = list(ACTIVITY_FIELDS)
    d = data["log_date"]
    vals = [int(bool(data.get(f, 0))) for f in fields]
    weight = data.get("weight_kg")
    calories = data.get("calories")
    steps = int(data.get("steps_count") or data.get("steps") or 0)
    if steps >= PROFILE["daily_step_target"] and "steps_done" in fields:
        vals[fields.index("steps_done")] = 1
    notes = data.get("notes", "")

    conn = db()
    cur = conn.cursor()
    placeholders = ",".join(["%s"] * (5 + len(fields)))
    columns = "log_date,weight_kg,calories,steps,notes," + ",".join(fields)
    updates = [
        "weight_kg=VALUES(weight_kg)",
        "calories=VALUES(calories)",
        "steps=VALUES(steps)",
        "notes=VALUES(notes)",
    ] + [f"{f}=VALUES({f})" for f in fields]
    sql = f"""
        INSERT INTO daily_logs ({columns})
        VALUES ({placeholders})
        ON DUPLICATE KEY UPDATE {", ".join(updates)}
    """
    cur.execute(sql, [d, weight, calories, steps, notes] + vals)
    conn.commit()
    cur.close()
    conn.close()


def get_logs_between(start_d, end_d):
    conn = db()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        "SELECT * FROM daily_logs WHERE log_date BETWEEN %s AND %s ORDER BY log_date",
        (start_d, end_d),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_food_totals_between(start_d, end_d):
    conn = db()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        "SELECT log_date, SUM(calories) AS calories, SUM(protein) AS protein, "
        "SUM(carbs) AS carbs, SUM(fat) AS fat, SUM(fiber) AS fiber "
        "FROM food_log WHERE log_date BETWEEN %s AND %s GROUP BY log_date ORDER BY log_date",
        (start_d, end_d),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {
        r["log_date"]: {key: round(float(r[key] or 0), 1)
                        for key in ("calories", "protein", "carbs", "fat", "fiber")}
        for r in rows
    }


def bmr(weight):
    return 10 * weight + 6.25 * PROFILE["height_cm"] - 5 * PROFILE["age"] + 5


def tdee(weight):
    return bmr(weight) * 1.55


def calorie_target(weight):
    return max(1800, round(tdee(weight) - 500))


def predicted_weekly_loss(weight):
    deficit = max(0, tdee(weight) - calorie_target(weight))
    return min(0.75, round((deficit * 7) / 7700, 2))


def weekly_target_weight(weight):
    return round(weight - predicted_weekly_loss(weight), 2)


def activity_score(log):
    if not log:
        return 0
    done = sum(int(log.get(k, 0) or 0) for k, _ in ACTIVITIES)
    return round(done / len(ACTIVITIES) * 100)


def get_week_summary(anchor):
    monday = anchor - timedelta(days=anchor.weekday())
    sunday = monday + timedelta(days=6)
    rows = get_logs_between(monday, sunday)
    by_date = {r["log_date"]: r for r in rows}
    daily = []
    for i in range(7):
        d = monday + timedelta(days=i)
        r = by_date.get(d)
        if r:
            score = activity_score(r)
            wt = float(r["weight_kg"]) if r["weight_kg"] is not None else None
        else:
            score = 0
            wt = None
        daily.append({"date": d.isoformat(), "score": score, "weight": wt})
    weights = [x["weight"] for x in daily if x["weight"] is not None]
    avg_weight = round(sum(weights) / len(weights), 2) if weights else None
    first = weights[0] if weights else None
    last = weights[-1] if weights else None
    change = round(last - first, 2) if first is not None and last is not None else None
    return {
        "monday": monday, "sunday": sunday, "daily": daily,
        "average_weight": avg_weight, "weight_change": change,
    }


def reference_target_for_date(d):
    weeks = max(0, (d - START_DATE).days // 7)
    target = PROFILE["starting_weight_kg"]
    for _ in range(weeks):
        target = max(PROFILE["target_weight_kg"], target - predicted_weekly_loss(target))
    return round(target, 2)


def weekly_reference_targets():
    items = []
    target = PROFILE["starting_weight_kg"]
    max_weeks = ((END_DATE - START_DATE).days // 7) + 1
    for _ in range(max_weeks):
        items.append(round(target, 2))
        target = max(PROFILE["target_weight_kg"], target - predicted_weekly_loss(target))
    return items


def all_time_progress():
    rows = get_logs_between(START_DATE, date.today())
    scores = [activity_score(r) for r in rows]
    avg = round(sum(scores) / len(scores), 1) if scores else 0
    weights = [
        (r["log_date"], float(r["weight_kg"]))
        for r in rows if r["weight_kg"] is not None
    ]
    latest = weights[-1][1] if weights else PROFILE["starting_weight_kg"]
    total_loss = round(PROFILE["starting_weight_kg"] - latest, 2)
    return avg, latest, total_loss


def current_streak(threshold=70):
    """Consecutive most-recent days with an activity score >= threshold."""
    rows = get_logs_between(START_DATE, date.today())
    rows.sort(key=lambda r: r["log_date"], reverse=True)
    streak = 0
    for r in rows:
        if activity_score(r) >= threshold:
            streak += 1
        else:
            break
    return streak


def fmt_label(d):
    if isinstance(d, str):
        d = datetime.strptime(d[:10], "%Y-%m-%d").date()
    return d.strftime("%d.%m.%Y")


@app.route("/")
def index():
    today = date.today()
    log = get_log(today)
    food_totals = get_food_totals_between(today, today).get(today, {})
    weekday = today.strftime("%A")
    current_weight = (
        float(log["weight_kg"])
        if log and log["weight_kg"] is not None
        else PROFILE["starting_weight_kg"]
    )
    avg_score, latest_weight, total_loss = all_time_progress()
    week = get_week_summary(today)
    target_cal = calorie_target(current_weight)
    consumed_calories = food_totals.get("calories", 0)
    weekly_loss = predicted_weekly_loss(current_weight)
    target_wt = weekly_target_weight(current_weight)
    rows = get_logs_between(START_DATE, today)
    labels = [r["log_date"].strftime("%d %b") for r in rows]
    weights = [float(r["weight_kg"]) if r["weight_kg"] is not None else None for r in rows]
    scores = [activity_score(r) for r in rows]
    targets = [reference_target_for_date(r["log_date"]) for r in rows]
    return render_template(
        "index.html",
        profile=PROFILE, today=today.isoformat(), weekday=weekday,
        log=log or {}, activities=ACTIVITIES, score=activity_score(log),
        current_weight=current_weight, latest_weight=latest_weight,
        total_loss=total_loss, avg_score=avg_score, week=week,
        target_calories=target_cal, weekly_loss=weekly_loss,
        target_weight=target_wt, workout=WORKOUTS[weekday],
        workout_image=workout_images[weekday], labels=labels,
        weights=weights, scores=scores, targets=targets,
        weekly_targets=weekly_reference_targets(),
        streak=current_streak(), challenge_start=START_DATE, challenge_end=END_DATE,
        challenge_days=(END_DATE - START_DATE).days + 1,
        consumed_calories=consumed_calories, food_totals=food_totals,
    )


@app.route("/save", methods=["POST"])
def save():
    payload = request.get_json(silent=True) or request.form.to_dict()
    log_date = payload.get("log_date") or date.today().isoformat()
    data = {"log_date": log_date}
    for f, _ in ACTIVITIES:
        data[f] = payload.get(f) in [True, "true", "1", 1, "on", "yes"]
    data["steps"] = payload.get("steps", 0)
    data["weight_kg"] = payload.get("weight_kg") or None
    data["calories"] = payload.get("calories") or None
    data["notes"] = payload.get("notes", "")
    save_log(data)
    d = datetime.strptime(log_date, "%Y-%m-%d").date()
    return jsonify({"ok": True, "score": activity_score(get_log(d))})


@app.route("/date/<log_date>")
def date_log(log_date):
    try:
        d = datetime.strptime(log_date, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Invalid date"}), 400
    row = get_log(d)
    return jsonify(row or {"log_date": log_date})


@app.route("/workout")
def workout_page():
    return render_template("workout.html", workouts=WORKOUTS, workout_images=workout_images)


@app.route("/diet")
def diet_page():
    current = float(
        (get_log(date.today()) or {}).get("weight_kg") or PROFILE["starting_weight_kg"]
    )
    added_food_totals = get_food_totals_between(date.today(), date.today()).get(
        date.today(), {key: 0 for key in ("calories", "protein", "carbs", "fat", "fiber")}
    )
    return render_template(
        "diet.html",
        diet=DIET, calories=calorie_target(current),
        weekly_loss=predicted_weekly_loss(current), current_weight=current,
        diet_images=diet_images, diet_groups=DIET_GROUPS,
        diet_totals=estimate_diet_totals(), diet_meal_totals=estimate_diet_meal_totals(),
        added_food_totals=added_food_totals, food_db=FOOD_DB,
    )


@app.route("/api/food-macros")
def food_macros_api():
    name = request.args.get("name", "").strip()
    try:
        qty = float(request.args.get("qty", 1))
    except ValueError:
        qty = 1.0
    if not name:
        return jsonify({"ok": False, "error": "name required"}), 400
    macros = lookup_food_macros(name, qty)
    if not macros:
        return jsonify({"ok": False, "error": "food not found", "name": name})
    return jsonify({"ok": True, "name": name, "qty": qty, "macros": macros})


@app.route("/api/food-log", methods=["GET", "POST"])
def food_log_api():
    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        name = (payload.get("food_name") or "").strip()
        try:
            grams = float(payload.get("grams"))
        except (TypeError, ValueError):
            return jsonify({"ok": False, "error": "valid grams required"}), 400
        if not name:
            return jsonify({"ok": False, "error": "food_name required"}), 400
        if grams <= 0:
            return jsonify({"ok": False, "error": "grams must be greater than zero"}), 400
        log_date = payload.get("log_date") or date.today().isoformat()
        macros = lookup_food_macros_by_grams(name, grams)
        if not macros:
            return jsonify({"ok": False, "error": "food not found", "name": name}), 400
        conn = db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO food_log (log_date, food_name, grams, calories, protein, carbs, fat, fiber) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (log_date, name, grams, macros["calories"], macros["protein"],
             macros["carbs"], macros["fat"], macros["fiber"]),
        )
        conn.commit()
        new_id = cur.lastrowid
        cur.close()
        conn.close()
        return jsonify({"ok": True, "id": new_id, "food_name": name, "grams": grams,
                         "log_date": log_date, "macros": macros})

    log_date = request.args.get("date", date.today().isoformat())
    conn = db()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        "SELECT id, food_name, grams, calories, protein, carbs, fat, fiber "
        "FROM food_log WHERE log_date=%s ORDER BY id", (log_date,)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    totals = {k: round(sum(float(r[k] or 0) for r in rows), 1)
              for k in ("calories", "protein", "carbs", "fat", "fiber")}
    return jsonify({"ok": True, "log_date": log_date, "items": rows, "totals": totals})


@app.route("/api/food-log/<int:item_id>", methods=["DELETE"])
def food_log_delete(item_id):
    conn = db()
    cur = conn.cursor()
    cur.execute("DELETE FROM food_log WHERE id=%s", (item_id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"ok": True})


@app.route("/progress")
def progress_page():
    end_date = min(date.today(), END_DATE)
    rows = get_logs_between(START_DATE, end_date)
    logs_by_date = {r["log_date"]: r for r in rows}
    food_by_date = get_food_totals_between(START_DATE, end_date)
    added_food_totals = sum_food_totals(food_by_date)
    chart_dates = [START_DATE + timedelta(days=i) for i in range((end_date - START_DATE).days + 1)]
    iso_dates = [d.isoformat() for d in chart_dates]
    labels = [fmt_label(d) for d in chart_dates]
    weights = [float(logs_by_date[d]["weight_kg"]) if d in logs_by_date and logs_by_date[d]["weight_kg"] is not None else None for d in chart_dates]
    scores = [activity_score(logs_by_date.get(d)) for d in chart_dates]
    calories = [food_by_date.get(d, {}).get("calories") or (float(logs_by_date[d]["calories"]) if d in logs_by_date and logs_by_date[d]["calories"] is not None else None) for d in chart_dates]
    protein = [food_by_date.get(d, {}).get("protein") for d in chart_dates]
    carbs = [food_by_date.get(d, {}).get("carbs") for d in chart_dates]
    fat = [food_by_date.get(d, {}).get("fat") for d in chart_dates]
    fiber = [food_by_date.get(d, {}).get("fiber") for d in chart_dates]
    targets = [reference_target_for_date(d) for d in chart_dates]
    valid_scores = [s for s in scores if s is not None]
    valid_cals = [c for c in calories if c is not None]
    valid_weights = [w for w in weights if w is not None]
    avg_score = round(sum(valid_scores) / len(valid_scores), 1) if valid_scores else 0
    avg_calories = round(sum(valid_cals) / len(valid_cals), 0) if valid_cals else 0
    avg_weight = round(sum(valid_weights) / len(valid_weights), 1) if valid_weights else None
    return render_template(
        "progress.html",
        labels=labels, iso_dates=iso_dates, weights=weights, scores=scores,
        calories=calories, protein=protein, carbs=carbs, fat=fat, fiber=fiber,
        targets=targets, weekly_targets=weekly_reference_targets(), profile=PROFILE,
        avg_score=avg_score, avg_calories=avg_calories, avg_weight=avg_weight,
        challenge_start=START_DATE, challenge_end=END_DATE,
        challenge_days=(END_DATE - START_DATE).days + 1,
        diet_meal_totals=estimate_diet_meal_totals(), added_food_totals=added_food_totals,
    )


@app.route("/export/csv")
def export_csv():
    start = request.args.get("start", (date.today() - timedelta(days=6)).isoformat())
    end = request.args.get("end", date.today().isoformat())
    rows = get_logs_between(start, end)
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(
        ["Date", "Weight (kg)", "Calories", "Steps", "Activity Score %"]
        + [label for _, label in ACTIVITIES]
    )
    for r in rows:
        activity_vals = [r.get(k, 0) for k, _ in ACTIVITIES]  # FIX KeyError
        writer.writerow(
            [r.get("log_date"), r.get("weight_kg"), r.get("calories"),
             r.get("steps", 0), activity_score(r)]
            + activity_vals
        )
    mem = io.BytesIO(out.getvalue().encode("utf-8"))
    mem.seek(0)
    return send_file(
        mem, mimetype="text/csv", as_attachment=True,
        download_name=f"transformation_{start}_to_{end}.csv",
    )


@app.route("/export/pdf")
def export_pdf():
    start = request.args.get("start", START_DATE.isoformat())
    end = request.args.get("end", END_DATE.isoformat())
    rows = get_logs_between(start, end)
    food_totals = get_food_totals_between(start, end)
    logs_by_date = {r["log_date"]: r for r in rows}
    export_dates = sorted(set(logs_by_date) | set(food_totals))
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=1.2 * cm, leftMargin=1.2 * cm,
        topMargin=1.2 * cm, bottomMargin=1.2 * cm,
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CenterTitle", parent=styles["Title"], alignment=TA_CENTER, fontSize=20))
    story = [
        Paragraph("Peak Transformation — Challenge Report", styles["CenterTitle"]),
        Paragraph(f"{PROFILE['name']} • {start} to {end}", styles["Normal"]),
        Spacer(1, 10),
    ]
    data = [["Date", "Weight", "Calories", "Steps", "Score"]]
    for log_date in export_dates:
        r = logs_by_date.get(log_date, {})
        food_calories = food_totals.get(log_date, {}).get("calories")
        data.append([
            str(log_date),
            f"{float(r['weight_kg']):.1f}" if r.get("weight_kg") is not None else "-",
            f"{food_calories if food_calories is not None else float(r['calories']):.0f}"
            if food_calories is not None or r.get("calories") is not None else "-",
            str(r.get("steps", 0)),
            f"{activity_score(r)}%",
        ])
    table = Table(data, repeatRows=1, colWidths=[3.0*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.0*cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#111827")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
    ]))
    story.append(table)
    story.append(Spacer(1, 12))
    current = (
        float(rows[-1]["weight_kg"])
        if rows and rows[-1].get("weight_kg") is not None
        else PROFILE["starting_weight_kg"]
    )
    story += [
        Paragraph(f"Current weight: {current:.1f} kg", styles["Heading2"]),
        Paragraph(f"Estimated calorie target: {calorie_target(current)} kcal/day", styles["Normal"]),
        Paragraph(f"Estimated weekly loss at that target: {predicted_weekly_loss(current):.2f} kg/week", styles["Normal"]),
        Paragraph(f"Next-week reference weight: {weekly_target_weight(current):.2f} kg", styles["Normal"]),
        Spacer(1, 8),
        Paragraph(
            "Important: body weight fluctuates from water, sodium, glycogen and digestion. "
            "Use the 7-day average rather than reacting to one day's scale reading.",
            styles["Normal"],
        ),
    ]
    doc.build(story)
    buffer.seek(0)
    return send_file(
        buffer, mimetype="application/pdf", as_attachment=True,
        download_name=f"transformation_{start}_to_{end}.pdf",
    )


try:
    init_db()
except Exception as e:
    print("Startup DB error:", e)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5070)