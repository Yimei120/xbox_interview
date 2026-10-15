"""Consistency checks for the interview dataset."""

import csv
import unittest
from collections import Counter, defaultdict
from datetime import datetime, timedelta

from generate_dataset import COHORT_START, FIELDS, FOLLOW_UP_DAYS, OUTPUT, PLAYERS_PER_DAY, FEATURES, generate


class DatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with OUTPUT.open(newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            cls.fields = reader.fieldnames
            cls.rows = list(reader)
        cls.players = defaultdict(list)
        for row in cls.rows:
            cls.players[row["userid"]].append(row)

    def test_file_matches_seeded_generator(self):
        self.assertEqual(self.fields, FIELDS)
        self.assertEqual(self.rows, [
            {key: str(value) for key, value in row.items()} for row in generate()
        ])

    def test_cohorts_and_activity_days(self):
        self.assertEqual(len(self.players), 5 * PLAYERS_PER_DAY)
        self.assertGreater(len(self.rows), 5000)
        cohorts = Counter(rows[0]["startdate"] for rows in self.players.values())
        self.assertEqual(cohorts, Counter({
            f"{day.month}/{day.day}/{day.year}": PLAYERS_PER_DAY
            for day in (COHORT_START + timedelta(days=offset) for offset in range(5))
        }))
        for rows in self.players.values():
            start = datetime.strptime(rows[0]["startdate"], "%m/%d/%Y").date()
            self.assertEqual(rows[0]["DaysSinceStart"], "0")
            days = [int(row["DaysSinceStart"]) for row in rows]
            self.assertEqual(days, sorted(set(days)))
            for row, day in zip(rows, days):
                current = datetime.strptime(row["date"], "%m/%d/%Y").date()
                self.assertEqual(current, start + timedelta(days=day))
                self.assertLess(day, FOLLOW_UP_DAYS)
                self.assertEqual(row["DayOfWeek"], current.strftime("%A"))
                self.assertEqual(row["Weekend"], str(current.weekday() >= 5))

    def test_plans_status_and_limits(self):
        upgraded = cancelled = 0
        for rows in self.players.values():
            plans = [row["plan"] for row in rows]
            self.assertEqual(plans, sorted(plans))
            upgraded += plans[0] == "Free" and "Paid" in plans
            cancelled += rows[-1]["Status"] == "Cancelled"
            for index, row in enumerate(rows):
                self.assertIn(row["plan"], ("Free", "Paid"))
                self.assertIn(row["Status"], ("Active", "Cancelled"))
                if row["Status"] == "Cancelled":
                    self.assertEqual(row["plan"], "Paid")
                    self.assertEqual(index, len(rows) - 1)
                for feature, free_cap, paid_cap, _ in FEATURES:
                    success = int(row[f"{feature}_Success"])
                    error = int(row[f"{feature}_Error"])
                    self.assertGreaterEqual(success, 0)
                    self.assertGreaterEqual(error, 0)
                    self.assertLessEqual(success + error, paid_cap if row["plan"] == "Paid" else free_cap)
        self.assertGreater(upgraded, 0)
        self.assertGreater(cancelled, 0)
        self.assertTrue(any(row["DaysSinceStart"] == "59" for row in self.rows))


if __name__ == "__main__":
    unittest.main()
