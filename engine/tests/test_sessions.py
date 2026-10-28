"""The developer track's session types (WP-23): recorded, counted, in the day's record; never evidence."""
from tests.helpers import Case


class Sessions(Case):
    mini = False

    def setUp(self):
        super().setUp()
        self.sb.onboard(tracks="10x")

    def test_a_session_is_recorded_and_shows_in_the_day_and_the_counts(self):
        sb = self.sb
        out = sb.run("practice", "session", "outage", "--minutes", "45", "--topic", "eng-vocab/reliability",
                     "--note", "a config push that took a region down")
        self.assertIn("outage session recorded on eng-vocab/reliability, 45 min", out)
        self.assertIn("notes fragment eng-vocab/reliability", out)
        self.assertIn("session outage 45 min", sb.run("day"))
        counts = sb.run("practice", "sessions")
        self.assertIn("outage     1 session, 45 min", counts)
        self.assertIn("not yet: system-day, classic, oss, vocab", counts)
        self.assertIsNone(sb.state().topics.get("eng-vocab/reliability"))   # nothing scheduled or credited

    def test_a_classic_asks_for_three_ideas_and_bad_input_is_refused(self):
        sb = self.sb
        self.assertIn("at least three new ideas", sb.run("practice", "session", "classic", "--ideas", "2"))
        self.assertNotIn("three new ideas", sb.run("practice", "session", "classic", "--ideas", "3"))
        sb.run("practice", "session", "hackathon", expect=2)
        sb.run("practice", "session", "vocab", "--topic", "eng-vocab/nope", expect=2)
        sb.run("practice", "session", "vocab", "--note", "x" * 201, expect=2)

    def test_the_journal_counts_sessions(self):
        sb = self.sb
        sb.run("practice", "session", "vocab", "--minutes", "20", "--topic", "eng-vocab/distributed")
        sb.run("practice", "session", "vocab", "--minutes", "15")
        sb.run("rebuild")
        from tests.helpers import read

        month = read(sb.path("learner", "journal", "2026-03.md"))
        self.assertIn("- developer sessions: vocab 2", month)
