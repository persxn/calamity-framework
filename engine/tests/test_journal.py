"""Date-wise views (WP-28): a day's record, history by period, the monthly journal, the store layout."""
import os
import shutil
import subprocess
import unittest

from tests.helpers import Case, Sandbox, read, write

from cal.store import Repo


def _study(sb):
    """Two learner days of work in March 2026, one in April."""
    sb.onboard()
    sb.legacy_pace()
    sb.run("enroll", "shell")
    sb.run("enroll", "docker", "--force")
    for topic in ("shell/pipes", "shell/perms", "docker/images"):
        sb.item(topic)
        sb.item(topic)
    sb.run("ask", "--topic", "shell/pipes", "--taught", "--parts", "model,example", "--minutes", "15")
    sb.answer(_open(sb), "B")
    sb.do("docker/images")
    sb.run("workout", "30")
    sb.advance(days=1)
    sb.do("shell/perms", answer="A")
    sb.do("shell/pipes")
    sb.at("2026-04-03T10:00:00+05:30")
    sb.do("shell/perms")


def _open(sb):
    return next(i for i, it in sb.state().items.items() if it.open)


class History(Case):
    def setUp(self):
        super().setUp()
        _study(self.sb)

    def test_day_shows_what_was_recorded_that_day(self):
        out = self.sb.run("day", "2026-03-02")
        self.assertIn("recorded: ", out)
        self.assertRegex(out, r"2 answers 100% \(2 new, 0 reviews\)")
        self.assertIn("taught shell/pipes", out)
        self.assertIn("workout 30 min", out)
        self.assertNotIn("recorded:", self.sb.run("day", "2026-03-10"))

    def test_history_by_month_and_by_day(self):
        out = self.sb.run("history", "--by", "month")
        self.assertRegex(out, r"(?m)^2026-03\s+2\s")
        self.assertRegex(out, r"(?m)^2026-04\s+1\s")
        days = self.sb.run("history", "--by", "day", "--from", "2026-03-03", "--to", "2026-03-03")
        self.assertRegex(days, r"(?m)^2026-03-03\s+1\s+\S+\s+2\s+50%")
        self.assertNotIn("2026-03-02", days.split("\n", 1)[1])

    def test_history_for_one_skill_counts_its_answers_only(self):
        out = self.sb.run("history", "--by", "month", "--skill", "docker")
        self.assertRegex(out, r"(?m)^2026-03\s+1\s+1\s+100%\s+1\s")
        self.assertNotIn("2026-04", out)
        self.assertIn("not split by skill", out)
        self.assertIn("nothing recorded", self.sb.run("history", "--track", "cp"))
        self.sb.run("history", "--skill", "nope", expect=2)
        self.sb.run("history", "--from", "2026-04-01", "--to", "2026-03-01", expect=2)


class Journal(Case):
    def test_rebuild_writes_a_month_per_file_from_the_log_alone(self):
        sb = self.sb
        _study(sb)
        out = sb.run("rebuild")
        self.assertIn("journal: 2 month file(s) rewritten", out)
        march = read(sb.path("learner", "journal", "2026-03.md"))
        self.assertIn("# Journal 2026-03", march)
        self.assertIn("- 2 active days", march)
        self.assertRegex(march, r"- 2026-03-02 Mon · .*taught shell/pipes")
        self.assertRegex(march, r"- 2026-03-03 Tue · .*2 answers 50%")
        self.assertIn("skills worked on: Shell", march)
        self.assertIn("journal: up to date", sb.run("rebuild"))

    def test_two_machines_with_the_same_events_write_the_same_journal(self):
        sb = self.sb
        _study(sb)
        other = Sandbox()
        self.addCleanup(other.close)
        other.onboard()   # its own profile and machine id; the events below are the first machine's
        shutil.copyfile(sb.path("learner", "profile.md"), other.path("learner", "profile.md"))
        shutil.rmtree(other.path("learner", "events"), ignore_errors=True)
        shutil.copytree(sb.path("learner", "events"), other.path("learner", "events"))
        other.advance(days=60)                  # a different clock changes nothing either
        sb.run("rebuild")
        other.run("rebuild")
        self.assertNotEqual(Repo(sb.root).machine(), Repo(other.root).machine())
        for month in ("2026-03.md", "2026-04.md"):
            self.assertEqual(read(sb.path("learner", "journal", month)), read(other.path("learner", "journal", month)))

    def test_a_month_with_nothing_left_in_it_loses_its_file(self):
        sb = self.sb
        sb.onboard()
        write(sb.path("learner", "journal", "2025-01.md"), "# Journal 2025-01\n")
        write(sb.path("learner", "journal", "notes.txt"), "mine\n")
        sb.run("workout", "20")
        sb.run("rebuild")
        self.assertFalse(os.path.exists(sb.path("learner", "journal", "2025-01.md")))
        self.assertTrue(os.path.exists(sb.path("learner", "journal", "notes.txt")))
        self.assertTrue(os.path.exists(sb.path("learner", "journal", "2026-03.md")))


