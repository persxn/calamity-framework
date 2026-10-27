"""The day's shape: one format in learner/schedule.md, notes and goals in learner/timetable.json."""
import json
import os
import re
import subprocess
import sys

from tests.helpers import ENGINE, REPO, Case, read, write

TUESDAY = "2026-03-03T10:00:00+05:30"
FRONT = """---
updated: 2026-03-01
weekday:
  - "09:15-09:45 | Recall | due reviews"
  - "09:45-12:15 | GATE block A | new theory and lectures"
  - "22:30-01:00 | Late practice | past papers"
weekend:
  - "10:00-12:00 | Mock"
sat:
  - "08:00-09:00 | Long run"
---

# Day shape

Free text for the learner.
"""
TABLES = """---
updated: 2026-03-01
basis: stated at onboarding; the weekday runs fuller
  than the target by design
---

# Day shape

## Weekday (Mon-Fri)

| Time | Block | Purpose |
|---|---|---|
| 09:15–09:45 | **Recall** (30 m) | Due reviews. |
| 09:45–12:15 | **GATE block A** | — |

## Weekend

| Time | Block | Purpose |
|---|---|---|
| 10:00–12:00 | Mock | full paper |

# Changes

- 2026-03-01: first version.
"""


class Day(Case):
    def setUp(self):
        super().setUp()
        self.sb.at(TUESDAY)
        self.sb.onboard()

    def schedule(self, text):
        write(self.sb.path("learner", "schedule.md"), text)

    def test_front_matter_blocks_with_the_current_one(self):
        self.schedule(FRONT)
        out = self.sb.run("day")
        self.assertIn("Tue 2026-03-03 · schedule.md (weekday)", out)
        self.assertIn("▸ 09:45-12:15  GATE block A  — new theory and lectures", out)
        self.assertIn("· 09:15-09:45  Recall", out)                     # over already
        self.assertIn("today:", out)                                         # the finish line comes along
        self.assertIn("Now: GATE block A (09:45-12:15) · next: Late practice 22:30", self.sb.run("brief"))
        self.assertIn("schedule.md (sat)", self.sb.run("day", "sat"))       # a day of the week of its own
        self.assertIn("10:00-12:00  Mock", self.sb.run("day", "sun"))
        data = json.loads(self.sb.run("day", "--json"))
        self.assertEqual([b["name"] for b in data["blocks"]], ["Recall", "GATE block A", "Late practice"])
        self.assertEqual(data["now"], 1)

    def test_a_block_after_midnight_belongs_to_the_evening(self):
        self.schedule(FRONT)
        self.sb.at("2026-03-04T00:40:00+05:30")                              # Wednesday 00:40: still Tuesday's day
        self.assertIn("Now: Late practice (22:30-01:00)", self.sb.run("brief"))
        self.sb.at("2026-03-04T02:00:00+05:30")
        self.assertIn("Now: between blocks · the day's blocks are over", self.sb.run("brief"))

    def test_tables_are_read_and_migrated(self):
        self.schedule(TABLES)
        out = self.sb.run("day")
        self.assertIn("schedule.md (weekday table)", out)
        self.assertIn("09:45-12:15  GATE block A", out)
        self.assertIn("day migrate", out)                                     # the front matter does not read
        preview = self.sb.run("day", "migrate")
        self.assertIn("would rewrite", preview)
        self.assertEqual(read(self.sb.path("learner", "schedule.md")), TABLES)  # nothing written yet
        self.assertIn("rewrote learner/schedule.md", self.sb.run("day", "migrate", "--write"))
        text = read(self.sb.path("learner", "schedule.md"))
        self.assertIn('basis: "stated at onboarding; the weekday runs fuller than the target by design"', text)
        self.assertIn('  - "09:15-09:45 | Recall (30 m) | Due reviews."', text)
        self.assertIn('  - "09:45-12:15 | GATE block A"', text)
        self.assertTrue(text.endswith(TABLES.split("---\n", 2)[2]))           # the body is kept as it was
        self.assertIn("schedule.md (weekday)", self.sb.run("day"))
        self.assertIn("in the one format already", self.sb.run("day", "migrate"))

    def test_the_rule_book_example_renders(self):
        with open(os.path.join(REPO, "framework", "rules", "scheduler.md"), "r", encoding="utf-8") as fh:
            example = re.search(r"```markdown\n(---\n.*?)```", fh.read(), re.S).group(1)
        self.schedule(example)
        out = self.sb.run("day")
        self.assertIn("▸ 09:30-12:30  Deep block A", out)
        self.assertNotIn("note:", out)

    def test_notes_goals_and_a_shifted_day(self):
        self.schedule(FRONT)
        self.assertIn("note for 2026-03-04 saved", self.sb.run("day", "note", "tomorrow", "college exam 10-13"))
        self.assertIn("Day note: college exam 10-13", self.sb.at("2026-03-04T09:00:00+05:30").run("brief"))
        self.sb.at(TUESDAY)
        self.sb.run("day", "goal", "finish lecture 3", "--at", "9:45")
        self.sb.run("day", "goal", "two past papers", "--date", "fri")
        self.assertIn("goal 1 done", self.sb.run("day", "done", "1"))
        out = self.sb.run("day")
        self.assertIn("goal 1: [x] finish lecture 3 @09:45", out)
        self.assertIn("goal 1: [ ] two past papers", self.sb.run("day", "fri"))
        store = json.loads(read(self.sb.path("learner", "timetable.json")))
        store["overrides"]["2026-03-05"] = {"blocks": [{"time": "11:00-13:00", "name": "Travel", "purpose": ""}]}
        write(self.sb.path("learner", "timetable.json"), json.dumps(store))
        self.assertIn("timetable.json (this date)", self.sb.run("day", "thu"))
        self.sb.run("day", "done", "7", expect=2)
        self.sb.run("day", "next-month", expect=2)
        self.assertIn("note for 2026-03-04 removed", self.sb.run("day", "note", "2026-03-04", ""))

    def test_no_schedule_says_where_to_write_one(self):
        self.assertIn("no blocks", self.sb.run("day"))
        self.assertNotIn("Now:", self.sb.run("brief"))


class Timetable(Case):
    def test_it_reads_the_engine_and_installs_nothing_unasked(self):
        with open(os.path.join(REPO, "tools", "timetable.py"), "r", encoding="utf-8") as fh:
            source = fh.read()
        self.assertNotIn("sudo", source)
        self.assertNotIn("/var/x", source)
        self.sb.onboard()
        write(self.sb.path("learner", "schedule.md"), FRONT)
        env = dict(os.environ, CALAMITY_ROOT=self.sb.root, CALAMITY_NOW=TUESDAY, TIMETABLE_NO_TUI="1",
                   HOME=self.sb.root, NO_COLOR="1")
        proc = subprocess.run([sys.executable, os.path.join(REPO, "tools", "timetable.py"), "print", "2026-03-03"],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, timeout=60)
        out = proc.stdout.decode("utf-8")
        self.assertEqual(proc.returncode, 0, proc.stderr.decode("utf-8", "replace"))
        self.assertIn("GATE block A", out)
        self.assertFalse(os.path.exists(self.sb.path(".local")))           # printing installs nothing
        self.assertTrue(os.path.isfile(os.path.join(ENGINE, "calamity.py")))
