"""Practice sets (WP-13): outside questions tracked as metadata, every question revisited, official keys as evidence."""
import json
import os

from tests.helpers import Case, read, write


class Practice(Case):
    def setUp(self):
        super().setUp()
        sb = self.sb
        sb.onboard(gate__year="2027", gate__papers="CS", tracks="gate-cs")
        sb.legacy_pace()
        sb.run("enroll", "gate.cs.os")
        sb.run("practice", "add", "os-pyq", "--title", "OS previous papers", "--items", "1-40", "--key", "official",
               "--source", "printed book, own copy")
        self.map = sb.path(".calamity", "tmp", "os-pyq-map.json")
        write(self.map, json.dumps([
            {"from": 1, "to": 10, "topics": ["gate.cs.os/scheduling"], "type": "nat", "pages": "41-44"},
            {"from": 11, "to": 20, "topics": ["gate.cs.os/deadlock"], "type": "mcq", "pages": "45-47"}]))
        sb.run("practice", "map", "os-pyq", "--file", self.map)

    def record(self, q):
        return self.sb.state().practice["os-pyq"]["qs"][q]

    def test_the_set_file_holds_metadata_only(self):
        text = read(self.sb.path("learner", "practice", "os-pyq.md"))
        self.assertIn("key: official", text)
        self.assertIn("- Q1-10 (nat): gate.cs.os/scheduling · pp. 41-44", text)
        bad = self.sb.path(".calamity", "tmp", "bad.json")
        write(bad, json.dumps([{"from": 1, "to": 2, "topics": [], "question": "What is a TLB?"}]))
        self.sb.run("practice", "map", "os-pyq", "--file", bad, expect=2)
        self.assertIn("no question text", self.sb.err)
        self.sb.run("practice", "log", "os-pyq", "3", "wrong", "--note", "x" * 300, expect=2)

    def test_a_wrong_question_comes_back_twice_before_it_retires(self):
        sb = self.sb
        sb.run("practice", "log", "os-pyq", "12", "wrong", "--err", "concept", "--note", "forgot hold and wait")
        self.assertEqual(round((self.record(12)["due"] - sb.clock).total_seconds() / 86400), 2)
        self.assertIn("No practice question is due", sb.run("practice", "due"))
        sb.advance(days=2, minutes=1)
        self.assertIn("redo Q12 from OS previous papers (pp. 45-47)", sb.run("practice", "due"))
        self.assertIn("NEXT: review", sb.run("next"))           # the topic it went wrong on is due first
        sb.run("practice", "log", "os-pyq", "12", "solved")                     # first right revisit
        self.assertFalse(self.record(12)["retired"])
        self.assertEqual(round((self.record(12)["due"] - sb.clock).total_seconds() / 86400), 7)
        sb.advance(days=7, minutes=1)
        sb.run("practice", "log", "os-pyq", "12", "solved")                     # second in a row
        self.assertTrue(self.record(12)["retired"])
        self.assertEqual(self.record(12)["n"], 3)

    def test_revisits_come_after_due_reviews_and_before_new_material(self):
        sb = self.sb
        sb.item("gate.cs.os/deadlock")
        sb.run("practice", "log", "os-pyq", "30", "skipped")                   # not mapped: no topic is due
        sb.advance(days=2, minutes=1)
        out = sb.run("next")
        self.assertIn("NEXT: practice", out)
        self.assertIn("redo: Q30", out)
        self.assertIn("practice os-pyq", sb.run("today"))

    def test_a_slip_restarts_the_short_ladder_and_a_guess_does_not_count(self):
        sb = self.sb
        sb.run("practice", "log", "os-pyq", "1-3", "solved")
        self.assertEqual(round((self.record(2)["due"] - sb.clock).total_seconds() / 86400), 10)
        sb.advance(days=10, minutes=1)
        sb.run("practice", "log", "os-pyq", "2", "wrong")
        self.assertEqual(round((self.record(2)["due"] - sb.clock).total_seconds() / 86400), 2)
        sb.advance(days=2, minutes=1)
        sb.run("practice", "log", "os-pyq", "2", "guessed")
        self.assertEqual((self.record(2)["streak"], self.record(2)["retired"]), (0, False))
        status = sb.run("practice", "status")
        self.assertRegex(status, r"set\s+key\s+attempted")
        self.assertRegex(status, r"os-pyq\s+official\s+3/40\s+100%")
        self.assertRegex(sb.run("practice", "stats"), r"gate.cs.os/scheduling\s+3\s+100%")

    def test_official_keys_are_evidence_and_other_sets_are_not(self):
        sb = self.sb
        sb.run("practice", "log", "os-pyq", "1-4", "solved")
        ts = sb.state().topics["gate.cs.os/scheduling"]
        self.assertEqual((ts.n_vok, len(ts.ok_items)), (1, 1))                 # one batch, one exercise
        sb.run("practice", "add", "notes-sheet", "--title", "Class sheet", "--items", "10", "--key", "unofficial")
        write(self.map, json.dumps([{"from": 1, "to": 10, "topics": ["gate.cs.os/paging"]}]))
        sb.run("practice", "map", "notes-sheet", "--file", self.map)
        out = sb.run("practice", "log", "notes-sheet", "1-5", "solved")
        self.assertIn("scheduled (not evidence", out)
        ts = sb.state().topics["gate.cs.os/paging"]
        self.assertIsNotNone(ts.card)                                           # scheduled
        self.assertEqual(ts.n_vok, 0)                                           # but not evidence

    def test_no_question_text_is_stored_anywhere(self):
        sb = self.sb
        sb.run("practice", "log", "os-pyq", "5", "wrong", "--note", "TLB: forgot the second access")
        for folder, _, files in os.walk(sb.path("learner", "events")):
            for name in files:
                for line in read(os.path.join(folder, name)).splitlines():
                    e = json.loads(line)
                    if e["t"].startswith("practice"):
                        self.assertFalse({"stem", "question", "text", "options"} & set(e), e)
