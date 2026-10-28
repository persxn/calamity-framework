"""The learner model and n-of-1 experiments (WP-20): numbers from synthetic logs, refusals below n."""
from datetime import timedelta

from tests.helpers import Case

from cal import model

TOPICS = ["docker/images", "docker/dockerfile", "docker/multi-stage", "java/classes", "java/collections",
          "java/streams"]


class Model(Case):
    def setUp(self):
        super().setUp()
        sb = self.sb
        sb.onboard()
        sb.legacy_pace()
        for skill in ("docker", "java"):
            sb.run("enroll", skill, "--force")
        for topic in TOPICS:
            sb.item(topic)
            sb.item(topic)

    def first_tries(self, pattern, parts="model,example"):
        """Teach each topic and answer its first question right (1) or wrong (0)."""
        sb = self.sb
        for topic, right in zip(TOPICS, pattern):
            out = sb.run("ask", "--topic", topic, "--taught", "--parts", parts)
            item = out.split("ITEM ", 1)[1].split()[0]
            sb.answer(item, "B" if right else "A", seconds=40)
            sb.advance(minutes=2)

    def test_first_try_accuracy_reproduces_on_a_synthetic_log(self):
        self.first_tries([1, 1, 0, 1, 1, 0])
        out = self.sb.run("model")
        self.assertRegex(out, r"(?m)^dev\s+6\s+67% \(6\)")          # 4 of 6 new topics right first time
        self.assertIn("example+model", out)
        self.assertRegex(out, r"by the part taught first: model 67% \(6\)")
        self.assertRegex(out, r"(?m)^docker\s+3\s+67% \(3\)|^docker\s+3\s+- \(3\)")

    def test_retention_counts_reviews_a_week_or_more_apart(self):
        sb = self.sb
        self.first_tries([1] * 6)
        sb.advance(days=8)
        for topic in TOPICS[:5]:
            sb.do(topic, answer="B" if topic != TOPICS[0] else "A")
        rows = model.attempts(sb.state().repo, sb.tree(), sb.state())
        g = model.group_stats(rows)
        self.assertEqual(g["first"], (6, 6))
        self.assertEqual(g["r7"], (4, 5))
        self.assertEqual(g["r30"], (0, 0))

    def test_rates_below_five_answers_are_not_shown(self):
        self.first_tries([1, 0])
        self.assertRegex(self.sb.run("model"), r"(?m)^dev\s+\d+\s+- \(2\)")

    def test_session_minute_curve_and_recommended_length(self):
        curve = [(0, 30, 18, 20), (30, 60, 17, 20), (60, 90, 12, 20), (90, 10 ** 6, 5, 10)]
        self.assertEqual(model.recommended_length(curve), 60)
        self.assertIsNone(model.recommended_length([(0, 30, 5, 8)] + curve[1:]))


class Experiments(Case):
    def setUp(self):
        super().setUp()
        sb = self.sb
        sb.onboard()
        sb.legacy_pace()
        sb.run("enroll", "docker", "--force")
        sb.run("enroll", "java", "--force")
        for topic in TOPICS:
            sb.item(topic)

    def test_arms_alternate_and_no_conclusion_below_n(self):
        sb = self.sb
        out = sb.run("experiment", "start", "ex-01", "--skill", "java", "--arms", "theory-first,example-first",
                     "--n", "4", "--desc", "worked example first?")
        self.assertIn("alternate theory-first / example-first", out)
        self.assertIn("experiment ex-01: teach this topic theory-first (topic 1 of 4", sb.run("next", "--skill", "java"))
        for topic, right in (("java/classes", "B"), ("java/collections", "A"), ("java/streams", "B")):
            item = sb.run("ask", "--topic", topic, "--taught").split("ITEM ", 1)[1].split()[0]
            sb.answer(item, right)
        state = sb.state()
        self.assertEqual([arm for _, arm in state.experiments["ex-01"]["assigned"]],
                         ["theory-first", "example-first", "theory-first"])
        status = sb.run("experiment", "status", "ex-01")
        self.assertIn("no conclusion yet: 3 of 4 topics measured", status)
        self.assertNotIn("P(", status)
        sb.env["CALAMITY_NO_CACHE"] = "1"                            # the same arms from a full replay
        self.assertEqual(sb.state().experiments, state.experiments)

    def test_starting_is_checked(self):
        sb = self.sb
        sb.run("experiment", "start", "ex-02", "--skill", "java", "--arms", "a", "--n", "4", expect=2)
        sb.run("experiment", "start", "ex-02", "--skill", "java", "--arms", "a,b", "--n", "3", expect=2)
        sb.run("experiment", "start", "ex-02", "--skill", "java", "--arms", "a,b", "--n", "4")
        sb.run("experiment", "start", "ex-03", "--skill", "java", "--arms", "a,b", "--n", "4", expect=2)
        sb.run("experiment", "start", "ex-02", "--skill", "docker", "--arms", "a,b", "--n", "4", expect=2)
        self.assertIn("stopped", sb.run("experiment", "stop", "ex-02"))
        self.assertNotIn("experiment ex-02", sb.run("next", "--skill", "java"))

    def test_the_probability(self):
        self.assertAlmostEqual(model.prob_b_beats_a(3, 3, 3, 3), 0.5, places=6)
        self.assertGreater(model.prob_b_beats_a(0, 6, 6, 0), 0.99)
        self.assertLess(model.prob_b_beats_a(6, 0, 0, 6), 0.01)
        self.assertGreater(model.prob_b_beats_a(2, 4, 5, 1), 0.9)
