"""The adaptive daily quota (WP-09, design §6.1): fewer new topics when reviews pile up or first tries go wrong."""
from datetime import timedelta

from tests.helpers import Case


class Quota(Case):
    def setUp(self):
        super().setUp()
        self.sb.onboard()
        self.sb.run("enroll", "shell")

    def quota(self, first_tries=None):
        state = self.sb.state()
        if first_tries is not None:            # a synthetic history of first tries on new topics
            now = state.last_dt or self.sb.clock
            state.first_tries = [(now - timedelta(hours=i), ok) for i, ok in enumerate(first_tries)]
        return state.new_quota(self.sb.clock)

    def test_a_fresh_learner_gets_the_pace_profiles_most(self):
        q = self.quota()
        self.assertEqual((q["quota"], q["max"], q["acc"]), (6, 6, None))          # mastery pace
        self.sb.run("enroll", "gate.ga")
        self.assertEqual(self.quota()["max"], 8)                                    # the exam pace is higher
        self.sb.run("profile", "set", "cfg.new_per_day_max", "4")
        self.assertEqual(self.quota()["quota"], 4)

    def test_the_old_name_is_still_honoured_and_zero_means_none(self):
        self.sb.run("profile", "set", "cfg.new_per_day", "3")
        self.assertEqual(self.quota()["quota"], 3)
        self.sb.run("profile", "set", "cfg.new_per_day", "0")
        self.assertEqual(self.quota()["quota"], 0)
        self.sb.run("profile", "set", "cfg.new_per_day_max", "5")                  # the new name wins
        self.assertEqual(self.quota()["quota"], 5)

    def test_low_first_try_accuracy_lowers_it(self):
        q = self.quota([True] * 6 + [False] * 4)
        self.assertEqual(round(q["acc"], 2), 0.6)
        self.assertEqual(q["quota"], 5)                     # 6 x 0.75, rounded
        self.assertEqual(self.quota([True] * 9)["acc"], None)                       # below 10 tries it is not counted

    def test_strong_accuracy_and_a_light_load_give_the_most(self):
        q = self.quota([True] * 12)
        self.assertEqual((q["quota"], q["max"]), (6, 6))    # x1.1, never above the most

    def test_a_heavy_review_forecast_lowers_it(self):
        sb = self.sb
        for topic in ("shell/pipes", "shell/perms"):
            sb.item(topic)
        sb.legacy_pace()
        sb.do("shell/pipes")
        sb.do("shell/perms")
        light = self.quota()
        self.assertEqual(light["quota"], 6)
        sb.run("profile", "set", "cfg.review_budget_min", "1")        # two cards due this week, one minute a day
        heavy = self.quota()
        self.assertLess(heavy["quota"], 6)
        self.assertGreaterEqual(heavy["quota"], 1)                     # never below one while new topics are allowed
        sb.run("profile", "set", "cfg.quota.adaptive", "false")
        self.assertEqual(self.quota()["quota"], 6)

    def test_first_tries_and_review_times_come_from_the_log(self):
        sb = self.sb
        sb.legacy_pace()
        for topic in ("shell/pipes", "shell/perms"):
            sb.item(topic)
        sb.do("shell/pipes", answer="A")                    # a first try that went wrong
        sb.do("shell/perms")
        state = sb.state()
        self.assertEqual([ok for _, ok in state.first_tries], [False, True])
        self.assertEqual(state.review_secs, [])             # neither was a review
        for _ in range(5):
            ts = sb.state().topics["shell/perms"]
            sb.at(ts.card.due.isoformat()).advance(minutes=5)
            sb.do("shell/perms", seconds=30)
        self.assertEqual(sb.state().review_secs, [30.0] * 5)
        sb.run("profile", "set", "cfg.review_budget_min", "1")
        self.assertLess(self.quota()["forecast"], 1.0)      # a 30 s median, not the 60 s default

    def test_the_reason_is_printed_in_today_and_the_brief(self):
        sb = self.sb
        today = sb.run("today")
        self.assertIn("new quota 6 (max 6): reviews forecast 0 min a day of 60; first-try accuracy not counted "
                      "yet (0 of 10 first tries in 14 days)", today)
        self.assertIn("  new quota 6 (max 6): ", sb.run("brief"))
        sb.run("profile", "set", "cfg.quota.adaptive", "off")
        self.assertIn("new quota 6 (max 6): fixed (quota.adaptive is off)", sb.run("today"))