class Layout(Case):
    def _old_store(self):
        sb = self.sb
        write(sb.path("learner", "mastery", "linux", "log.md"), "# log\n")
        write(sb.path("learner", "mastery", "linux", "recall.md"), "# recall\n")
        write(sb.path("learner", "mastery", "linux", "book", "README.md"), "# Linux\n")
        write(sb.path("learner", "mastery", "projects", "shell-clone", "brief.md"), "# brief\n")

    def test_migrate_shows_then_moves(self):
        sb = self.sb
        self._old_store()
        self.assertIn("still under learner/mastery/", sb.run("layout", "check"))
        self.assertRegex(sb.run("doctor", expect=None), r"WARN\s+learner store layout\s+4 thing")
        shown = sb.run("layout", "migrate")
        self.assertIn("move  learner/mastery/linux/book -> learner/books/linux", shown)
        self.assertIn("move  learner/mastery/linux/log.md -> learner/coach/linux/log.md", shown)
        self.assertIn("move  learner/mastery/projects/shell-clone -> learner/projects/shell-clone", shown)
        self.assertTrue(os.path.exists(sb.path("learner", "mastery", "linux", "log.md")))   # nothing moved yet
        done = sb.run("layout", "migrate", "--write")
        self.assertIn("4 moved, 0 skipped", done)
        self.assertEqual(read(sb.path("learner", "books", "linux", "README.md")), "# Linux\n")
        self.assertEqual(read(sb.path("learner", "coach", "linux", "recall.md")), "# recall\n")
        self.assertTrue(os.path.exists(sb.path("learner", "projects", "shell-clone", "brief.md")))
        self.assertFalse(os.path.exists(sb.path("learner", "mastery")))
        self.assertEqual(sb.run("layout", "check"), "current layout\n")

    def test_an_existing_target_is_never_overwritten(self):
        sb = self.sb
        self._old_store()
        write(sb.path("learner", "coach", "linux", "log.md"), "# newer log\n")
        out = sb.run("layout", "migrate", "--write")
        self.assertIn("skip  learner/mastery/linux/log.md -> learner/coach/linux/log.md", out)
        self.assertIn("3 moved, 1 skipped", out)
        self.assertEqual(read(sb.path("learner", "coach", "linux", "log.md")), "# newer log\n")
        self.assertEqual(read(sb.path("learner", "mastery", "linux", "log.md")), "# log\n")

    @unittest.skipUnless(shutil.which("git"), "git is not installed")
    def test_tracked_files_move_with_git(self):
        sb = self.sb
        self._old_store()
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@e", GIT_COMMITTER_NAME="t",
                   GIT_COMMITTER_EMAIL="t@e")

        def git(*args):
            return subprocess.run(["git"] + list(args), cwd=sb.root, env=env, check=True,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.decode()

        git("init", "-q")
        git("add", "learner/mastery/linux/log.md", "learner/mastery/linux/book/README.md")
        git("commit", "-q", "-m", "old layout")
        sb.run("layout", "migrate", "--write")
        status = git("status", "--short")
        self.assertRegex(status, r"R\s+learner/mastery/linux/log.md -> learner/coach/linux/log.md")
        self.assertRegex(status, r"R\s+learner/mastery/linux/book/README.md -> learner/books/linux/README.md")
        self.assertTrue(os.path.exists(sb.path("learner", "coach", "linux", "recall.md")))   # untracked, moved too


if __name__ == "__main__":
    unittest.main()
