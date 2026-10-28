"""The engine's task queue (WP-18): what falls due around the studying, cooldowns, and the brief's line."""
import os

from tests.helpers import Case, write


class Tasks(Case):
    def setUp(self):
        super().setUp()
        sb = self.sb
        sb.onboard()
        sb.legacy_pace()
        sb.run("enroll", "shell")

    def test_a_week_of_work_brings_the_weekly_review_and_done_hides_it(self):
        sb = self.sb
        self.assertNotIn("weekly-review", sb.run("tasks"))           # nothing recorded yet
        sb.run("workout", "20")
        sb.advance(days=7)
        out = sb.run("tasks")
        self.assertIn("weekly-review", out)
        self.assertIn("/coach", out)
        self.assertIn("Tasks: weekly review due", sb.run("brief"))
        self.assertIn("hidden until", sb.run("tasks", "done", "weekly-review"))
        self.assertNotIn("weekly-review", sb.run("tasks"))
        sb.advance(days=7)
        self.assertIn("weekly-review", sb.run("tasks"))              # due again a week later

    def test_snooze_puts_a_task_off_for_a_day(self):
        sb = self.sb
        sb.run("workout", "20")
        sb.advance(days=8)
        sb.run("tasks", "snooze", "weekly-review")
        self.assertNotIn("weekly-review", sb.run("tasks"))
        sb.advance(days=1)
        self.assertIn("weekly-review", sb.run("tasks"))
        sb.run("tasks", "done", "nope", expect=2)

    def test_stocking_and_plan_reviews(self):
        sb = self.sb
        out = sb.run("tasks")
        self.assertRegex(out, r"stock\s+item bank not stocked")      # shell's topics have no items
        sb.item("shell/pipes")
        sb.item("shell/perms")
        self.assertNotIn("stock ", sb.run("tasks"))
        write(sb.path("learner", "cp", "plan.md"), "---\nreview_on: 2026-03-01\n---\n# plan\n")
        self.assertIn("cp-plan", sb.run("tasks"))
        write(sb.path("learner", "gate", "plan.md"), "---\nreview_on: 2026-04-01\n---\n# plan\n")
        self.assertNotIn("gate-plan", sb.run("tasks"))
        sb.run("gate", "mock", "CS", "40", "--source", "test series A")
        os.utime(sb.path("learner", "gate", "plan.md"), (0, 0))
        self.assertIn("gate-plan", sb.run("tasks"))

    def test_the_queue_is_the_same_from_a_full_replay(self):
        sb = self.sb
        sb.run("workout", "20")
        sb.advance(days=8)
        sb.run("tasks", "done", "weekly-review")
        fast = sb.run("tasks")
        sb.env["CALAMITY_NO_CACHE"] = "1"
        self.assertEqual(sb.run("tasks"), fast)
