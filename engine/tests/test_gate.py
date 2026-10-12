import json
import unittest
from datetime import datetime, timedelta

from tests.helpers import Case, Sandbox, write

from cal import gateinfo
from cal.store import Repo


class GateFacts(unittest.TestCase):
    """The shipped facts for the year, as the engine reads them."""

    def setUp(self):
        self.sb = Sandbox(mini=False)
        self.addCleanup(self.sb.close)
        self.sb.onboard(gate__year="2027", gate__papers="CS,DA", tracks="gate-cs,gate-da")

    def test_year_file(self):
        repo = Repo(self.sb.root)
        data = gateinfo.year_data(repo)
        self.assertEqual(data["organiser"], "IIT Madras")
        self.assertEqual(data["exam_days"], ["2027-02-06", "2027-02-07", "2027-02-13", "2027-02-14", "2027-02-20",
                                             "2027-02-21"])
        self.assertEqual((data["questions"], data["marks.total"], data["minutes"]), (65, 100, 180))
        self.assertEqual(data["marks.ga"] + data["marks.cs.maths"] + data["marks.cs.subject"], 100)
        self.assertEqual(data["marks.ga"] + data["marks.da.subject"], 100)
        self.assertEqual(gateinfo.papers(repo), ["CS", "DA"])
        self.assertEqual(gateinfo.exam_date(repo, "CS").isoformat(), "2027-02-06")   # first exam day until told otherwise
        self.assertEqual(gateinfo.days_left(repo, "CS", datetime(2026, 10, 11).date()), 118)

    def test_learner_can_correct_the_year_and_set_a_paper_date(self):
        sb = self.sb
        sb.run("profile", "set", "gate.exam_date.DA", "2027-02-14")
        write(sb.path("learner", "gate", "2027.md"), "---\nresults: 2027-03-20\n---\n")
        repo = Repo(sb.root)
        self.assertEqual(gateinfo.exam_date(repo, "DA").isoformat(), "2027-02-14")
        self.assertEqual(gateinfo.exam_date(repo, "CS").isoformat(), "2027-02-06")
        self.assertEqual(gateinfo.year_data(repo)["results"], "2027-03-20")
        self.assertEqual(gateinfo.year_data(repo)["organiser"], "IIT Madras")

    def test_whole_syllabus_enrols_and_reports(self):
        sb = self.sb
        sb.at("2026-10-11T10:00:00+05:30")
        out = sb.run("gate", "enroll")
        self.assertIn("enrolled 21 GATE subject(s)", out)                             # 1 + 13 + 7
        self.assertIn("already enrolled", sb.run("gate", "enroll"))
        status = sb.run("gate", "status")
        self.assertIn("CS: 118 days to 2027-02-06 (first exam day; paper date not set)", status)
        self.assertIn("foundation phase", status)
        self.assertIn("checked 2026-10-11", status)
        self.assertIn("gate.general-aptitude", status)
        self.assertIn("15.0 ", status)                                                 # official weight: no star
        self.assertIn("8.0*", status)                                                  # a prior weight is starred
        triage = sb.run("gate", "triage")
        self.assertIn("marks marked with a star are priors", triage)
        verdicts = [line.rsplit("  ", 1)[-1].strip() for line in triage.split("\n") if line.startswith("gate.")]
        self.assertEqual(len(verdicts), 21)
        self.assertEqual(verdicts.count("focus"), 7)                                   # the top third
        self.assertEqual(verdicts.count("candidate to drop"), 0)                       # never this far from the exam
        brief = sb.run("brief")
        self.assertIn("GATE 2027: CS in 118 days", brief)
        self.assertIn("GATE phase: foundation phase", brief)
        self.assertIn("GATE 118d", sb.run("statusline"))
        self.assertIn("Calamity", sb.run("remind", "check", "--always"))
        # inside the last ten weeks, untouched low-value subjects are flagged; the learner decides
        sb.at("2027-01-10T10:00:00+05:30")
        late = sb.run("gate", "triage")
        flagged = [line.split()[0] for line in late.split("\n") if line.startswith("gate.") and
                   line.rstrip().endswith("candidate to drop")]
        self.assertEqual(len(flagged), 3)                                              # the bottom 15% of 21
        self.assertNotIn("gate.general-aptitude", flagged)
        self.assertIn("revision phase", sb.run("gate", "status"))
        sb.at("2026-10-11T10:00:00+05:30")
        # shared topics are studied once
        sb.item("gate.cs.linear-algebra/eigenvalues", marks=2)
        out = sb.do("gate.cs.linear-algebra/eigenvalues")
        self.assertIn("same topic elsewhere: gate.da.linear-algebra/eigenvalues", out)
        self.assertIn("marks: +2.00", out)


