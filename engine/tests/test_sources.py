import json
import os
import unittest

from tests.helpers import Case, write


CATALOGUE = [
    {"id": "os-01", "title": "Process states", "section": "Operating Systems", "order": 1, "minutes": 50, "topics": []},
    {"id": "os-02", "title": "Round robin scheduling", "section": "Operating Systems", "order": 2, "minutes": 55,
     "topics": ["gate.cs.os/scheduling"]},
    {"id": "os-03", "title": "Deadlock: Banker's algorithm", "section": "Operating Systems", "order": 3, "minutes": 60,
     "topics": ["gate.cs.os/deadlock"]},
    {"id": "os-04", "title": "Paging part 1", "section": "Operating Systems", "order": 4, "minutes": 45, "topics": []},
    {"id": "os-05", "title": "Paging part 2", "section": "Operating Systems", "order": 5, "minutes": 40,
     "topics": ["gate.cs.os/paging"]},
]


class Sources(Case):
    def setUp(self):
        super().setUp()
        sb = self.sb
        sb.onboard(gate__year="2027", gate__papers="CS", tracks="gate-cs")
        sb.legacy_pace()
        sb.run("enroll", "gate.cs.os")
        out = sb.run("source", "add", "course", "--title", "GATE CS course", "--kind", "course",
                     "--url", "https://example.com/course", "--route", "paste", "--tracks", "gate-cs",
                     "--note", "robots.txt disallows automated access (read 2026-03-02): paste and manual log")
        self.assertIn("learner/sources/course.md", out)
        self.catalogue = sb.path(".calamity", "tmp", "course.json")
        write(self.catalogue, json.dumps(CATALOGUE))

    def test_add_import_check(self):
        sb = self.sb
        self.assertIn("items: 5 added, 0 replaced", sb.run("source", "import", "course", "--file", self.catalogue))
        with open(sb.path("learner", "sources", "course.md"), "r", encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("terms_note:", text)
        self.assertIn("route: paste", text)
        self.assertIn("## os-03 | Deadlock: Banker's algorithm", text)
        self.assertIn("Only progress metadata belongs in this file", text)   # text before the items survives
        check = sb.run("source", "check")
        self.assertIn("2 item(s) not mapped", check)
        self.assertIn("1 source(s), 0 error(s)", check)

        changed = [dict(CATALOGUE[0], topics=["gate.cs.os/nope"])] + [dict(CATALOGUE[3], title="Paging, part one")]
        write(self.catalogue, json.dumps(changed))
        out = sb.run("source", "import", "course", "--file", self.catalogue, expect=2)
        self.assertIn("0 added, 2 replaced", out)
        self.assertIn("maps to unknown topic 'gate.cs.os/nope'", out)
        sb.run("source", "check", expect=2)

        sb.run("source", "add", "course", "--title", "again", expect=2)
        sb.run("source", "add", "Bad.Id", "--title", "x", expect=2)
        sb.run("source", "import", "ghost", "--file", self.catalogue, expect=2)
        write(self.catalogue, json.dumps([{"title": "no id"}]))
        sb.run("source", "import", "course", "--file", self.catalogue, expect=2)

    def test_lecture_first_then_test(self):
        sb = self.sb
        sb.run("source", "import", "course", "--file", self.catalogue)
        nxt = sb.run("next")
        self.assertIn("NEXT: watch", nxt)                         # nothing may be tested before its lecture
        self.assertIn("course os-01 | Process states (50m)", nxt)
        self.assertIn("NEXT: watch", sb.run("ask", "--skill", "gate.cs.os"))
        self.assertIn("next lecture: course os-01 | Process states", sb.run("today"))

        logged = sb.run("log", "course", "os-01")
        self.assertIn("logged: course os-01 | Process states", logged)
        self.assertIn("not mapped to a syllabus topic", logged)
        self.assertIn("NEXT: watch", sb.run("next"))
        logged = sb.run("log", "course", "2")                     # by its number
        self.assertIn("ready to be tested: gate.cs.os/scheduling", logged)
        nxt = sb.run("next")
        self.assertIn("NEXT: new", nxt)
        self.assertIn("lecture logged, not tested yet", nxt)
        self.assertIn("gate.cs.os/scheduling", nxt)
        sb.item("gate.cs.os/scheduling")
        self.assertIsNotNone(sb.ask())                            # served without `covered`: the lecture was the teaching
        self.assertEqual(sb.state().topics["gate.cs.os/scheduling"].covered_by, "source")

        self.assertIn("os-03", sb.run("log", "course", "banker"))  # by a piece of its title
        ambiguous = sb.run("log", "course", "paging", expect=None) + sb.err
        self.assertEqual(sb.code, 2)
        self.assertIn("matches several items: os-04, os-05", ambiguous)
        sb.run("log", "course", "os-99", expect=2)
        sb.run("log", "ghost", "os-01", expect=2)

        status = sb.run("source", "status", "course")
        self.assertIn("3/5 items done (60%)", status)
        self.assertIn("165 of 250 minutes watched", status)
        self.assertIn("next: os-04 | Paging part 1 (45m)", status)
        sb.run("log", "course", "os-03", "--undo")
        self.assertIn("2/5 items done", sb.run("source", "status"))

    def test_lecture_quota_and_accounted_time(self):
        sb = self.sb
        sb.run("source", "import", "course", "--file", self.catalogue)
        sb.run("profile", "set", "cfg.lectures_per_day", "2")
        self.assertIn("lectures 0/2", sb.run("today"))
        self.assertIn("2 lectures", sb.run("today"))
        sb.run("log", "course", "os-01", "--method", "manual-log")
        sb.advance(hours=2)
        sb.run("log", "course", "os-02", "--score", "8/10")
        logged = sb.state().src["course"]
        self.assertEqual((logged["os-01"]["method"], logged["os-02"]["method"], logged["os-02"]["score"]),
                         ("manual-log", "paste", "8/10"))                # without --method the source's route is kept
        today = sb.run("today")
        self.assertIn("lectures 2/2", today)
        sb.run("workout", "45", "--note", "run")
        week = sb.run("stats", "week")
        self.assertIn("2 (1h45m)", week)                         # 50 + 55 minutes of lectures
        self.assertIn("45m", week)
        state = sb.state()
        ds = state.days[state.day(sb.clock)]
        self.assertEqual((ds.src_done, ds.src_min, ds.workout_min), (2, 105, 45))
        self.assertIn("lec 2/2", sb.run("statusline"))

    def test_the_lecture_line_never_asks_for_more_than_the_source_holds(self):
        sb = self.sb
        sb.run("source", "import", "course", "--file", self.catalogue)
        sb.run("profile", "set", "cfg.lectures_per_day", "2")
        sb.run("log", "course", "os-04", "--upto")                       # watched before joining: four of five
        today = sb.run("today")
        self.assertIn("lectures 0/1", today)                             # one lecture is left, not two
        self.assertIn("1 lecture to go", today)
        sb.advance(days=1)
        sb.run("log", "course", "os-05")
        self.assertIn("lectures 1/1", sb.run("today"))
        self.assertIn("lec 1/1", sb.run("statusline"))
        sb.advance(days=1)
        today = sb.run("today")                                          # the course is over: the line goes away
        self.assertNotIn("lectures", today)
        self.assertNotIn("lec ", sb.run("statusline"))
        self.assertNotIn("lectures", sb.run("dash"))

    def test_catching_up_does_not_count_as_today(self):
        sb = self.sb
        sb.run("source", "import", "course", "--file", self.catalogue)
        out = sb.run("log", "course", "os-03", "--upto")
        self.assertIn("logged 3 lecture(s) as watched earlier, up to os-03", out)
        self.assertIn("2 mapped topic(s) are now ready to be tested", out)
        state = sb.state()
        ds = state.days[state.day(sb.clock)]
        self.assertEqual((ds.src_done, ds.src_min), (0, 0))
        self.assertEqual(state.topic_status("gate.cs.os/deadlock"), "covered")     # ready to test, not known
        self.assertEqual(state.topic_status("gate.cs.os/paging"), "new")
        self.assertIn("3/5 items done", sb.run("source", "status"))
        self.assertIn("nothing to log", sb.run("log", "course", "os-02", "--upto"))
        sb.run("log", "course", "os-02", "--upto", "--undo", expect=2)
        self.assertIn("NEXT: new", sb.run("next"))

    def test_a_watched_lecture_is_tested_before_anything_else(self):
        sb = self.sb
        sb.run("source", "import", "course", "--file", self.catalogue)
        sb.run("enroll", "shell")
        for topic in ("gate.cs.os/scheduling", "gate.cs.os/deadlock", "shell/pipes"):
            sb.item(topic)
        self.assertIn("new 0/5", sb.run("today"))             # three behind lectures, two in the shell: not the full 8
        needs = sb.run("item", "needs")
        self.assertIn("  gate.cs.os/paging (new)", needs)     # the bank is stocked for lectures still to be watched
        self.assertNotIn("topic: gate.cs.os/scheduling", needs)
        sb.run("log", "course", "os-02")
        self.assertIn("topic: gate.cs.os/scheduling", sb.run("next"))
        sb.do("gate.cs.os/scheduling")
        self.assertIn("topic: shell/pipes", sb.run("next"))   # the exam lane has had its turn
        sb.run("covered", "shell/pipes")
        sb.do("shell/pipes")
        nxt = sb.run("next")                                  # the exam lane again, and its next topic needs a lecture
        self.assertIn("NEXT: watch", nxt)
        self.assertIn("the next new topic in turn (gate.cs.os/deadlock) is behind a lecture", nxt)
        self.assertIn("course os-03 | Deadlock", nxt)
        self.assertIn("Next action: watch course os-01", sb.run("brief"))    # the first lecture not yet logged
        self.assertIn("topic: shell/perms", sb.run("next", "--skill", "shell"))   # one skill only: no lecture is pushed
        sb.run("log", "course", "os-03")
        nxt = sb.run("next")
        self.assertIn("topic: gate.cs.os/deadlock", nxt)
        self.assertIn("lecture logged, not tested yet", nxt)

    def test_course_subjects_and_self_study_subjects_take_turns(self):
        sb = self.sb
        sb.run("source", "import", "course", "--file", self.catalogue)
        sb.run("enroll", "gate.cs.la")                        # an exam subject the course does not cover
        for topic in ("gate.cs.la/matrices", "gate.cs.la/eigen", "gate.cs.os/scheduling"):
            sb.item(topic)
        seen = []
        for _ in range(2):
            nxt = sb.run("next")
            if "NEXT: watch" in nxt:
                self.assertIn("(gate.cs.os/scheduling) is behind a lecture not watched yet", nxt)
                self.assertIn("or carry on without it for now: gate.cs.la/", nxt)
                sb.run("log", "course", "os-02", "--upto")
                sb.do("gate.cs.os/scheduling")
                seen.append("course")
            else:
                self.assertIn("NEXT: new", nxt)
                self.assertIn("topic: gate.cs.la/", nxt)
                self.assertIn("teach one small chunk", nxt)
                sb.run("covered", "gate.cs.la/matrices")
                sb.do("gate.cs.la/matrices")
                seen.append("self-study")
        self.assertEqual(sorted(seen), ["course", "self-study"])   # one turn each, whichever went first

    def test_a_watched_lecture_is_tested_even_past_the_quota(self):
        sb = self.sb
        sb.run("source", "import", "course", "--file", self.catalogue)
        sb.run("profile", "set", "cfg.new_per_day", "1")
        sb.run("profile", "set", "cfg.lectures_per_day", "2")
        sb.run("enroll", "shell")
        for topic in ("gate.cs.os/scheduling", "shell/pipes", "shell/perms"):
            sb.item(topic)
        self.assertIn("NEXT: watch", sb.run("next"))          # the exam lane goes first, and it needs its lecture
        sb.run("covered", "shell/pipes")                      # the learner does the shell first anyway
        sb.do("shell/pipes")
        self.assertIn("NEXT: watch", sb.run("next"))          # the day's one new topic is done; two lectures are not
        sb.run("log", "course", "os-01")
        sb.run("log", "course", "os-02")
        today = sb.run("today")
        self.assertIn("new 1/1 · lectures 2/2", today)
        self.assertIn("finish line: 1 watched lecture to test to go", today)
        self.assertIn("1 watched lecture to test", sb.run("remind", "check"))
        nxt = sb.run("next")
        self.assertIn("NEXT: new", nxt)
        self.assertIn("topic: gate.cs.os/scheduling", nxt)
        sb.do("gate.cs.os/scheduling")
        self.assertIn("finish line reached", sb.run("today"))
        nxt = sb.run("next")
        self.assertIn("NEXT: done", nxt)                      # the lecture quota is met: no more lectures are pushed
        self.assertIn("optional: more new material is unlocked (shell/perms)", nxt)

    def test_what_the_course_does_not_cover_is_taught_once_its_lectures_are_done(self):
        sb = self.sb
        partial = [dict(row, topics=[]) if row["id"] == "os-05" else row for row in CATALOGUE]
        write(self.catalogue, json.dumps(partial))            # no lecture is mapped to paging
        sb.run("source", "import", "course", "--file", self.catalogue)
        for topic in ("gate.cs.os/scheduling", "gate.cs.os/deadlock"):
            sb.item(topic)
        self.assertIn("NEXT: watch", sb.run("next"))          # paging waits while mapped lectures remain
        sb.run("log", "course", "os-03", "--upto")
        sb.do("gate.cs.os/scheduling")
        sb.do("gate.cs.os/deadlock")
        nxt = sb.run("next")
        self.assertIn("NEXT: new", nxt)
        self.assertIn("topic: gate.cs.os/paging", nxt)
        self.assertIn("teach one small chunk", nxt)           # taught here: the course never reached it

    def test_find_covers_lectures(self):
        sb = self.sb
        sb.run("source", "import", "course", "--file", self.catalogue)
        out = sb.run("find", "round robin")
        self.assertIn("lecture", out)
        self.assertIn("course os-02", out)

    def test_no_sources(self):
        os.remove(self.sb.path("learner", "sources", "course.md"))
        self.assertIn("No study sources connected yet", self.sb.run("source", "status"))


if __name__ == "__main__":
    unittest.main()


class SourceSlices(Case):
    """WP-12: a mapping or syllabus task reads a slice of a source, never the whole file."""

    def setUp(self):
        super().setUp()
        sb = self.sb
        sb.onboard(gate__year="2027", gate__papers="CS", tracks="gate-cs")
        sb.run("enroll", "gate.cs.os")
        sb.run("source", "add", "course", "--title", "GATE CS course", "--route", "paste", "--tracks", "gate-cs",
               "--note", "paste and manual log")
        rows = CATALOGUE + [{"id": "la-01", "title": "Rank", "section": "Linear Algebra", "order": 6,
                             "topics": ["gate.cs.la/matrices"]}]
        path = sb.path(".calamity", "tmp", "course.json")
        write(path, json.dumps(rows))
        sb.run("source", "import", "course", "--file", path)

    def test_sections_then_items(self):
        sb = self.sb
        out = sb.run("source", "show", "course")
        self.assertIn("source course | GATE CS course: 6 items, 2 unmapped", out)
        self.assertIn("  Operating Systems (5, 2)", out)
        self.assertIn("  Linear Algebra (1, 0)", out)
        self.assertNotIn("Banker", out)                                   # no items without a filter
        out = sb.run("source", "show", "course", "--unmapped")
        self.assertIn("os-01 | Process states | Operating Systems | unmapped", out)
        self.assertIn("2 item(s) match", out)
        out = sb.run("source", "show", "course", "--section", "operating", "--limit", "2")
        self.assertIn("5 item(s) match, showing 2", out)
        self.assertIn("... 3 more: --limit 5", out)
        out = sb.run("source", "show", "course", "--topic", "gate.cs.os")
        self.assertIn("os-03 | Deadlock: Banker's algorithm | Operating Systems | gate.cs.os/deadlock", out)
        self.assertNotIn("la-01", out)
        self.assertIn("1 item(s) match", sb.run("source", "show", "course", "--topic", "gate.cs.os/paging"))
        sb.run("source", "show", "course", "--topic", "gate.cs.os/nope", expect=2)

    def test_a_deepened_syllabus_must_keep_the_ids_in_use(self):
        sb = self.sb
        deeper = """---
skill: gate.cs.os
written: 2026-03-02
sources: [https://gate2027.iitr.ac.in/]
---

# Topics

## deadlock | Deadlock
level: 3
- [T] explain the four conditions a deadlock needs and why removing any one prevents it
- [N] run the Banker's algorithm on a 5-process table and find a safe sequence
- [N] find the fewest resources that make a system deadlock-free

## sched | CPU scheduling
level: 3
- [N] average waiting time under round robin with a given quantum
"""
        write(sb.path("learner", "syllabus", "gate.cs.os.md"), deeper)
        out = sb.run("syllabus", "check", "gate.cs.os", expect=2)
        self.assertIn("ERROR gate.cs.os/scheduling is used by lectures but is not in your syllabus", out)
        self.assertIn("ERROR gate.cs.os/paging is used by lectures", out)
        write(sb.path("learner", "syllabus", "gate.cs.os.md"),
              deeper.replace("## sched | CPU scheduling", "## scheduling | CPU scheduling")
              + "\n## paging | Paging\nlevel: 3\n- [N] effective access time with a TLB\n")
        self.assertIn("ok: gate.cs.os has 3 topics (your syllabus)", sb.run("syllabus", "check", "gate.cs.os"))
