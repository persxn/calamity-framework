import unittest

from tests.helpers import Case, write


class Enrolment(Case):
    def test_prerequisites_gate_enrolment(self):
        sb = self.sb
        sb.onboard()
        self.assertIn("NEXT: enroll", sb.run("next"))
        out = sb.run("enroll", "docker", expect=None) + sb.err
        self.assertEqual(sb.code, 2)
        self.assertIn("docker is locked", out)
        self.assertIn("shell is available", out)
        self.assertIn("enrolled: shell", sb.run("enroll", "shell"))
        forced = sb.run("enroll", "docker", "--force")
        self.assertIn("unmet prerequisites: shell", forced)
        self.assertEqual(sb.state().skill_status("docker"), "active")
        self.assertEqual(sb.state().skill_status("capstone"), "locked")
        self.assertEqual(sb.state().skill_status("java"), "available")
        self.assertIn("no syllabus yet", sb.run("enroll", "python"))
        sb.run("enroll", "nothing", expect=2)
        sb.run("enroll", "shell", "--mode", "cramming", expect=2)

    def test_pause_resume_unenroll(self):
        sb = self.sb
        sb.onboard()
        sb.run("pause", "shell", expect=2)  # not enrolled yet
        sb.run("enroll", "shell")
        sb.item("shell/pipes")
        sb.do("shell/pipes")
        self.assertEqual(len(sb.state().scheduled_topics()), 1)
        sb.run("pause", "shell")
        self.assertEqual(sb.state().skill_status("shell"), "paused")
        self.assertEqual(sb.state().scheduled_topics(), [])
        sb.run("resume", "shell")
        self.assertEqual(len(sb.state().scheduled_topics()), 1)
        sb.run("unenroll", "shell")
        state = sb.state()
        self.assertEqual(state.scheduled_topics(), [])
        self.assertIsNotNone(state.topics["shell/pipes"].card)  # progress is kept


