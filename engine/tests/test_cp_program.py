"""The CP program's measures (WP-24): time to AC, wrong submissions, editorial dependence, recognition;
judge problem sets as practice sets."""
import json
import os

from tests.helpers import Case, write
from tests.test_cf import NOW, ago, by_id, fixtures, sub


class Program(Case):
    def setUp(self):
        super().setUp()
        sb = self.sb
        sb.onboard(tracks="cp")
        data = fixtures()
        live = sub(13, "1502C", "OK", ago(5), "CONTESTANT")
        live["relativeTimeSeconds"] = 50 * 60                    # accepted 50 minutes into the contest
        data["user.status"].append(live)
        folder = sb.path("fixtures")
        for method, result in data.items():
            write(os.path.join(folder, method + ".json"), json.dumps({"status": "OK", "result": result}))
        sb.env["CALAMITY_CF_FIXTURES"] = folder
        sb.at("2026-10-07T10:00:00+05:30")                       # assigned a day before it was solved
        sb.run("cf", "link", "tester")
        sb.run("cf", "assign", "1503D", "--reason", "dp in the band")
        sb.at("2026-10-09T08:00:00+05:30")                       # the editorial, before 1501B was accepted
        sb.run("cf", "mark", "1501B", "editorial")
        sb.at(NOW)
        sb.run("cf", "mark", "1500A", "recognized")
        sb.run("cf", "mark", "1504A", "missed")
        sb.run("cf", "sync")

    def test_analyse_prints_the_program_measures_by_band(self):
        out = self.sb.run("cf", "analyse")
        self.assertIn("program measures by band", out)
        self.assertRegex(out, r"(?m)^\s*1500\s+1\s+50 min \(1\)\s+2\.0\s+0%")      # the contest solve
        self.assertRegex(out, r"(?m)^\s*1300\s+1\s+1440 min \(1\)\s+0\.0\s+0%")    # from its assignment
        self.assertRegex(out, r"(?m)^\s*1200\s+1\s+-\s+1\.0\s+100%")               # after an editorial
        self.assertIn("recognition on untagged sets: 1 of 2 named the right technique first (50%)", out)

    def test_marks_are_checked(self):
        self.sb.run("cf", "mark", "1500A", "guessed", expect=2)
        self.assertTrue(by_id("1500A"))


class JudgeSets(Case):
    def test_a_cses_set_is_a_practice_set_that_schedules_but_proves_nothing(self):
        sb = self.sb
        sb.onboard(tracks="cp")
        out = sb.run("practice", "add", "cses", "--title", "CSES problem set", "--kind", "cses", "--items", "300")
        self.assertIn("none key", out)
        self.assertIn("their place in the judge's own list", out)
        path = sb.path(".calamity", "tmp", "map.json")
        write(path, json.dumps([{"from": 1, "to": 10, "topics": ["cp.bs/on-answer"], "type": "code"}]))
        sb.run("practice", "map", "cses", "--file", path)
        sb.run("practice", "log", "cses", "3", "solved")
        ts = sb.state().topics["cp.bs/on-answer"]
        self.assertIsNotNone(ts.card)          # scheduled for review
        self.assertEqual(ts.n_vok, 0)          # not evidence
