import json
import os
import unittest

from tests.helpers import Case, write

from cal import items
from cal.util import CalError


def sealed(kind, answer, **more):
    item = {"id": "it-test000000", "type": kind, "sealed": items.seal({"answer": answer, "solution": "because"})}
    item.update(more)
    return item


class Grading(unittest.TestCase):
    OPTIONS = {"A": "one", "B": "two", "C": "three", "D": "four"}

    def test_mcq(self):
        item = sealed("mcq", "B", options=self.OPTIONS)
        for raw in ("B", "b", "(b)", " Option B ", "b."):
            self.assertEqual(items.grade(item, raw), (True, "B"))
        self.assertEqual(items.grade(item, "c"), (False, "C"))
        for raw in ("E", "A,B", "", "two"):
            with self.assertRaises(CalError):
                items.grade(item, raw)

    def test_msq_needs_the_exact_set(self):
        item = sealed("msq", ["A", "C"], options=self.OPTIONS)
        for raw in ("A,C", "c, a", "AC", "a and c", "A;C", "(a),(c)"):
            self.assertEqual(items.grade(item, raw), (True, ["A", "C"]))
        self.assertEqual(items.grade(item, "A")[0], False)
        self.assertEqual(items.grade(item, "A,B,C")[0], False)

    def test_nat_keys(self):
        self.assertEqual(items._nat_key(42), {"min": 42.0, "max": 42.0})
        self.assertEqual(items._nat_key("7"), {"min": 7.0, "max": 7.0})
        key = items._nat_key("0.42")
        self.assertAlmostEqual(key["min"], 0.415)
        self.assertAlmostEqual(key["max"], 0.425)
        key = items._nat_key("1250.5")  # 0.5% is wider than half a decimal here
        self.assertAlmostEqual(key["max"] - key["min"], 2 * 0.005 * 1250.5)
        self.assertEqual(items._nat_key({"value": 3.5, "tol": 0.1}), {"min": 3.4, "max": 3.6})
        self.assertEqual(items._nat_key({"min": "1/4", "max": 0.3}), {"min": 0.25, "max": 0.3})
        key = items._nat_key("1e-3")
        self.assertLess(key["min"], 0.001)
        self.assertGreater(key["max"], 0.001)
        for bad in (True, {"min": 2, "max": 1}, {"about": 3}, "many"):
            with self.assertRaises(CalError):
                items._nat_key(bad)

    def test_nat_grading(self):
        item = sealed("nat", items._nat_key("0.42"))
        for raw in ("0.42", ".42", "0.4249", " = 0.416", "21/50"):
            self.assertTrue(items.grade(item, raw)[0], raw)
        for raw in ("0.43", "0.4", "42"):
            self.assertFalse(items.grade(item, raw)[0], raw)
        exact = sealed("nat", items._nat_key(120))
        self.assertTrue(items.grade(exact, "120")[0])
        self.assertTrue(items.grade(exact, "120.0")[0])
        self.assertTrue(items.grade(exact, "1,20")[0])  # thousands separators are stripped
        self.assertFalse(items.grade(exact, "121")[0])
        with self.assertRaises(CalError):
            items.grade(exact, "about a hundred")

    def test_short(self):
        key = items._short_key({"accept": ["O(n log n)", "n log n"], "regex": r"\s*o\(\s*n\s*log\s*n\s*\)\s*"})
        item = sealed("short", key)
        for raw in ("O(n log n)", " o(N LOG N). ", "n  log n", "O( n log n )"):
            self.assertTrue(items.grade(item, raw)[0], raw)
        self.assertFalse(items.grade(item, "O(n^2)")[0])
        with self.assertRaises(CalError):
            items._short_key({"accept": [], "regex": None})
        with self.assertRaises(CalError):
            items._short_key({"accept": ["x"], "regex": "("})

    def test_hands_on_items_are_not_auto_graded(self):
        with self.assertRaises(CalError):
            items.grade({"id": "it-x", "type": "task", "sealed": items.seal({})}, "anything")

    def test_gate_marks(self):
        one = {"type": "mcq", "marks": 1}
        two = {"type": "mcq", "marks": 2}
        self.assertEqual(items.marks_for(one, True), 1.0)
        self.assertAlmostEqual(items.marks_for(one, False), -1 / 3)
        self.assertAlmostEqual(items.marks_for(two, False), -2 / 3)
        self.assertEqual(items.marks_for({"type": "msq", "marks": 2}, False), 0.0)
        self.assertEqual(items.marks_for({"type": "nat", "marks": 2}, False), 0.0)
        self.assertEqual(items.marks_for({"type": "nat", "marks": 2}, True), 2.0)
        self.assertIsNone(items.marks_for({"type": "mcq", "marks": None}, True))