class AskAnswer(Case):
    def setUp(self):
        super().setUp()
        self.sb.onboard()
        self.sb.run("enroll", "shell")

    def test_new_topic_flow(self):
        sb = self.sb
        nxt = sb.run("next")
        self.assertIn("NEXT: new", nxt)
        self.assertIn("topic: shell/pipes | Pipes", nxt)
        self.assertIn("covered shell/pipes", nxt)
        self.assertIn("NEXT: new", sb.run("ask"))          # not taught yet: nothing is served
        self.assertIn("covered: shell/pipes", sb.run("covered", "shell/pipes"))
        again = sb.run("next")                              # taught (perhaps in an earlier session): test, do not reteach
        self.assertIn("do: ask --topic shell/pipes   (taught already, not tested yet", again)
        self.assertNotIn("teach one small chunk", again)
        need = sb.run("ask", expect=4)                      # taught, but the bank is empty
        self.assertTrue(need.startswith("NEED_ITEM"))
        self.assertIn("topic: shell/pipes | Pipes", need)
        self.assertIn("purpose: new", need)
        self.assertIn("difficulty: 1", need)
        self.assertIn("- chain two commands with a pipe", need)
        self.assertIn("bank for this topic: empty", need)

        draft = sb.draft("shell/pipes")
        sb.run("ask", "--topic", "shell/pipes", expect=4)   # a draft is not enough
        sb.run("item", "verify", draft, "--answer", "B", "--by", "checker")
        shown = sb.run("ask")
        self.assertIn("ITEM " + draft, shown)
        self.assertIn("B. second choice", shown)
        self.assertNotIn("KEY", shown)
        self.assertIn("answer %s --answer <letter>" % draft, shown)

        out = sb.answer(draft, "b")
        self.assertIn("CORRECT · %s · shell/pipes" % draft, out)
        self.assertIn("grade: shell/pipes Good", out)
        self.assertIn("KEY: B", out)
        self.assertIn("SOLUTION:", out)
        self.assertIn("shell/pipes: learning; solid needs 2 more correct answers on verified items", out)
        self.assertIn("today: reviews 0/0 · new 1/2", out)
        state = sb.state()
        self.assertEqual(state.topic_status("shell/pipes"), "learning")
        self.assertEqual(state.topics["shell/pipes"].n_vok, 1)
        self.assertEqual(state.today_numbers(sb.clock)["new_done"], 1)
        sb.run("answer", draft, "--answer", "B", expect=2)  # it is no longer open
        self.assertIn("topic: shell/perms", sb.run("next"))  # the next topic is now unlocked

    def test_wrong_answer_comes_back(self):
        sb = self.sb
        ident = sb.item("shell/pipes", answer="C")
        sb.ask("shell/pipes")
        sb.run("answer", ident, "--answer", "A", "--err", "nonsense", expect=2)
        out = sb.answer(ident, "A", err="concept", note="mixed up | and >")
        self.assertIn("WRONG", out)
        self.assertIn("KEY: C", out)
        state = sb.state()
        ts = state.topics["shell/pipes"]
        self.assertEqual(ts.errors, {"concept": 1})
        self.assertEqual((ts.card.due - sb.clock).total_seconds(), 600)
        self.assertIn("answer again today: shell/pipes", sb.run("today"))
        self.assertIn("1 to re-answer correctly", sb.run("today"))
        self.assertIn("NEXT: new", sb.run("next"))          # it is not due for ten minutes: something else meanwhile
        sb.advance(minutes=11)
        nxt = sb.run("next")
        self.assertIn("NEXT: review", nxt)
        self.assertIn("failed earlier today", nxt)
        again = sb.do("shell/pipes", "C")
        self.assertIn("CORRECT", again)
        self.assertIn("answered after seeing the solution today", again)
        ts = sb.state().topics["shell/pipes"]
        self.assertEqual((ts.n, ts.n_ok, ts.n_vok), (2, 1, 0))  # scheduled, but not evidence
        self.assertNotIn("answer again today", sb.run("today"))
        self.assertIn("shell/pipes", sb.run("stats", "errors"))

    def test_grade_follows_hints_and_time(self):
        sb = self.sb
        for topic in ("shell/pipes", "shell/perms"):
            sb.item(topic)
        self.assertIn("grade: shell/pipes Good", sb.do("shell/pipes", seconds=5))      # a first answer is never Easy
        self.assertIn("grade: shell/perms Hard", sb.do("shell/perms", hints="1"))
        sb.advance(days=3)
        self.assertIn("grade: shell/pipes Easy", sb.do("shell/pipes", seconds=20))     # under half the expected 90 s
        sb.advance(days=10)
        self.assertIn("grade: shell/pipes Hard", sb.do("shell/pipes", seconds=200))    # over twice the expected time
        self.assertEqual(sb.state().topics["shell/pipes"].slow, 1)
        sb.advance(days=10)
        self.assertIn("grade: shell/pipes Good", sb.do("shell/pipes", seconds=80))

    def test_quick_check_is_not_evidence(self):
        sb = self.sb
        out = sb.run("quick", "shell/pipes", "pass")
        self.assertIn("CORRECT (oral check)", out)
        ts = sb.state().topics["shell/pipes"]
        self.assertIsNotNone(ts.card)
        self.assertEqual((ts.n_ok, ts.n_vok), (1, 0))
        self.assertEqual(sb.state().topic_status("shell/pipes"), "learning")
        sb.run("quick", "shell/pipes", "fail", "--err", "memory", "--note", "blanked")
        self.assertEqual(sb.state().topics["shell/pipes"].errors, {"memory": 1})
        sb.run("quick", "shell/pipes", "maybe", expect=2)
        sb.run("quick", "shell/perms", "fail", expect=2)      # never taught, never answered: nothing to bring back
        self.assertIn("has not been studied yet", sb.err)
        self.assertNotIn("shell/perms", sb.state().topics)
        sb.run("covered", "shell/perms")
        sb.run("quick", "shell/perms", "fail", "--err", "concept")
        self.assertEqual(sb.state().topics["shell/perms"].card.lapses, 1)

    def test_mistake_is_classified_after_the_answer(self):
        sb = self.sb
        ident = sb.item("shell/pipes", answer="C")
        sb.run("mistake", ident, "careless", expect=2)                    # nothing has been answered yet
        sb.ask("shell/pipes")
        out = sb.answer(ident, "A")
        self.assertIn("record it: mistake %s concept|" % ident, out)
        self.assertEqual(sb.state().topics["shell/pipes"].errors, {"unclassified": 1})
        out = sb.run("mistake", ident, "careless", "--note", "read > where it said |")
        self.assertIn("recorded as careless (was: unclassified)", out)
        self.assertEqual(sb.state().topics["shell/pipes"].errors, {"careless": 1})
        sb.run("mistake", ident, "concept")                               # a second look replaces the first
        state = sb.state()
        self.assertEqual(state.topics["shell/pipes"].errors, {"concept": 1})
        self.assertEqual([tag for _, tag in state.topics["shell/pipes"].err_log], ["concept"])
        self.assertIn("concept x1", sb.run("stats", "errors"))
        sb.run("mistake", ident, "sloppy", expect=2)
        sb.run("mistake", "it-aaaaaaaaaa", "concept", expect=2)
        sb.advance(minutes=11)
        self.assertNotIn("mistake", sb.do("shell/pipes", "C"))            # right this time: nothing to classify
        sb.run("mistake", ident, "careless", expect=2)
        self.assertIn("was correct", sb.err)
        ident2 = sb.item("shell/perms", answer="C")
        sb.ask("shell/perms")
        self.assertNotIn("record it: mistake", sb.answer(ident2, "A", err="memory"))   # already said with the answer

    def test_ask_due_serves_reviews_only(self):
        sb = self.sb
        for _ in range(2):
            sb.item("shell/pipes")
        sb.run("covered", "shell/pipes")
        out = sb.run("ask", "--due")
        self.assertIn("NEXT: new", out)                                   # nothing is due, and new material is not served
        self.assertNotIn("ITEM it-", out)
        self.assertEqual(sb.state().items[sorted(sb.state().items)[0]].n_shown, 0)
        sb.do("shell/pipes")
        sb.advance(days=5)
        self.assertIn("ITEM it-", sb.run("ask", "--due"))                 # now it is a review

    def test_hands_on_item(self):
        sb = self.sb
        ident = sb.item("shell/perms", kind="task")
        shown = sb.run("ask", "--topic", "shell/perms")
        self.assertIn("--result pass|fail", shown)
        self.assertNotIn("CHECK", shown)
        self.assertIn("CHECK", sb.run("item", "show", ident, "--check"))
        sb.run("answer", ident, "--answer", "B", expect=2)
        sb.run("answer", ident, "--result", "pass", expect=2)  # evidence is required
        sb.advance(minutes=12)
        out = sb.run("answer", ident, "--result", "pass", "--evidence", "ran chmod 640; ls -l shows rw-r-----")
        self.assertIn("CORRECT", out)
        self.assertEqual(sb.state().topics["shell/perms"].n_vok, 1)

    def test_dispute_voids_an_unfair_answer(self):
        sb = self.sb
        keys = {sb.item("shell/pipes", answer="C"): "C", sb.item("shell/pipes", answer="B"): "B"}
        first = sb.ask("shell/pipes")
        sb.answer(first, keys[first])
        ident = first
        before = sb.state().topics["shell/pipes"]
        sb.advance(days=3)
        asked = sb.ask("shell/pipes")
        self.assertNotEqual(asked, first)              # an unseen item is preferred
        sb.answer(asked, "D", err="concept")
        self.assertEqual(sb.state().topics["shell/pipes"].errors, {"concept": 1})
        out = sb.run("item", "dispute", asked, "--reason", "two options are correct", "--void")
        self.assertIn("no longer counts", out)
        state = sb.state()
        after = state.topics["shell/pipes"]
        self.assertEqual(state.items[asked].status, "disputed")
        self.assertEqual((after.n, after.n_ok, after.errors), (before.n, before.n_ok, {}))
        self.assertEqual(after.card.due, before.card.due)
        self.assertEqual(state.n_voided, 1)
        sb.run("ask", "--id", asked, expect=2)
        sb.run("item", "reject", ident, "--reason", "x", "--void", expect=2)
        sb.run("item", "dispute", ident, expect=2)     # a reason is required


