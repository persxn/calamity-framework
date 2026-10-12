import json
import os
import unittest
from datetime import datetime, timedelta, timezone

from tests.helpers import ENGINE

from cal import fsrs


class Reference(unittest.TestCase):
    """The port must reproduce py-fsrs 6.3.2 number for number."""

    def test_against_py_fsrs(self):
        with open(os.path.join(ENGINE, "tests", "fixtures", "fsrs_reference.json"), "r", encoding="utf-8") as fh:
            ref = json.load(fh)
        self.assertGreaterEqual(len(ref["cases"]), 50)
        steps = 0
        for case in ref["cases"]:
            sched = fsrs.Scheduler(retention=case["retention"])
            card = None
            for step in case["steps"]:
                when = datetime.fromisoformat(step["t"])
                card, days = sched.review(card, step["g"], when)
                self.assertAlmostEqual(card.s / step["s"], 1.0, places=9)
                self.assertAlmostEqual(card.d, step["d"], places=9)
                self.assertEqual(days, step["days"])
                steps += 1
        self.assertGreater(steps, 300)


class Behaviour(unittest.TestCase):
    def setUp(self):
        self.sched = fsrs.Scheduler()
        self.t0 = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)

    def test_first_review_by_grade(self):
        days = [self.sched.review(None, g, self.t0)[1] for g in (fsrs.AGAIN, fsrs.HARD, fsrs.GOOD, fsrs.EASY)]
        self.assertEqual(days, sorted(days))
        self.assertGreaterEqual(days[0], 1)
        card, _ = self.sched.review(None, fsrs.GOOD, self.t0)
        self.assertAlmostEqual(card.s, fsrs.DEFAULT_PARAMETERS[2])
        self.assertEqual(card.reps, 1)
        self.assertEqual(card.lapses, 0)

    def test_due_is_last_plus_interval(self):
        card, days = self.sched.review(None, fsrs.GOOD, self.t0)
        self.assertEqual(card.due, self.t0 + timedelta(days=days))
        self.assertEqual(card.last, self.t0)

    def test_success_grows_and_failure_shrinks(self):
        card, _ = self.sched.review(None, fsrs.GOOD, self.t0)
        later = card.due
        good, _ = self.sched.review(card, fsrs.GOOD, later)
        again, _ = self.sched.review(card, fsrs.AGAIN, later)
        self.assertGreater(good.s, card.s)
        self.assertLess(again.s, card.s)
        self.assertEqual(again.lapses, 1)
        self.assertGreater(again.d, good.d)

    def test_input_card_is_not_modified(self):
        card, _ = self.sched.review(None, fsrs.GOOD, self.t0)
        before = (card.s, card.d, card.due, card.reps)
        self.sched.review(card, fsrs.AGAIN, card.due)
        self.assertEqual(before, (card.s, card.d, card.due, card.reps))

    def test_retrievability(self):
        self.assertAlmostEqual(self.sched.retrievability(10.0, 0), 1.0)
        self.assertAlmostEqual(self.sched.retrievability(10.0, 10.0), 0.9, places=6)
        values = [self.sched.retrievability(10.0, d) for d in (1, 5, 10, 50, 200)]
        self.assertEqual(values, sorted(values, reverse=True))

    def test_higher_retention_means_shorter_intervals(self):
        tight = fsrs.Scheduler(retention=0.95)
        loose = fsrs.Scheduler(retention=0.80)
        self.assertLess(tight.interval(30.0), self.sched.interval(30.0))
        self.assertGreater(loose.interval(30.0), self.sched.interval(30.0))

    def test_max_interval(self):
        sched = fsrs.Scheduler(max_interval=30)
        card = None
        when = self.t0
        for _ in range(12):
            card, days = sched.review(card, fsrs.EASY, when)
            self.assertLessEqual(days, 30)
            when = card.due

    def test_fuzz_is_deterministic_and_bounded(self):
        card = None
        when = self.t0
        for _ in range(5):
            card, _ = self.sched.review(card, fsrs.GOOD, when)
            when = card.due
        plain = self.sched.review(card, fsrs.GOOD, when)[1]
        a = self.sched.review(card, fsrs.GOOD, when, fuzz=0.25)[1]
        b = self.sched.review(card, fsrs.GOOD, when, fuzz=0.25)[1]
        self.assertEqual(a, b)
        lows = self.sched.review(card, fsrs.GOOD, when, fuzz=0.0)[1]
        highs = self.sched.review(card, fsrs.GOOD, when, fuzz=0.999)[1]
        self.assertLessEqual(lows, plain)
        self.assertGreaterEqual(highs, plain)
        self.assertLess(highs - lows, max(4, 0.4 * plain))
        self.assertEqual(self.sched.fuzzed(2, 0.9), 2)  # short intervals are never fuzzed

    def test_bad_grade(self):
        with self.assertRaises(ValueError):
            self.sched.review(None, 5, self.t0)


if __name__ == "__main__":
    unittest.main()
