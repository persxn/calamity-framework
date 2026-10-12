import json
import re
import unittest

from tests.helpers import Case, Sandbox, write


class Brief(Case):
    def test_not_onboarded(self):
        out = self.sb.run("brief")
        self.assertTrue(out.startswith("=== CALAMITY BRIEF ==="))
        self.assertIn("NOT ONBOARDED", out)
        self.assertTrue(out.strip().endswith("=== END BRIEF ==="))
        self.assertIn("NEXT: onboard", self.sb.run("next"))
        self.assertIn("Not onboarded", self.sb.run("today"))

    def test_brief_states_facts(self):
        sb = self.sb
        sb.onboard(tracks="dev", teach__style="examples-first", sleep__start="01:00", sleep__end="08:00")
        sb.run("enroll", "shell")
        sb.run("enroll", "java")
        for topic in ("shell/pipes", "java/classes"):
            sb.item(topic)
            sb.do(topic)
        sb.advance(days=5)
        out = sb.run("brief")
        for needle in ("Learner: Tester · tracks: dev · default mode: mastery", "Teaching preferences: examples-first",
                       "Due now (2, most forgotten first):", "Surprise-recall candidates: the first 2 above",
                       "Active skills:", "shell · 0/2 solid · mastery", "Next action: review ",
                       "Sleep window 01:00-08:00", "engine: "):
            self.assertIn(needle, out)
        self.assertLess(len(out), 6100)
        self.assertNotIn("KEY", out)

    def test_hook_mode_never_fails_and_records_the_session(self):
        sb = self.sb
        sb.onboard()
        out = sb.run("brief", "--hook", stdin=json.dumps({"source": "resume", "session_id": "abc"}))
        self.assertIn("=== CALAMITY BRIEF ===", out)
        events = [e for e in sb.state().repo.events() if e["t"] == "session"]
        self.assertEqual([e["src"] for e in events], ["resume"])
        sb.run("brief", "--hook", stdin="not json at all")          # still a brief, exit code 0
        write(sb.path("framework", "tree", "dev", "broken.md"), "---\nid: [unclosed\n---\n")
        self.assertIn("=== END BRIEF ===", sb.run("brief", "--hook", stdin="{}"))