class Mastery(Case):
    def setUp(self):
        super().setUp()
        self.sb.onboard()
        self.sb.run("enroll", "shell")

    def until(self, topic, status, limit=8):
        """Answer the topic correctly each time it comes due until it reaches `status`."""
        sb = self.sb
        for n in range(1, limit + 1):
            state = sb.state()
            ts = state.topics.get(topic)
            if ts is not None and ts.card is not None and ts.card.due > sb.clock:
                sb.at(ts.card.due.isoformat()).advance(hours=1)
            sb.do(topic)
            if sb.state().topic_status(topic) == status:
                return n
        self.fail("%s did not reach %s in %d answers" % (topic, status, limit))

    def test_solid_then_mastered(self):
        sb = self.sb
        for _ in range(4):
            sb.item("shell/pipes")
        sb.do("shell/pipes")
        sb.advance(minutes=30)
        sb.do("shell/pipes")
        sb.advance(minutes=30)
        sb.do("shell/pipes")
        state = sb.state()
        self.assertEqual(state.topics["shell/pipes"].n_vok, 3)
        self.assertEqual(state.topic_status("shell/pipes"), "learning")   # three right, but all on one day
        answers = self.until("shell/pipes", "solid")
        self.assertLessEqual(answers, 3)
        ts = sb.state().topics["shell/pipes"]
        self.assertGreaterEqual(len(ts.ok_days), 2)
        self.assertGreaterEqual(ts.card.s, 7)
        self.until("shell/pipes", "mastered")
        ts = sb.state().topics["shell/pipes"]
        self.assertGreaterEqual(ts.card.s, 21)
        self.assertGreaterEqual(len(ts.ok_items), 4)

    def test_one_item_is_never_mastery(self):
        sb = self.sb
        sb.item("shell/pipes")
        self.until("shell/pipes", "solid")
        for _ in range(6):
            ts = sb.state().topics["shell/pipes"]
            sb.at(ts.card.due.isoformat()).advance(hours=1)
            sb.do("shell/pipes")
        self.assertEqual(sb.state().topic_status("shell/pipes"), "solid")
        self.assertIn("more distinct item", sb.run("tree", "show", "shell") + sb.do("shell/pipes"))

    def test_skill_unlocks_dependents_when_ready(self):
        sb = self.sb
        for topic in ("shell/pipes", "shell/perms"):
            sb.item(topic)
        self.assertEqual(sb.state().skill_status("docker"), "locked")
        self.until("shell/pipes", "solid")
        self.assertEqual(sb.state().skill_status("shell"), "active")      # 1 of 2 solid is under 60%
        self.assertEqual(sb.state().skill_status("docker"), "locked")
        self.until("shell/perms", "solid")
        state = sb.state()
        self.assertEqual(state.skill_status("shell"), "ready")
        self.assertEqual(state.skill_status("docker"), "available")
        self.assertIn("enrolled: docker", sb.run("enroll", "docker"))

    def test_a_failure_takes_solid_away(self):
        sb = self.sb
        sb.item("shell/pipes")
        self.until("shell/pipes", "solid")
        ts = sb.state().topics["shell/pipes"]
        sb.at(ts.card.due.isoformat()).advance(hours=1)
        sb.do("shell/pipes", "A", err="memory")
        state = sb.state()
        self.assertEqual(state.topic_status("shell/pipes"), "learning")
        self.assertEqual(state.topics["shell/pipes"].card.lapses, 1)

    def test_brushup_mode(self):
        sb = self.sb
        sb.run("enroll", "java", "--mode", "brushup")
        for topic in ("java/classes", "java/collections", "java/streams"):
            sb.item(topic)
        sb.do("java/classes")
        state = sb.state()
        self.assertEqual(state.topic_status("java/classes"), "solid")     # one verified answer is enough
        self.assertEqual(state.skill_status("java"), "active")
        sb.do("java/collections")
        self.assertEqual(sb.state().skill_status("java"), "ready")        # 2 of 3 is over 50%
        self.assertEqual(sb.state().skill_status("api"), "available")
        sb.do("java/streams")
        self.assertEqual(sb.state().skill_status("java"), "mastered")     # brush-up has no boss
        self.assertEqual(sb.state().retention_for("java", sb.clock), 0.85)
        self.assertEqual(sb.state().retention_for("shell", sb.clock), 0.9)


