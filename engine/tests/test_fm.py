import unittest

from tests import helpers

from cal import fm
from cal.util import CalError


assert helpers.ENGINE  # importing the helpers puts the engine on sys.path


class FrontMatter(unittest.TestCase):
    def test_scalars_and_lists(self):
        meta, body = fm.parse(
            "---\n"
            "id: docker\n"
            "est_hours: 20\n"
            "ratio: 0.5\n"
            "optional: false\n"
            "empty:\n"
            "prereqs: [linux-shell, \"slot:language\"]\n"
            "gate.papers: [CS, DA]   # dotted keys are flat keys\n"
            "summary: \"Images: layers, and more\"\n"
            "version: \"1200\"\n"
            "---\n"
            "\nBody text\n"
        )
        self.assertEqual(meta["id"], "docker")
        self.assertEqual(meta["est_hours"], 20)
        self.assertEqual(meta["ratio"], 0.5)
        self.assertIs(meta["optional"], False)
        self.assertIsNone(meta["empty"])
        self.assertEqual(meta["prereqs"], ["linux-shell", "slot:language"])
        self.assertEqual(meta["gate.papers"], ["CS", "DA"])
        self.assertEqual(meta["summary"], "Images: layers, and more")
        self.assertEqual(meta["version"], "1200")
        self.assertEqual(body.strip(), "Body text")

    def test_block_list(self):
        meta, _ = fm.parse("---\ntags:\n  - a\n  - b c\nname: x\n---\n")
        self.assertEqual(meta["tags"], ["a", "b c"])
        self.assertEqual(meta["name"], "x")

    def test_dates_and_times_stay_text(self):
        meta, _ = fm.parse("---\nday: 2027-02-06\nat: 23:30\nexam_days: [2027-02-06, 2027-02-07]\n---\n")
        self.assertEqual(meta["day"], "2027-02-06")
        self.assertEqual(meta["at"], "23:30")
        self.assertEqual(meta["exam_days"], ["2027-02-06", "2027-02-07"])

    def test_round_trip(self):
        meta = {"id": "cp.dp", "title": "DP: the basics", "band": 1200, "tags": ["dfs and similar", "2-sat", "1200"],
                "optional": True, "ratio": 0.25, "summary": "a, b and c", "note": "ends with colon:", "dash": "- x"}
        text = fm.dump(meta, "# Scope\n\n- one\n")
        again, body = fm.parse(text)
        self.assertEqual(again, meta)
        self.assertEqual(body.strip(), "# Scope\n\n- one")

    def test_no_front_matter(self):
        meta, body = fm.parse("# Just a file\n")
        self.assertEqual(meta, {})
        self.assertEqual(body, "# Just a file\n")

    def test_crlf_and_bom(self):
        meta, body = fm.parse("﻿---\r\nid: a\r\n---\r\nline\r\n")
        self.assertEqual(meta, {"id": "a"})
        self.assertEqual(body, "line\n")

    def test_errors(self):
        with self.assertRaises(CalError):
            fm.parse("---\nid: a\n")  # never closed
        with self.assertRaises(CalError):
            fm.parse("---\nmap: {a: 1}\n---\n")
        with self.assertRaises(CalError):
            fm.parse("---\ntext: |\n---\n")
        with self.assertRaises(CalError):
            fm.parse("---\nnot a key value line\n---\n")
        with self.assertRaises(CalError):
            fm.parse("---\nlist: [a, b\n---\n")


class Sections(unittest.TestCase):
    BODY = (
        "Intro\n\n# Scope\n\n- one\n\n```\n# not a heading\n```\n\n# Topics\n\n"
        "## images | Images and containers\nlevel: 1\nneeds: []\n- say what an image is\n\n"
        "## `multi-stage` | Multi-stage builds\nneeds: [images]\nlevel: 3\nunknown: stays in the body\n- two stages\n\n"
        "## bare-id\n- no title given\n\n# Boss\n\nBuild it.\n"
    )

    def test_section_text(self):
        self.assertEqual(fm.section_text(self.BODY, "Boss"), "Build it.")
        self.assertIn("# not a heading", fm.section_text(self.BODY, "scope"))
        self.assertEqual(fm.section_text(self.BODY, "Missing"), "")

    def test_entries(self):
        got = fm.entries(self.BODY, "Topics", ("needs", "level"))
        self.assertEqual([e["id"] for e in got], ["images", "multi-stage", "bare-id"])
        self.assertEqual(got[0]["title"], "Images and containers")
        self.assertEqual(got[0]["meta"], {"level": 1, "needs": []})
        self.assertEqual(got[0]["body"], "- say what an image is")
        self.assertEqual(got[1]["meta"], {"needs": ["images"], "level": 3})
        self.assertTrue(got[1]["body"].startswith("unknown: stays in the body"))
        self.assertEqual(got[2]["title"], "Bare id")
        self.assertEqual(fm.entries(self.BODY, "Nothing", ()), [])

    def test_render_entry_round_trip(self):
        text = "# Topics\n\n" + fm.render_entry("lis", "Longest increasing subsequence",
                                                {"needs": ["linear-dp"], "level": 3, "band": None, "aliases": []},
                                                "- O(n log n) with lower_bound")
        got = fm.entries(text, "Topics", ("needs", "level", "band", "aliases"))
        self.assertEqual(got[0]["meta"], {"needs": ["linear-dp"], "level": 3})
        self.assertEqual(got[0]["body"], "- O(n log n) with lower_bound")


if __name__ == "__main__":
    unittest.main()
