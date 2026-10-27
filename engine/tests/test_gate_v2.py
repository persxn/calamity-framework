"""Mastery Gate v2: topics open on evidence, a limit on open topics per skill, same-day consolidation."""
from tests.helpers import Case


class Gate(Case):
    def setUp(self):
        super().setUp()
        self.sb.onboard()
        self.sb.run("enroll", "shell")

    def startable(self, skill=None):
        from cal import plan
        from cal.util import parse_ts

        state = self.sb.state()
        return [c["key"] for c in plan.new_candidates(state.repo, state.tree, state, parse_ts(self.sb.now()), skill=skill)]

    def test_a_topic_opens_once_what_it_builds_on_is_consolidated(self):
        sb = self.sb
        first = sb.item("shell/pipes")
        sb.item("shell/perms")
        sb.run("covered", "shell/pipes")
        self.assertIn("ITEM " + first, sb.run("ask", "--topic", "shell/pipes"))
        sb.answer(first, "B")
        self.assertNotIn("shell/perms", self.startable())           # one right answer: perms (needs pipes) waits
        nxt = sb.run("next")
        self.assertIn("NEXT: consolidate", nxt)
        self.assertIn("not before", nxt)                              # the second item comes 20 minutes later
        sb.advance(minutes=20)
        out = sb.run("ask", expect=4)                                 # time to consolidate, but no second item yet
        self.assertIn("purpose: consolidate", out)
        self.assertIn("shell/pipes (consolidate)", sb.run("item", "needs"))
        second = sb.item("shell/pipes")
        self.assertIn("ITEM " + second, sb.run("ask"))                # never the item it was answered right on
        sb.answer(second, "B")
        state = sb.state()
        self.assertEqual(state.topic_status("shell/pipes"), "consolidating")
        self.assertIn("shell/perms", self.startable())
        self.assertIn("consolidated 1/1", sb.run("today"))

    def test_too_soon_does_not_consolidate(self):
        sb = self.sb
        sb.item("shell/pipes")
        sb.item("shell/pipes")
        sb.do("shell/pipes")
        sb.advance(minutes=5)
        sb.do("shell/pipes")                                          # a second item, but only 5 minutes later
        self.assertEqual(sb.state().topic_status("shell/pipes"), "learning")
        sb.advance(minutes=30)
        sb.do("shell/pipes")
        self.assertEqual(sb.state().topic_status("shell/pipes"), "consolidating")

    def test_an_oral_check_unlocks_nothing(self):
        sb = self.sb
        sb.run("covered", "shell/pipes")
        sb.run("quick", "shell/pipes", "pass")
        sb.advance(minutes=30)
        sb.run("quick", "shell/pipes", "pass")
        state = sb.state()
        self.assertEqual(state.topic_status("shell/pipes"), "learning")
        self.assertNotIn("shell/perms", self.startable())

    def test_the_wip_limit_holds_a_third_topic_and_serves_another_lane(self):
        sb = self.sb
        sb.run("enroll", "java")
        for topic in ("java/classes", "java/collections", "java/streams"):
            sb.item(topic)
        sb.do("java/classes")
        sb.do("java/collections")                                     # two open topics in java: its limit (2)
        self.assertEqual(len(sb.state().open_topics("java")), 2)
        self.assertNotIn("java/streams", self.startable())
        self.assertIn("shell/pipes", self.startable())                 # another lane goes on
        self.assertEqual(self.startable("java"), [])

    def test_the_exam_pace(self):
        sb = self.sb
        sb.run("profile", "set", "cfg.pace.track.dev", "exam")         # the mini tree's shell is track dev
        state = sb.state()
        self.assertEqual(state.pace("shell"), {"name": "exam", "unlock": "learning", "wip": 3,
                                               "consolidate_minutes": 20})
        sb.item("shell/pipes")
        sb.item("shell/pipes")
        sb.item("shell/perms")
        sb.do("shell/pipes", "A")                                     # wrong: what builds on it stays closed
        self.assertNotIn("shell/perms", self.startable())
        sb.advance(minutes=15)
        sb.do("shell/pipes")              # right on another item (the first one's key was shown): open at this pace
        self.assertIn("shell/perms", self.startable())

    def test_brushup_needs_no_consolidation(self):
        sb = self.sb
        sb.run("enroll", "java", "--mode", "brushup")
        sb.item("java/classes")
        sb.do("java/classes")
        state = sb.state()
        self.assertEqual(state.pace("java")["name"], "brushup")
        self.assertIsNone(state.consolidation_due("java/classes"))
        self.assertNotIn("to consolidate", sb.run("today"))
