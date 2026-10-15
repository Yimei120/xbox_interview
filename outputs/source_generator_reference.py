"""Regenerate the synthetic interview dataset using only the Python standard library."""

import csv
import random
from datetime import date, datetime, timedelta
from pathlib import Path


SEED = 20250303
COHORT_START = date(2025, 3, 3)
COHORT_DAYS = 5
FOLLOW_UP_DAYS = 60
PLAYERS_PER_DAY = 60
OUTPUT = Path(__file__).with_name("contoso_gaming_pc_app_output.csv")

FIELDS = [
    "date",
    "userid",
    "startdate",
    "plan",
    "Status",
    "DayOfWeek",
    "Weekend",
    "DaysSinceStart",
    "AI_AutoComplete_Success",
    "AI_Chat_Success",
    "AI_Agent_Success",
    "AI_AutoComplete_Error",
    "AI_Chat_Error",
    "AI_Agent_Error",
]
FEATURES = (
    ("AI_AutoComplete", 100, 200, 15),
    ("AI_Chat", 10, 50, 6),
    ("AI_Agent", 5, 20, 3),
)


def generate():
    rng = random.Random(SEED)
    rows = []
    ids = rng.sample(range(10000000, 99999999), COHORT_DAYS * PLAYERS_PER_DAY)
    for cohort_day in range(COHORT_DAYS):
        start = COHORT_START + timedelta(days=cohort_day)
        for userid in ids[cohort_day * PLAYERS_PER_DAY:(cohort_day + 1) * PLAYERS_PER_DAY]:
            engagement = rng.choices(("casual", "regular", "enthusiast"), (35, 45, 20))[0]
            affinity = rng.randrange(len(FEATURES))
            paid = rng.random() < 0.20
            cancelled = False
            stopped = False

            for day in range(FOLLOW_UP_DAYS):
                if stopped or cancelled:
                    break
                current = start + timedelta(days=day)
                weekend = current.weekday() >= 5
                if day:
                    stop_rate = {"casual": 0.027, "regular": 0.012, "enthusiast": 0.006}[engagement]
                    if rng.random() < stop_rate:
                        stopped = True
                        break
                    attendance = {"casual": 0.39, "regular": 0.67, "enthusiast": 0.86}[engagement]
                    if rng.random() >= min(0.96, attendance * (1.17 if weekend else 1)):
                        continue

                # Plan and billing status are recorded at the end of the activity day.
                if not paid and 4 <= day <= 45:
                    upgrade_rate = {"casual": 0.003, "regular": 0.009, "enthusiast": 0.016}[engagement]
                    if rng.random() < upgrade_rate:
                        paid = True
                if paid and day >= 7 and rng.random() < 0.006:
                    cancelled = True

                row = {
                    "date": f"{current.month}/{current.day}/{current.year}",
                    "userid": userid,
                    "startdate": f"{start.month}/{start.day}/{start.year}",
                    "plan": "Paid" if paid else "Free",
                    "Status": "Cancelled" if cancelled else "Active",
                    "DayOfWeek": current.strftime("%A"),
                    "Weekend": weekend,
                    "DaysSinceStart": day,
                }
                for index, (feature, free_cap, paid_cap, typical) in enumerate(FEATURES):
                    cap = paid_cap if paid else free_cap
                    scale = 1.7 if index == affinity else 0.65
                    if engagement == "enthusiast":
                        scale *= 1.5
                    elif engagement == "casual":
                        scale *= 0.6
                    interactions = min(cap, int(rng.uniform(0.3, 1.3) * typical * scale))
                    # Some frequent Free users reach the Coach/Agent daily limits.
                    if not paid and index == affinity and rng.random() < 0.12:
                        interactions = cap if index else min(cap, interactions * 3)
                    errors = sum(rng.random() < (0.08 if index == 2 else 0.05)
                                 for _ in range(interactions))
                    row[f"{feature}_Success"] = interactions - errors
                    row[f"{feature}_Error"] = errors
                rows.append(row)
    rows.sort(key=lambda row: (datetime.strptime(row["date"], "%m/%d/%Y"), row["userid"]))
    return rows


if __name__ == "__main__":
    with OUTPUT.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(generate())