class Weaving(Case):
    def setUp(self):
        super().setUp()
        sb = self.sb
        sb.onboard()
        sb.run("enroll", "shell")
        sb.run("enroll", "docker", "--force")
        sb.run("enroll", "java")
        for topic in ("shell/pipes", "docker/images", "docker/dockerfile"):
            sb.item(topic)
            sb.do(topic)

    def test_earlier_skills_are_offered_for_embedding(self):
        sb = self.sb
        self.assertIn("WEAVE: none", sb.run("weave", "java"))            # learnt today: too fresh to weave
        sb.advance(days=1)
        out = sb.run("weave", "java")
        self.assertIn("WEAVE for java", out)
        self.assertIn("docker/", out)                                    # Docker weaves into runnable skills
        self.assertIn("shell/pipes", out)                                # the shell weaves into the dev track
        self.assertEqual(out.count("recall chance"), 2)
        self.assertEqual(sb.run("weave", "java", "--n", "1").count("recall chance"), 1)
        self.assertNotIn("java/", sb.run("weave", "docker"))             # Java does not weave into Docker
        need = sb.run("ask", "--topic", "java/classes", expect=4)
        self.assertIn("embed (earlier topics", need)
        self.assertIn("docker/", need)
        needs = sb.run("item", "needs", "--skill", "java")
        self.assertIn("ITEMS NEEDED", needs)
        self.assertIn("topic: java/classes | Classes", needs)
        self.assertIn("embed", needs)

    def test_one_answer_credits_every_woven_topic(self):
        sb = self.sb
        sb.advance(days=1)
        before = sb.state().topics["docker/dockerfile"].card.due
        ident = sb.item("java/classes", kind="task", also=["docker/dockerfile", "shell/pipes"])
        sb.ask("java/classes")
        sb.advance(minutes=15)
        out = sb.run("answer", ident, "--result", "pass", "--evidence", "mvn package ok; docker build ok; image runs")
        self.assertIn("grade: java/classes Good", out)
        self.assertIn("also credited: docker/dockerfile Good", out)
        self.assertIn("also credited: shell/pipes Good", out)
        state = sb.state()
        self.assertGreater(state.topics["docker/dockerfile"].card.due, before)
        self.assertEqual(state.topics["docker/dockerfile"].n_vok, 2)
        self.assertEqual(state.topics["java/classes"].n_vok, 1)
        # crediting a woven review does not count as new material for the other skills
        self.assertEqual(state.days[state.day(sb.clock)].new, 1)

    def test_blame_spares_the_other_topics(self):
        sb = self.sb
        sb.advance(days=1)
        ident = sb.item("java/classes", kind="task", also=["docker/dockerfile", "shell/pipes"])
        sb.ask("java/classes")
        sb.advance(minutes=15)
        sb.run("answer", ident, "--result", "fail", "--blame", "ghost/topic", "--evidence", "x", expect=2)
        out = sb.run("answer", ident, "--result", "fail", "--blame", "docker/dockerfile", "--err", "syntax",
                     "--evidence", "java part fine; Dockerfile COPY path wrong")
        self.assertIn("WRONG", out)
        self.assertIn("docker/dockerfile Again", out)
        state = sb.state()
        self.assertEqual(state.topics["docker/dockerfile"].card.lapses, 1)
        self.assertEqual(state.topics["shell/pipes"].card.lapses, 0)
        self.assertTrue("java/classes" not in state.topics or state.topics["java/classes"].card is None)
        ds = state.days[state.day(sb.clock)]
        self.assertEqual((ds.new, ds.reviews), (0, 1))                   # the day counts it as a Docker review
        self.assertEqual(state.today_numbers(sb.clock)["new_done"], 0)   # Java's topic is still to be learnt

    def test_equivalent_exam_topics_move_together(self):
        sb = self.sb
        sb.run("enroll", "gate.cs.la")
        sb.run("enroll", "gate.da.la")
        sb.item("gate.cs.la/matrices")
        out = sb.do("gate.cs.la/matrices")
        self.assertIn("same topic elsewhere: gate.da.la/matrices Good", out)
        self.assertIn("marks: +1.00", out)
        state = sb.state()
        self.assertEqual(state.topics["gate.da.la/matrices"].n_vok, 1)
        self.assertIsNone(state.topics["gate.da.la/matrices"].first_day)     # not new material twice
        self.assertEqual(state.days[state.day(sb.clock)].new, 4)             # three in setUp plus this one
        self.assertNotIn("embed", sb.run("ask", "--topic", "gate.cs.la/eigen", expect=4))  # exam items are not woven


