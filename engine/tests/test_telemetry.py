"""Teaching telemetry (WP-10): what was taught, for how long, and the learner's word on the pace."""
import json

from tests.helpers import Case, write

SYLLABUS = """---
skill: shell
written: 2026-03-01
sources: [https://www.gnu.org/software/bash/manual/]
---

# Topics

## pipes | Pipes
level: 1
- explain what a pipe hands from one process to the next

## perms | Permissions
needs: [pipes]
level: 3
- read and change file modes
- explain why a directory needs x to be entered
- choose a umask for a shared folder
"""


class Telemetry(Case):
    def setUp(self):
        super().setUp()
        self.sb.onboard()
        write(self.sb.path("learner", "syllabus", "shell.md"), SYLLABUS)
        self.sb.run("enroll", "shell")
        self.sb.legacy_pace()
        for topic in ("shell/pipes", "shell/perms"):
            self.sb.item(topic)

    def test_parts_and_minutes_ride_on_the_covered_event_and_show_in_day(self):
        sb = self.sb
        out = sb.run("ask", "--topic", "shell/pipes", "--taught", "--parts", "model,example,usage", "--minutes", "18")
        self.assertIn("ITEM ", out)
        self.assertNotIn("warning:", out)                       # level 1 asks for a model and an example
        ds = sb.state().days[sb.state().day(sb.clock)]
        self.assertEqual(ds.taught, [["shell/pipes", ["model", "example", "usage"], 18]])
        self.assertIn("taught: shell/pipes · 18 min · model, example, usage", sb.run("day"))
        self.assertEqual(json.loads(sb.run("day", "--json"))["teaching"][0],
                         "taught: shell/pipes · 18 min · model, example, usage")

    def test_a_thin_teaching_of_a_level_3_topic_is_warned_about_not_blocked(self):
        sb = self.sb
        sb.do("shell/pipes")
        out = sb.run("ask", "--topic", "shell/perms", "--taught", "--parts", "model,example")
        self.assertIn("warning: a level-3 topic asks for history, mechanics, usage, tradeoffs too", out)
        self.assertIn("ITEM ", out)                              # the question is still served
        full = sb.run("ask", "--topic", "shell/perms", "--taught",
                      "--parts", "history,model,mechanics,example,usage,tradeoffs")
        self.assertNotIn("warning:", full)

    def test_parts_are_checked(self):
        sb = self.sb
        sb.run("ask", "--topic", "shell/pipes", "--taught", "--parts", "model,vibes", expect=2)
        self.assertIn("--parts names the parts taught", sb.err)
        sb.run("ask", "--topic", "shell/pipes", "--minutes", "5", expect=2)
        self.assertIn("use them with --topic K --taught", sb.err)
        ts = sb.state().topics.get("shell/pipes")
        self.assertTrue(ts is None or ts.covered_ts is None)                  # nothing was recorded

    def test_feedback_is_recorded_and_shown(self):
        sb = self.sb
        out = sb.run("feedback", "pace=slow", "depth=more", "--topic", "shell/pipes")
        self.assertEqual(out.strip(), "feedback noted: pace=slow depth=more on shell/pipes")
        self.assertIn("feedback: pace=slow depth=more on shell/pipes", sb.run("day"))
        self.assertIn("pace=slow depth=more", sb.run("observations", "--tag", "feedback"))
        for wrong in ("pace=glacial", "mood=ok"):
            sb.run("feedback", wrong, expect=2)
            self.assertIn("feedback takes", sb.err)