class FinishLine(Case):
    def setUp(self):
        super().setUp()
        self.sb.onboard()

    def test_new_quota_and_reviews(self):
        sb = self.sb
        sb.run("profile", "set", "cfg.new_per_day", "2")
        sb.run("enroll", "shell")
        sb.advance(minutes=1)
        sb.run("enroll", "java")
        for topic in ("shell/pipes", "shell/perms", "java/classes", "java/collections"):
            sb.item(topic)
        self.assertIn("today: reviews 0/0 · new 0/2 · finish line: 2 new to go", sb.run("today"))
        self.assertIn("new, in order: shell/pipes, java/classes", sb.run("today"))   # skills are interleaved
        sb.do("shell/pipes")
        sb.do("java/classes")
        today = sb.run("today")
        self.assertIn("new 2/2 · finish line reached", today)
        nxt = sb.run("next")
        self.assertIn("NEXT: done", nxt)
        self.assertIn("optional: more new material is unlocked", nxt)
        self.assertIn("NEXT: done", sb.run("ask"))                                    # nothing is served past the quota

        sb.advance(days=1)                                                            # next day: nothing due yet
        self.assertIn("reviews 0/0 · new 0/2", sb.run("today"))
        sb.advance(days=2)                                                            # both first reviews are due
        today = sb.run("today")
        self.assertIn("reviews 0/2 · new 0/2", today)
        self.assertIn("finish line: 2 reviews, 2 new to go", today)
        nxt = sb.run("next")
        self.assertIn("NEXT: review", nxt)
        self.assertIn("most forgotten of 2 due", nxt)
        sb.do("shell/pipes")
        sb.do("java/classes")
        self.assertIn("reviews 2/2", sb.run("today"))
        sb.do("shell/perms")
        sb.do("java/collections")
        self.assertIn("finish line reached", sb.run("today"))
        self.assertIn("CAL · due 0 · new 2/2 · done", sb.run("statusline"))

    def test_review_reuse_and_item_needs(self):
        sb = self.sb
        sb.run("enroll", "shell")
        first = sb.item("shell/pipes")
        needs = sb.run("item", "needs")
        self.assertIn("  shell/perms (new)", needs)                                   # it looks past the topic that is next
        self.assertNotIn("  shell/pipes (", needs)
        sb.do("shell/pipes")
        needs = sb.run("item", "needs")
        self.assertIn("  shell/perms (new)", needs)                                   # the next new topic has no item
        self.assertNotIn("  shell/pipes (", needs)                                 # not due today
        spare = sb.draft("shell/perms")
        self.assertIn("  shell/perms (new)", sb.run("item", "needs"))                 # a draft is not stock
        sb.run("item", "verify", spare, "--answer", "B", "--by", "checker")
        self.assertIn("ITEMS: stocked", sb.run("item", "needs"))
        sb.advance(days=3)
        needs = sb.run("item", "needs", "--skill", "shell", "--n", "5")
        self.assertIn("  shell/pipes (review)", needs)                                # due, and its only item was seen
        full = sb.run("item", "needs", "--skill", "shell", "--full")
        self.assertIn("purpose: review", full)
        self.assertIn("bank for this topic: 1 verified", full)
        self.assertEqual(sb.ask("shell/pipes"), first)                                # reuse rather than stall
        sb.run("item", "needs", "--skill", "ghost", expect=2)

    def study_next(self, n):
        """Follow `next` for n new topics; return the topics in the order they came."""
        sb, order = self.sb, []
        for _ in range(n):
            nxt = sb.run("next")
            self.assertIn("NEXT: new", nxt)
            key = re.search(r"^topic: (\S+)", nxt, re.M).group(1)
            order.append(key)
            if "covered %s" % key in nxt:
                sb.run("covered", key)
            sb.do(key)
        return order

    def test_skills_studied_side_by_side_take_turns(self):
        sb = self.sb
        sb.run("enroll", "shell")
        sb.advance(minutes=1)
        sb.run("enroll", "java")
        for topic in ("shell/pipes", "shell/perms", "java/classes", "java/collections", "java/streams"):
            sb.item(topic)
        self.assertIn("new 0/5", sb.run("today"))                 # the target counts what today's work will open
        self.assertEqual(self.study_next(4), ["shell/pipes", "java/classes", "shell/perms", "java/collections"])
        self.assertEqual(self.study_next(1), ["java/streams"])    # the shell is finished: Java carries on alone
        self.assertIn("new 5/5 · finish line reached", sb.run("today"))

    def test_focus_comes_first(self):
        sb = self.sb
        sb.run("enroll", "shell")
        sb.advance(minutes=1)
        sb.run("enroll", "java")
        for topic in ("shell/pipes", "shell/perms", "java/classes", "java/collections", "java/streams"):
            sb.item(topic)
        sb.run("profile", "set", "focus", "java")
        self.assertEqual(self.study_next(4), ["java/classes", "java/collections", "java/streams", "shell/pipes"])
        sb.run("profile", "set", "focus", "dev")                  # a track name puts all of its skills in focus
        self.assertIn("topic: shell/perms", sb.run("next"))

    def test_exam_subjects_share_one_lane(self):
        sb = self.sb
        sb.run("profile", "set", "gate.year", "2027")
        sb.run("profile", "set", "gate.papers", "CS")
        sb.run("gate", "enroll")
        sb.advance(minutes=1)
        sb.run("enroll", "shell")
        for topic in ("gate.ga/series", "gate.ga/ratios", "gate.cs.la/matrices", "gate.cs.la/eigen", "gate.cs.os/deadlock",
                      "gate.cs.os/scheduling", "gate.cs.os/paging", "shell/pipes", "shell/perms"):
            sb.item(topic)
        order = self.study_next(6)
        self.assertEqual([k for k in order if k.startswith("shell/")], ["shell/pipes", "shell/perms"])
        self.assertEqual([order.index(k) for k in order if k.startswith("shell/")], [1, 3])   # every other turn
        exam = [k.split("/")[0] for k in order if k.startswith("gate.")]
        self.assertEqual(len(exam), 4)
        self.assertEqual(exam[0], exam[1])                        # a subject under way is finished before another opens
        sb.run("profile", "set", "focus", "gate")
        self.assertIn("topic: gate.", sb.run("next"))

    def test_failed_topic_is_the_only_thing_left(self):
        sb = self.sb
        sb.run("profile", "set", "cfg.new_per_day", "1")
        sb.run("enroll", "shell")
        ident = sb.item("shell/pipes", answer="C")
        sb.ask("shell/pipes")
        sb.answer(ident, "A", err="guess")
        nxt = sb.run("next")
        self.assertIn("NEXT: review", nxt)
        self.assertIn("failed a few minutes ago; try it again", nxt)
        self.assertNotIn("finish line reached", sb.run("today"))