class PlacementAndBoss(Case):
    def setUp(self):
        super().setUp()
        self.sb.onboard()

    def test_partial_placement(self):
        sb = self.sb
        out = sb.run("placement", "java", "--known", "classes,collections", "--gaps", "streams")
        self.assertIn("java -> partial", out)
        self.assertIn("enroll java", out)
        state = sb.state()
        self.assertEqual(state.topic_status("java/classes"), "solid")
        self.assertEqual(state.topic_status("java/streams"), "new")
        self.assertEqual(state.skill_status("java"), "ready")                 # 2 of 3 solid
        self.assertEqual(state.scheduled_topics(), [])                        # not enrolled: nothing is scheduled
        self.assertEqual(state.today_numbers(sb.clock)["new_done"], 0)        # a placement is not today's new work
        sb.run("enroll", "java")
        state = sb.state()
        dues = sorted((ts.card.due - sb.clock).days for _, ts in state.scheduled_topics())
        self.assertEqual(len(dues), 2)
        self.assertTrue(all(1 <= d <= 14 for d in dues), dues)                # confirmations are spread out
        self.assertIn("first real review pending", sb.run("tree", "show", "java") + sb.run("quick", "java/classes", "pass"))
        sb.run("placement", "java", "--known", "nope", expect=2)
        sb.run("placement", "java", "--known", "classes", "--gaps", "classes", expect=2)
        sb.run("placement", "java", "--result", "known", "--gaps", "streams", expect=2)

    def test_placement_test_answers(self):
        """In the test itself a right answer is evidence, and a miss only leaves the topic to be taught."""
        sb = self.sb
        ids = {t: sb.item("java/" + t) for t in ("classes", "collections", "streams")}
        sb.ask("java/classes")
        self.assertIn("grade: java/classes Easy", sb.answer(ids["classes"], "B", seconds=20, kind="placement"))
        sb.ask("java/collections")
        self.assertIn("grade: java/collections Good", sb.answer(ids["collections"], "B", seconds=80, kind="placement"))
        sb.ask("java/streams")
        out = sb.answer(ids["streams"], "A", seconds=80, kind="placement")
        self.assertIn("WRONG", out)
        self.assertIn("grade: java/streams Again · not scheduled", out)
        self.assertIn("placement: not known yet", out)
        self.assertIn("java/streams: new", out)
        state = sb.state()
        self.assertIsNone(state.topics["java/streams"].card)
        self.assertEqual(state.topics["java/streams"].errors, {})             # not knowing it yet is not a mistake
        self.assertEqual(state.topics["java/classes"].n_vok, 1)
        self.assertEqual(state.items[ids["streams"]].n_fail, 1)
        n = state.today_numbers(sb.clock)
        self.assertEqual((n["new_done"], n["relearn"], n["attempts"], n["ok"]), (0, [], 3, 2))
        ds = state.days[state.day(sb.clock)]
        self.assertEqual((ds.new, ds.reviews), (0, 0))                        # neither new material nor review
        sb.run("placement", "java", "--known", "classes,collections", "--gaps", "streams")
        sb.run("enroll", "java")
        state = sb.state()
        self.assertEqual(state.topic_status("java/classes"), "solid")
        self.assertGreater((state.topics["java/classes"].card.due - sb.clock).days,
                           (state.topics["java/collections"].card.due - sb.clock).days)   # Easy waits longer
        nxt = sb.run("next")
        self.assertIn("NEXT: new", nxt)                                       # the gap is taught, not drilled
        self.assertIn("topic: java/streams", nxt)
        # the item that was missed is not fresh evidence on the day it was seen
        sb.run("covered", "java/streams")
        self.assertIn("answered after seeing the solution today", sb.do("java/streams"))
        self.assertEqual(sb.state().today_numbers(sb.clock)["new_done"], 1)   # now it is today's new topic

    def test_placement_flag_on_a_studied_topic_is_an_ordinary_review(self):
        sb = self.sb
        sb.run("enroll", "java")
        for _ in range(2):
            sb.item("java/classes")
        sb.do("java/classes")
        sb.advance(days=3)
        ident = sb.ask("java/classes")
        self.assertIn("next review in 10m", sb.answer(ident, "A", kind="placement", err="memory"))
        state = sb.state()
        self.assertEqual(state.topics["java/classes"].card.lapses, 1)
        self.assertEqual(state.days[state.day(sb.clock)].reviews, 1)

    def test_whole_skill_placement_unlocks_dependents(self):
        sb = self.sb
        self.assertEqual(sb.state().skill_status("api"), "locked")
        out = sb.run("placement", "java", "--result", "known", "--note", "four years of Java at work")
        self.assertIn("3 topic(s) marked known", out)
        state = sb.state()
        self.assertEqual(state.skill_status("java"), "known")
        self.assertEqual(state.skill_status("api"), "available")
        self.assertEqual(len(state.scheduled_topics()), 3)                    # known skills stay in rotation
        sb.advance(days=20)
        sb.item("java/classes")
        sb.do("java/classes", "A", err="memory")                              # the first real review fails
        self.assertEqual(sb.state().topic_status("java/classes"), "learning")

    def test_project_boss(self):
        sb = self.sb
        self.assertIn("No boss is due", sb.run("boss", "status"))
        status = sb.run("boss", "status", "docker")
        self.assertIn("Containerise a service.", status)
        self.assertIn("- the image builds", status)
        self.assertIn("boss record docker pass|fail", status)
        sb.run("boss", "record", "docker", "pass", expect=2)                  # evidence is required
        sb.run("boss", "record", "docker", "maybe", "--evidence", "x", expect=2)
        self.assertIn("not passed yet", sb.run("boss", "record", "docker", "fail", "--evidence", "health check 500"))
        sb.run("boss", "record", "docker", "pass", "--evidence", "image 180 MB; /health 200; non-root")
        state = sb.state()
        self.assertTrue(state.skills["docker"].boss_ok)
        self.assertEqual(state.skills["docker"].boss_tries, 2)
        self.assertNotEqual(state.skill_status("docker"), "mastered")         # topics still have to be mastered

    def test_milestone(self):
        sb = self.sb
        sb.run("placement", "shell", "--result", "known")
        sb.run("placement", "java", "--result", "known")
        sb.run("placement", "docker", "--result", "known")
        self.assertEqual(sb.state().skill_status("capstone"), "locked")       # api is still missing
        sb.run("placement", "api", "--result", "known")
        self.assertEqual(sb.state().skill_status("capstone"), "available")
        sb.run("enroll", "capstone")
        self.assertIn("capstone", sb.run("boss", "status"))
        self.assertIn("NEXT: boss", sb.run("next"))
        out = sb.run("boss", "record", "capstone", "pass", "--kind", "capstone", "--evidence", "runs in a container")
        self.assertIn("status: mastered", out)

    def test_timed_test_with_exam_marking(self):
        sb = self.sb
        sb.run("enroll", "gate.cs.os")
        need = sb.run("test", "build", "--skills", "gate.cs.os", "--n", "3", "--minutes", "10", expect=4)
        self.assertIn("needs 3 more verified item(s)", need)
        ids = [sb.item("gate.cs.os/" + t, marks=2) for t in ("deadlock", "scheduling", "paging")]
        built = sb.run("test", "build", "--skills", "gate.cs.os", "--n", "3", "--minutes", "10", "--label", "boss")
        test_id = built.split()[1]
        self.assertTrue(test_id.startswith("t-"))
        order = [line.split(". ")[1] for line in built.split("\n") if line.strip()[:2] in ("1.", "2.", "3.")]
        self.assertEqual(sorted(order), sorted(ids))
        sb.run("ask", "--id", order[0], "--test", test_id)
        self.assertIn("1 of 3 answered", sb.answer(order[0], "B"))
        sb.run("ask", "--id", order[1], "--test", test_id)
        self.assertNotIn("KEY", sb.answer(order[1], "A"))                    # no feedback during a test
        sb.run("ask", "--id", "it-aaaaaaaaaa", "--test", test_id, expect=2)
        self.assertIn("not answered", sb.run("test", "show", test_id))
        sb.advance(minutes=6)
        done = sb.run("test", "finish", test_id)
        self.assertIn("score: 1.33 of 6 (22%) with GATE negative marking", done)
        self.assertIn("correct 1 · wrong 1 · skipped 1", done)
        self.assertIn("Solutions for the missed items", done)
        self.assertIn("KEY: B", done)
        sb.run("test", "finish", test_id, expect=2)
        sb.run("test", "finish", "t-nope", expect=2)


class Renames(Case):
    def test_progress_follows_a_renamed_topic(self):
        sb = self.sb
        sb.onboard()
        syllabus = sb.path("learner", "syllabus", "python.md")
        write(syllabus, "---\nskill: python\n---\n\n# Topics\n\n## types | Types\nlevel: 1\n- name them\n")
        sb.run("enroll", "python")
        sb.item("python/types")
        sb.do("python/types")
        write(syllabus, "---\nskill: python\n---\n\n# Topics\n\n## data-types | Data types\nlevel: 1\n- name them\n")
        self.assertEqual(sb.state().topic_status("python/data-types"), "new")
        sb.run("rename", "topic", "python/types", "python/nope", expect=2)
        sb.run("rename", "topic", "python/types", "python/data-types")
        state = sb.state()
        self.assertEqual(state.topic_status("python/data-types"), "learning")
        self.assertEqual(state.topics["python/data-types"].n_vok, 1)


if __name__ == "__main__":
    unittest.main()
