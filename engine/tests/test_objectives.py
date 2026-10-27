"""Objectives, coverage and the three strands: items say which objectives they test, and mastery needs them all."""
import json
import re

from tests.helpers import Case, write

SYLLABUS = """---
skill: shell
written: 2026-03-01
sources: [https://www.gnu.org/software/bash/manual/]
---

# Topics

## pipes | Pipes
level: 1
- [T] explain what a pipe hands from one process to the next, and why the shell can start both at once
- [P] chain three commands to filter a log file
- [I] build a two-process pipe with pipe(), fork() and dup2() in a 30-line C program
- explain what happens to a pipe's buffer when the reader is slow
- read the exit status of every command in a pipeline
- tell a pipe from a redirection

## perms | Permissions
needs: [pipes]
level: 2
- [X] read and change file modes
"""


class Objectives(Case):
    def setUp(self):
        super().setUp()
        self.sb.onboard()
        write(self.sb.path("learner", "syllabus", "shell.md"), SYLLABUS)
        self.sb.run("enroll", "shell")

    def tagged(self, objectives):
        return self.sb.item("shell/pipes", objectives=objectives)

    def answer_when_due(self, rounds):
        sb = self.sb
        for _ in range(rounds):
            ts = sb.state().topics["shell/pipes"]
            sb.at(ts.card.due.isoformat()).advance(hours=1)
            sb.do("shell/pipes")

    def test_the_next_block_numbers_every_objective_with_its_strand(self):
        out = self.sb.run("next")
        self.assertIn("objectives (teach every one; items name them by number):", out)
        self.assertIn("  1. [T] explain what a pipe hands", out)
        self.assertIn("  3. [I] build a two-process pipe", out)
        self.assertIn("  6. tell a pipe from a redirection", out)        # all six, not the first four
        show = self.sb.run("tree", "show", "shell")
        self.assertIn("strands: theory 14% · practice 14% · implementation 14% · 4 untagged", show)

    def test_tags_are_checked_and_stored(self):
        sb = self.sb
        draft = {"type": "mcq", "topics": ["shell/pipes"], "stem": "Which process reads the pipe first?",
                 "options": ["a", "b", "c", "d"], "answer": "B", "solution": "B, because the reader blocks.",
                 "objectives": [9]}
        write(sb.path(".calamity", "tmp", "d.json"), json.dumps(draft))
        sb.run("item", "draft", "--file", sb.path(".calamity", "tmp", "d.json"), expect=2)
        self.assertIn("there is no objective 9", sb.err)
        ident = self.tagged([1, 2])
        self.assertEqual(sb.state().items[ident].objectives, [1, 2])
        sb.run("item", "tag", ident, "--strand", "Q", expect=2)
        self.assertIn("tagged %s: strand P" % ident, sb.run("item", "tag", ident, "--strand", "P"))
        self.assertEqual(sb.state().items[ident].objectives, [1, 2])          # a strand alone keeps them

    def test_consolidation_wants_another_objective_when_items_are_tagged(self):
        sb = self.sb
        self.tagged([1])
        self.tagged([1])
        sb.do("shell/pipes")
        sb.advance(minutes=30)
        sb.do("shell/pipes")
        self.assertEqual(sb.state().topic_status("shell/pipes"), "learning")   # the same objective twice
        self.tagged([2])
        sb.advance(minutes=30)
        sb.do("shell/pipes")
        self.assertEqual(sb.state().topic_status("shell/pipes"), "consolidating")

    def test_four_items_on_one_objective_are_not_mastery(self):
        sb = self.sb
        ids = [self.tagged([1]) for _ in range(4)]
        sb.do("shell/pipes")
        sb.advance(minutes=30)
        sb.item("shell/pipes")                                 # an untagged item consolidates it
        sb.do("shell/pipes")
        self.answer_when_due(8)
        state = sb.state()
        self.assertEqual(state.coverage("shell/pipes"), (1, 6))
        self.assertNotIn(state.topic_status("shell/pipes"), ("solid", "mastered"))   # 1 of 6 objectives
        from cal import session
        from cal.util import parse_ts

        block = session.need_item_text(state.repo, state.tree, state, "shell/pipes", parse_ts(sb.now()), "review")
        self.assertIn("not yet answered right on: objectives 2, 3, 4, 5, 6", block)
        for n, ident in zip((2, 3, 4), ids[1:]):               # tagging later credits the answers already given
            sb.run("item", "tag", ident, "--objectives", "1,%d" % n)
        self.assertEqual(sb.state().coverage("shell/pipes"), (4, 6))
        self.assertEqual(sb.state().topic_status("shell/pipes"), "solid")             # 4 of 6 is over 60%
        self.assertIn("4/6", sb.run("tree", "show", "shell"))

    def test_untagged_items_count_as_before(self):
        sb = self.sb
        for _ in range(4):
            sb.item("shell/pipes")
        sb.do("shell/pipes")
        sb.advance(minutes=30)
        sb.do("shell/pipes")
        self.answer_when_due(8)
        state = sb.state()
        self.assertIsNone(state.coverage("shell/pipes"))
        self.assertEqual(state.topic_status("shell/pipes"), "mastered")

    def test_syllabus_check_reads_the_tags(self):
        sb = self.sb
        ident = self.tagged([4])
        out = sb.run("syllabus", "check", "shell")
        self.assertIn("[X] is not a strand tag", out)
        write(sb.path("learner", "syllabus", "shell.md"),
              SYLLABUS.replace("explain what happens to a pipe's buffer", "explain how a pipe's buffer fills"))
        self.assertRegex(sb.run("syllabus", "check", "shell"), r"objectives changed since item\(s\) %s" % re.escape(ident))