class Sleep(Case):
    def setUp(self):
        super().setUp()
        sb = self.sb
        sb.onboard(sleep__start="23:30", sleep__end="07:00")
        sb.run("enroll", "shell")
        sb.item("shell/pipes")
        sb.item("shell/perms")
        sb.do("shell/pipes")

    def test_guard_stops_new_material(self):
        sb = self.sb
        sb.at("2026-03-02T22:00:00+05:30")
        self.assertIn("NEXT: new", sb.run("next"))
        sb.at("2026-03-02T22:45:00+05:30")                 # inside the hour before the window
        nxt = sb.run("next")
        self.assertIn("NEXT: wind-down", nxt)
        self.assertIn("23:30", nxt)
        self.assertIn("new material is paused until tomorrow", sb.run("today"))
        self.assertIn("new material is paused, reviews only", sb.run("brief"))

    def test_inside_the_window(self):
        sb = self.sb
        sb.at("2026-03-06T00:30:00+05:30")                 # the review is due and it is past midnight
        nxt = sb.run("next")
        self.assertIn("NEXT: sleep", nxt)
        self.assertIn("1 review(s) are due and can wait", nxt)
        self.assertIn("inside the sleep window", sb.run("today"))
        self.assertIn("it is inside the window now", sb.run("brief"))
        self.assertEqual(sb.run("remind", "check", expect=3), "")           # reminders stay silent
        self.assertIn("Calamity: 1 review due", sb.run("remind", "check", "--always"))
        self.assertIsNotNone(sb.ask("shell/pipes"))        # the learner may still insist

    def test_no_window_set(self):
        sb = Sandbox()
        self.addCleanup(sb.close)
        sb.onboard()
        sb.run("enroll", "shell")
        sb.at("2026-03-03T02:30:00+05:30")
        self.assertIn("NEXT: new", sb.run("next"))
        self.assertNotIn("Sleep window", sb.run("brief"))


class BossDue(Case):
    def test_boss_comes_up_when_every_topic_is_solid(self):
        sb = self.sb
        sb.onboard()
        sb.run("placement", "docker", "--known", "images,dockerfile,multi-stage")
        sb.run("enroll", "docker", "--force")
        self.assertIn("Bosses due:\n  docker | Docker", sb.run("boss", "status"))
        self.assertIn("state: due", sb.run("boss", "status", "docker"))
        self.assertIn("boss due: docker", sb.run("today"))
        self.assertIn("NEXT: boss", sb.run("next"))
        sb.run("boss", "record", "docker", "pass", "--evidence", "all checks ran")
        self.assertIn("No boss is due", sb.run("boss", "status"))
        self.assertIn("state: passed on 2026-03-02", sb.run("boss", "status", "docker"))


if __name__ == "__main__":
    unittest.main()