class Drafts(Case):
    def base(self, **over):
        data = {"type": "mcq", "topics": ["docker/images"], "difficulty": 2,
                "stem": "Which statement about images is true?", "options": ["w", "x", "y", "z"], "answer": "B",
                "solution": "An image is a read-only template; x says so."}
        data.update(over)
        return data

    def test_validation(self):
        tree = self.sb.tree()
        ok = items.validate_draft(self.base(), tree)
        self.assertEqual(ok["public"]["skill"], "docker")
        self.assertEqual(ok["public"]["options"], {"A": "w", "B": "x", "C": "y", "D": "z"})
        self.assertEqual(ok["public"]["expect_s"], 90)
        self.assertEqual(ok["sealed"]["answer"], "B")
        self.assertNotIn("answer", ok["public"])
        self.assertNotIn("solution", ok["public"])
        bad = (
            {"type": "essay"}, {"topics": []}, {"topics": ["docker/nope"]}, {"topics": ["docker/images", "docker/images"]},
            {"stem": "short"}, {"difficulty": 9}, {"marks": 3}, {"options": ["only one"]}, {"options": ["a", "a"]},
            {"answer": "E"}, {"solution": ""}, {"expect_s": 0}, {"skill": "java"}, {"source": {"kind": "stolen"}},
            {"source": {"kind": "official"}},
        )
        for change in bad:
            with self.assertRaises(CalError, msg=str(change)):
                items.validate_draft(self.base(**change), tree)
        with self.assertRaises(CalError):
            items.validate_draft(["not", "an", "object"], tree)

    def test_types(self):
        tree = self.sb.tree()
        nat = items.validate_draft(self.base(type="nat", answer="2.5", options=None), tree)
        self.assertEqual(nat["public"]["expect_s"], 150)
        task = items.validate_draft({"type": "task", "topics": ["docker/dockerfile", "shell/pipes"],
                                     "stem": "Write a Dockerfile for the service in learner/work/docker/ex1.",
                                     "check": "cd learner/work/docker/ex1 && docker build -t ex1 .  # passes on exit 0"}, tree)
        self.assertEqual(task["public"]["topics"], ["docker/dockerfile", "shell/pipes"])
        self.assertEqual(task["public"]["expect_s"], 900)
        with self.assertRaises(CalError):
            items.validate_draft({"type": "task", "topics": ["docker/dockerfile"], "stem": "Do the task now."}, tree)
        with self.assertRaises(CalError):
            items.validate_draft({"type": "open", "topics": ["docker/images"], "stem": "Explain layers briefly."}, tree)
        gate = items.validate_draft(self.base(topics=["gate.cs.os/deadlock"]), tree)
        self.assertEqual(gate["public"]["marks"], 1)       # GATE items default to one mark
        self.assertEqual(gate["public"]["expect_s"], 90)
        two = items.validate_draft(self.base(topics=["gate.cs.os/deadlock"], marks=2), tree)
        self.assertEqual(two["public"]["expect_s"], 210)

    def test_stored_item_hides_its_key(self):
        sb = self.sb
        ident = sb.draft("docker/images", answer="C", solution="C is right because layers are read-only.")
        path = sb.path("learner", "items", "docker", ident + ".json")
        with open(path, "r", encoding="utf-8") as fh:
            raw = fh.read()
        stored = json.loads(raw)
        self.assertNotIn("answer", stored)
        self.assertNotIn("read-only", raw)
        self.assertEqual(items.unseal(stored)["answer"], "C")
        blind = sb.run("item", "show", ident)
        self.assertIn("status: draft", blind)
        self.assertNotIn("KEY", blind)
        self.assertNotIn("read-only", blind)
        sb.run("item", "show", ident, "--reveal", expect=2)  # a draft is never revealed
        self.assertFalse(os.path.exists(sb.path(".calamity", "tmp", "draft-1.json")))  # the plain draft is removed

    def test_verification(self):
        sb = self.sb
        ident = sb.draft("docker/images", answer="C")
        sb.run("item", "verify", ident, "--answer", "C", expect=2)                       # --by is required
        sb.run("item", "verify", ident, "--answer", "C", "--by", "examiner", expect=2)   # not by its author
        sb.run("item", "verify", ident, "--by", "checker", expect=2)                     # an answer is required
        sb.run("ask", "--id", ident, expect=2)                                           # drafts are never asked
        out = sb.run("item", "verify", ident, "--answer", "A", "--by", "checker")
        self.assertIn("rejected", out)
        self.assertNotIn("KEY", out)                                                     # the key is not leaked
        self.assertNotIn("SOLUTION", out)
        self.assertEqual(sb.state().items[ident].status, "rejected")
        sb.run("item", "verify", ident, "--answer", "C", "--by", "checker", expect=2)    # no second try

        good = sb.draft("docker/images", answer="C")
        self.assertIn("verified", sb.run("item", "verify", good, "--answer", "c", "--by", "checker"))
        self.assertEqual(sb.state().items[good].status, "verified")
        self.assertIn("KEY: C", sb.run("item", "show", good, "--reveal"))

    def test_hands_on_verification(self):
        sb = self.sb
        ident = sb.draft("docker/dockerfile", kind="task")
        sb.run("item", "verify", ident, "--by", "checker", expect=2)             # the check must have been run
        sb.run("item", "verify", ident, "--ran", "--by", "checker", expect=2)    # and evidence given
        shown = sb.run("item", "show", ident, "--check")
        self.assertIn("CHECK", shown)
        self.assertIn("RUBRIC", shown)
        self.assertNotIn("CHECK", sb.run("item", "show", ident))
        sb.run("item", "verify", ident, "--ran", "--evidence", "built ref solution; check passed; empty failed",
               "--by", "checker")
        self.assertEqual(sb.state().items[ident].status, "verified")
        other = sb.draft("docker/dockerfile", kind="task")
        sb.run("item", "verify", other, "--fail", "--evidence", "check passes on an empty folder", "--by", "checker")
        self.assertEqual(sb.state().items[other].status, "rejected")

    def test_import_is_all_or_nothing(self):
        sb = self.sb
        path = sb.path(".calamity", "tmp", "batch.json")
        write(path, json.dumps([self.base(), self.base(stem="A second question about images?", answer="Z")]))
        out = sb.run("item", "import", "--file", path, "--by", "examiner", expect=None) + sb.err
        self.assertEqual(sb.code, 2)
        self.assertIn("item 2 of 2", out)
        self.assertIn("nothing was stored", out)
        self.assertEqual(sb.state().items, {})
        self.assertTrue(os.path.exists(path))
        write(path, json.dumps([self.base(), self.base(stem="A second question about images?", answer="D")]))
        out = sb.run("item", "import", "--file", path, "--by", "examiner")
        self.assertIn("imported 2 item(s)", out)
        self.assertFalse(os.path.exists(path))
        self.assertEqual({it.status for it in sb.state().items.values()}, {"draft"})
        listing = sb.run("item", "list", "--status", "draft")
        self.assertEqual(listing.count("docker/images"), 2)
        self.assertIn("No items match", sb.run("item", "list", "--status", "verified"))

    def test_official_items(self):
        sb = self.sb
        path = sb.path(".calamity", "tmp", "paper.json")
        official = self.base(topics=["gate.cs.os/deadlock"], marks=2,
                             source={"kind": "official", "ref": "GATE CS 2025 Q.31"})
        write(path, json.dumps([self.base(topics=["gate.cs.os/deadlock"])]))
        sb.run("item", "import", "--file", path, "--official", expect=2)  # needs an official source
        write(path, json.dumps([official]))
        out = sb.run("item", "import", "--file", path, "--official")
        ident = out.split("imported 1 item(s): ")[1].split()[0]
        self.assertEqual(sb.state().items[ident].status, "verified")
        # the transcription check disagrees: the item is put on hold, not rejected
        self.assertIn("disputed", sb.run("item", "verify", ident, "--answer", "A", "--by", "checker"))
        self.assertEqual(sb.state().items[ident].status, "disputed")
        sb.run("ask", "--id", ident, expect=2)
        sb.run("item", "restore", ident)
        self.assertEqual(sb.state().items[ident].status, "verified")
        sb.run("item", "restore", ident, expect=2)

    def test_bad_files(self):
        sb = self.sb
        sb.run("item", "draft", expect=2)
        sb.run("item", "draft", "--file", sb.path("nope.json"), expect=2)
        write(sb.path("broken.json"), "{not json")
        sb.run("item", "draft", "--file", sb.path("broken.json"), expect=2)
        sb.run("item", "show", "it-doesnotexist", expect=2)
        sb.run("item", "show", "../../etc/passwd", expect=2)
        out = sb.run("item", "draft", "--stdin", stdin=json.dumps(self.base()))
        self.assertIn("draft stored", out)


if __name__ == "__main__":
    unittest.main()
