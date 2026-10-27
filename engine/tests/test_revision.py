"""GATE revision (WP-14): backdated lecture ticks, revision passes, numericals, lecture revision, revision packs."""
import json
import os
import unittest

from tests.helpers import Case, read, write

CATALOGUE = [
    {"id": "l1", "title": "Scheduling", "section": "OS", "order": 1, "minutes": 50, "topics": ["gate.cs.os/scheduling"]},
    {"id": "l2", "title": "Deadlock", "section": "OS", "order": 2, "minutes": 40, "topics": ["gate.cs.os/deadlock"]},
    {"id": "l3", "title": "Paging", "section": "OS", "order": 3, "minutes": 45, "topics": ["gate.cs.os/paging"]},
]

SYLLABUS = """---
skill: gate.cs.os
written: 2026-03-01
sources: [https://gate2027.iitm.ac.in/]
---

# Topics

## deadlock | Deadlock
level: 3
- [T] explain the four conditions of a deadlock
- [N] find a safe sequence with the Banker's algorithm

## scheduling | CPU scheduling
level: 3
- [N] average waiting time under round robin

## paging | Paging
level: 3
- [T] explain what a TLB caches
"""


class Revision(Case):
    def setUp(self):
        super().setUp()
        sb = self.sb
        sb.onboard(gate__year="2027", gate__papers="CS", tracks="gate-cs")
        sb.legacy_pace()
        write(sb.path("learner", "syllabus", "gate.cs.os.md"), SYLLABUS)
        sb.run("enroll", "gate.cs.os")
        sb.run("source", "add", "course", "--title", "Course", "--route", "paste", "--tracks", "gate-cs")
        path = sb.path(".calamity", "tmp", "c.json")
        write(path, json.dumps(CATALOGUE))
        sb.run("source", "import", "course", "--file", path)

    def test_ticks_keep_their_times_and_a_second_sync_logs_nothing(self):
        sb = self.sb
        ticks = sb.path(".calamity", "tmp", "ticks.json")
        write(ticks, json.dumps({"l1": "2026-03-01T19:00:00+05:30", "l2": "2026-03-01T21:30:00+05:30"}))
        self.assertIn("logged 2 lecture(s) at their tick times", sb.run("log", "course", "--file", ticks))
        rec = sb.state().src["course"]
        self.assertEqual(rec["l1"]["ts"].isoformat(), "2026-03-01T19:00:00+05:30")
        self.assertEqual(sb.state().days["2026-03-01"].src_done, 2)                # counted on the day they were watched
        self.assertIn("logged 0 lecture(s) at their tick times, 2 already logged", sb.run("log", "course", "--file", ticks))
        sb.run("log", "course", "l3", "--at", "2026-03-01T22:00:00+05:30")
        self.assertEqual(sb.state().src["course"]["l3"]["ts"].isoformat(), "2026-03-01T22:00:00+05:30")
        sb.run("log", "course", "l3", "--at", "2099-01-01T00:00:00+05:30", expect=2)

    def test_passes_are_planned_marked_and_shown(self):
        sb = self.sb
        sb.run("gate", "pass", "gate.cs.os", "1", "--planned", "2026-11-20")
        sb.run("gate", "pass", "gate.cs.os", "2", "--planned", "2026-12-10")
        sb.run("gate", "pass", "gate.cs.os", "1", "--done", "--date", "2026-11-21")
        status = sb.run("gate", "status")
        self.assertIn("gate.cs.os: pass 1 done 2026-11-21 · pass 2 planned 2026-12-10", status)
        self.assertRegex(status, r"gate\.cs\.os\s.*\s1/2\s")
        sb.run("gate", "pass", "gate.cs.os", "1", expect=2)

    def test_numericals_are_counted_and_nudged_once_with_a_cooldown(self):
        sb = self.sb
        nat = sb.item("gate.cs.os/scheduling", kind="nat", answer="4.5")
        sb.do("gate.cs.os/scheduling", answer="4.5")
        out = sb.run("gate", "numericals", "gate.cs.os")
        self.assertRegex(out, r"gate\.cs\.os/scheduling\s+1\s+10")
        self.assertRegex(out, r"gate\.cs\.os/deadlock\s+0\s+10")
        self.assertNotIn("paging", out)                                      # no [N] objective
        for _ in range(4):                                                   # some history, three days on
            sb.advance(days=1)
            sb.run("quick", "gate.cs.os/scheduling", "pass")
        nudge = "numericals check: CPU scheduling, 1 solved, aim about 10"
        self.assertIn(nudge, sb.run("stats", "patterns"))
        sb.run("observe", "raised the study gap", "--tag", "coach", "--pattern", "zero-days")
        self.assertNotIn(nudge, sb.run("brief"))                               # one pattern a day at most
        sb.advance(days=1)
        self.assertIn("Behaviour pattern not yet raised today: " + nudge, sb.run("brief"))
        sb.run("observe", "raised the numericals check", "--tag", "coach", "--pattern", "numericals-low")
        sb.advance(days=1)
        self.assertNotIn(nudge, sb.run("brief"))                               # then it rests (3 days)
        self.assertTrue(nat)

    def test_lectures_with_fading_topics_are_listed_for_revision(self):
        sb = self.sb
        sb.item("gate.cs.os/scheduling")
        sb.run("log", "course", "l1")
        sb.do("gate.cs.os/scheduling")
        self.assertIn("No watched lecture", sb.run("source", "revise"))
        sb.advance(days=60)
        out = sb.run("source", "revise")
        self.assertIn("revise course l1 | Scheduling, 50 min | 1 topic below 85% recall: gate.cs.os/scheduling", out)

    def test_the_pack_has_formulas_and_the_error_book_but_no_keys(self):
        sb = self.sb
        frag = sb.run("notes", "fragment", "gate.cs.os/scheduling").strip().split()[-1]
        path = frag if os.path.isabs(frag) else sb.path(frag)
        write(path, read(path) + "\n## Formulas\n\n- waiting time = turnaround time - burst time\n")
        ident = sb.item("gate.cs.os/deadlock", solution="Option B: hold and wait is the one removed here.")
        sb.do("gate.cs.os/deadlock", answer="A", note="mixed up hold-and-wait and circular wait")
        out = sb.run("gate", "pack", "gate.cs.os")
        self.assertIn("revision pack written: learner/notes/gate.cs.os/revision-pack.md (1 formula section(s), 1 mistake(s))",
                      out.replace("\\", "/"))
        text = read(sb.path("learner", "notes", "gate.cs.os", "revision-pack.md"))
        self.assertIn("waiting time = turnaround time - burst time", text)
        self.assertIn("mixed up hold-and-wait and circular wait", text)
        self.assertIn("item " + ident, text)
        self.assertNotIn("hold and wait is the one removed", text)          # never the solution

    @unittest.skipUnless(__import__("cal.mdbook", fromlist=["x"]).unicode_engine(), "no TeX engine")
    def test_the_pack_builds_a_pdf(self):
        sb = self.sb
        sb.item("gate.cs.os/deadlock")
        sb.do("gate.cs.os/deadlock", answer="A", note="a slip")
        sb.run("gate", "pack", "gate.cs.os", "--pdf")
        self.assertTrue(os.path.isfile(sb.path("learner", "notes", "gate.cs.os", "revision-pack.pdf")))