class GateCompanion(Case):
    def setUp(self):
        super().setUp()
        sb = self.sb
        sb.onboard(gate__year="2027", gate__papers="CS", tracks="gate-cs", gate__target_marks__CS="70")
        sb.at("2026-10-11T10:00:00+05:30")
        sb.run("gate", "enroll")

    def test_needs_papers(self):
        other = Sandbox()
        self.addCleanup(other.close)
        other.onboard()
        self.assertIn("No GATE papers set", other.run("gate", "status"))
        other.run("gate", "enroll", expect=2)
        self.assertIn("No GATE subjects found", other.run("gate", "triage"))

    def test_only_the_learners_papers(self):
        state = self.sb.state()
        self.assertEqual(sorted(state.enrolled_skills()), ["gate.cs.la", "gate.cs.os", "gate.ga"])
        self.assertNotIn("gate.da.la", self.sb.run("gate", "status"))

    def test_marking_and_projection(self):
        sb = self.sb
        one = sb.item("gate.cs.os/deadlock", marks=1, answer="C")
        two = sb.item("gate.cs.os/scheduling", marks=2, answer="C")
        nat = sb.item("gate.cs.os/paging", kind="nat", marks=2, answer="4096")
        sb.ask("gate.cs.os/deadlock")
        self.assertIn("marks: -0.33", sb.answer(one, "A", err="concept"))
        sb.ask("gate.cs.os/scheduling")
        self.assertIn("marks: -0.67", sb.answer(two, "A", err="careless"))
        sb.ask("gate.cs.os/paging")
        self.assertIn("marks: +0.00", sb.answer(nat, "1024", err="method"))            # NAT never goes negative
        sb.advance(days=1)
        sb.ask("gate.cs.os/paging")
        sb.answer(nat, "4096")
        errors = sb.run("gate", "errors")
        self.assertIn("gate.cs.os/deadlock", errors)
        self.assertIn("careless x1", errors)
        status = sb.run("gate", "status")
        self.assertIn("target 70 marks", status)
        # 8 marks x 3 of 3 topics tested x 1 of 4 verified answers right
        self.assertIn("backed by practice so far: 2.0 marks", status)
        self.assertIn("25%", status)

    def test_weights_and_triage(self):
        sb = self.sb
        sb.run("gate", "weight", "docker", "5", "--source", "x", expect=2)             # not a GATE subject
        sb.run("gate", "weight", "gate.cs.os", "9", expect=2)                          # a source is required
        sb.run("gate", "weight", "gate.cs.os", "140", "--source", "x", expect=2)
        sb.run("gate", "weight", "gate.cs.os", "9.5", "--source", "counted from CS 2023-2025 papers")
        triage = sb.run("gate", "triage")
        self.assertIn("9.5 ", triage)
        self.assertNotIn("9.5*", triage)
        rows = [line.split()[0] for line in triage.split("\n") if line.startswith("gate.")]
        self.assertEqual(rows[0], "gate.ga")                                           # 15 marks for 30 hours comes first
        self.assertEqual(sb.state().weights["gate.cs.os"][0], 9.5)

    def test_phases(self):
        sb = self.sb
        self.assertIn("foundation phase", sb.run("gate", "status"))
        sb.at("2026-12-01T10:00:00+05:30")
        self.assertIn("build phase", sb.run("gate", "status"))
        sb.at("2027-01-10T10:00:00+05:30")
        self.assertIn("revision phase", sb.run("gate", "status"))
        sb.at("2027-01-25T10:00:00+05:30")
        self.assertIn("final phase", sb.run("gate", "status"))
        sb.at("2027-03-01T10:00:00+05:30")
        self.assertIn("exam passed", sb.run("gate", "status"))

    def test_mocks(self):
        sb = self.sb
        self.assertIn("No mock scores recorded yet", sb.run("gate", "mocks"))
        sb.run("gate", "mock", "CS", expect=2)
        sb.run("gate", "mock", "CS", "40", expect=2)                                   # which test it was is required
        sb.run("gate", "mock", "computer", "40", "--source", "x", expect=2)
        sb.run("gate", "mock", "CS", "140", "--source", "x", expect=2)
        out = sb.run("gate", "mock", "CS", "48.67", "--source", "series A, full test 1", "--date", "2026-10-04",
                     "--sections", "GA=11.33,OS=5")
        self.assertIn("against the target of 70: -21.3 marks", out)
        sb.advance(days=7)
        sb.run("gate", "mock", "CS", "33", "--max", "50", "--source", "series A, half test")
        mocks = sb.run("gate", "mocks")
        first = [line for line in mocks.split("\n") if line.startswith("2026-10-04")][0]
        self.assertEqual(first.split()[:4], ["2026-10-04", "CS", "48.67", "-21.3"])
        self.assertTrue(first.endswith("series A, full test 1  GA 11.33, OS 5"))
        self.assertIn("66.00", mocks)                                                  # scaled to 100
        self.assertIn("change since first +17.3", mocks)
        self.assertIn("last mock 66.0", sb.run("gate", "status"))
        self.assertIn("last mock 66.0", sb.run("brief"))
        self.assertIn("48.67", sb.run("dash", "gate"))
        sb.run("rebuild")
        with open(sb.path("learner", "PROGRESS.md"), "r", encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("## GATE 2027", text)
        self.assertIn("| 2026-10-04 | CS | 48.67 | series A, full test 1 |", text)

    def test_weights_from_official_papers(self):
        sb = self.sb
        self.assertIn("No fully imported official paper yet", sb.run("gate", "weights"))
        drafts = []
        plan = [("gate.ga/series", 5), ("gate.ga/ratios", 3), ("gate.cs.la/matrices", 6), ("gate.cs.os/deadlock", 20),
                ("gate.cs.os/paging", 16)]                                              # 50 two-mark questions: 100 marks
        number = 0
        for topic, count in plan:
            for _ in range(count):
                number += 1
                drafts.append({"type": "mcq", "topics": [topic], "marks": 2, "difficulty": 3,
                               "stem": "Official question %d, transcribed for the test." % number,
                               "options": ["p %d" % number, "q %d" % number, "r %d" % number, "s %d" % number],
                               "answer": "A", "solution": "The official key says A for this one.",
                               "source": {"kind": "official", "ref": "GATE CS 2025 Q.%d" % number}})
        path = sb.path(".calamity", "tmp", "cs2025.json")
        write(path, json.dumps(drafts))
        sb.run("item", "import", "--file", path, "--official")
        table = sb.run("gate", "weights")
        self.assertIn("gate.cs.os  CS          72.0       1", table)
        self.assertIn("run again with --apply", table)
        self.assertIn("applied 3 weight(s)", sb.run("gate", "weights", "--apply"))
        weights = sb.state().weights
        self.assertEqual(weights["gate.cs.os"], (72.0, "official papers CS (2025)"))
        self.assertEqual(weights["gate.ga"][0], 16.0)
        self.assertNotIn("*", sb.run("gate", "triage").split("\n")[2])


class FinalPhase(Case):
    def setUp(self):
        super().setUp()
        sb = self.sb
        sb.onboard(gate__year="2027", gate__papers="CS", tracks="gate-cs")
        sb.at("2026-10-11T10:00:00+05:30")
        sb.run("gate", "enroll")
        sb.item("gate.cs.os/deadlock")

    def test_every_topic_gets_a_last_review_inside_the_final_phase(self):
        sb = self.sb
        exam = datetime.fromisoformat("2027-02-06T09:00:00+05:30")
        reviewed = []
        for _ in range(12):                                         # keep answering correctly whenever it is due
            ts = sb.state().topics.get("gate.cs.os/deadlock")
            if ts is not None and ts.card is not None:
                if ts.card.due >= exam:
                    break
                sb.at(ts.card.due.isoformat()).advance(hours=1)
            sb.do("gate.cs.os/deadlock")
            reviewed.append(sb.clock)
        # without the rule, a review in December would have pushed the next one past the exam;
        # with it, the topic is seen once more between three weeks and three days before the exam
        final = [t for t in reviewed if exam - timedelta(days=21) <= t <= exam - timedelta(days=3) + timedelta(hours=2)]
        self.assertGreaterEqual(len(final), 1, [t.isoformat() for t in reviewed])
        self.assertGreater(sb.state().topics["gate.cs.os/deadlock"].card.due, exam)   # and not again before it
        # the same topic always gets the same place in the phase, whatever its history
        self.assertEqual(sb.state()._final_slot("gate.cs.os/deadlock"), sb.state()._final_slot("gate.cs.os/deadlock"))
        self.assertNotEqual(sb.state()._final_slot("gate.cs.os/deadlock"), sb.state()._final_slot("gate.cs.os/paging"))

    def test_retention_is_tighter_in_the_final_phase(self):
        sb = self.sb
        self.assertEqual(sb.state().retention_for("gate.cs.os", sb.clock), 0.9)
        late = datetime.fromisoformat("2027-01-25T10:00:00+05:30")
        self.assertEqual(sb.state().retention_for("gate.cs.os", late), 0.93)
        self.assertEqual(sb.state().retention_for("docker", late), 0.9)             # only exam subjects

    def test_no_clamp_once_the_exam_has_passed(self):
        sb = self.sb
        sb.at("2027-03-01T10:00:00+05:30")
        sb.do("gate.cs.os/deadlock")
        self.assertGreater(sb.state().topics["gate.cs.os/deadlock"].card.due, sb.clock)


if __name__ == "__main__":
    unittest.main()
