"""Item families and nightly stocking (WP-11): the work list for the next days, and its scheduler entry."""
import os

from tests.helpers import Case, read, write

SYLLABUS = """---
skill: shell
written: 2026-03-01
sources: [https://www.gnu.org/software/bash/manual/]
---

# Topics

## pipes | Pipes
level: 1
- [T] explain what a pipe hands from one process to the next
- [P] chain three commands to filter a log file
- [I] build a two-process pipe in C

## perms | Permissions
needs: [pipes]
level: 2
- read and change file modes
- explain why a directory needs x to be entered
"""


class Families(Case):
    def setUp(self):
        super().setUp()
        self.sb.onboard()
        write(self.sb.path("learner", "syllabus", "shell.md"), SYLLABUS)
        self.sb.run("enroll", "shell")

    def test_one_item_stocks_today_but_not_a_family(self):
        sb = self.sb
        sb.item("shell/pipes", objectives=[1])
        self.assertNotIn("shell/pipes", sb.run("item", "needs"))
        out = sb.run("item", "needs", "--per-topic", "3")
        self.assertIn("  shell/pipes (new, 2 more; objectives untested: 2, 3)", out)
        self.assertIn("item needs --full --per-topic 3", out)

    def test_drafts_waiting_are_counted_and_said(self):
        sb = self.sb
        sb.item("shell/pipes", objectives=[1])
        sb.draft("shell/pipes", objectives=[2])
        out = sb.run("item", "needs", "--per-topic", "3")
        self.assertIn("shell/pipes (new, 1 more, 1 draft waiting for the checker; objectives untested: 3)", out)
        full = sb.run("item", "needs", "--full", "--per-topic", "3")
        self.assertIn("family: write 1 more, 1 draft waiting for the checker; objectives untested: 3, across", full)
        self.assertIn("Write each topic's family", full)

    def test_days_ahead_reach_what_the_quota_would_open(self):
        sb = self.sb
        sb.legacy_pace()
        sb.run("profile", "set", "cfg.new_per_day_max", "1")
        for topic in ("shell/pipes", "shell/perms"):
            sb.item(topic)
        sb.do("shell/pipes")
        self.assertIn("ITEMS: stocked", sb.run("item", "needs", "--n", "1"))
        ahead = sb.run("item", "needs", "--days", "3", "--per-topic", "2")
        self.assertIn("over the next 3 day(s)", ahead)
        self.assertIn("shell/perms (new, 1 more", ahead)
        self.assertIn("shell/pipes (review", ahead)          # due again within three days, its item seen

    def test_a_full_bank_says_stocked(self):
        sb = self.sb
        for n in (1, 2, 3):
            sb.item("shell/pipes", objectives=[n])
        out = sb.run("item", "needs", "--per-topic", "3", "--skill", "shell")
        self.assertNotIn("shell/pipes", out)


class Nightly(Case):
    def setUp(self):
        super().setUp()
        self.sb.onboard()

    def test_render_writes_a_cron_entry_that_runs_only_when_work_is_listed(self):
        sb = self.sb
        out = sb.run("stock", "render", "--at", "23:45", "--os", "linux")
        self.assertIn("Stocking files written for Linux (23:45)", out)
        self.assertIn("crontab -", out)
        self.assertIn("It uses your plan's usage", out)
        folder = sb.path(".calamity", "stock")
        script = read(os.path.join(folder, "stock.sh"))
        self.assertIn("item needs --days 2 --per-topic 3", script)
        self.assertIn('"ITEMS NEEDED"*) ;;', script)                    # anything else: no Claude run
        self.assertIn("'-p' '/stock' '--permission-mode' 'dontAsk'", script)
        self.assertRegex(script, r"Bash\((python3|python|py -3) engine/calamity\.py \*\)")
        self.assertNotIn("Bash(*)", script)
        self.assertIn(".calamity/logs", script)
        cron = read(os.path.join(folder, "crontab.txt"))
        self.assertRegex(cron, r"^45 23 \* \* \* /bin/sh .*stock\.sh' # calamity-stock-[0-9a-f]{8}\n$")
        self.assertIn("calamity-stock-", sb.run("stock", "remove", "--os", "linux"))

    def test_the_time_comes_from_the_profile_or_is_asked_for(self):
        sb = self.sb
        sb.run("stock", "render", "--os", "linux", expect=2)
        self.assertIn("give the time", sb.err)
        sb.run("profile", "set", "stock.at", "nope", expect=2)
        sb.run("profile", "set", "stock.at", "00:30")
        self.assertIn("(00:30)", sb.run("stock", "render", "--os", "darwin"))
        plist = [f for f in os.listdir(sb.path(".calamity", "stock")) if f.endswith(".plist")]
        self.assertEqual(len(plist), 1)
        self.assertIn("<integer>30</integer>", read(sb.path(".calamity", "stock", plist[0])))

    def test_windows_files(self):
        sb = self.sb
        out = sb.run("stock", "render", "--at", "23:45", "--os", "windows")
        self.assertIn("install.cmd", out)
        ps = read(sb.path(".calamity", "stock", "stock.ps1"))
        self.assertIn("StartsWith('ITEMS NEEDED')", ps)
        self.assertIn("'dontAsk'", ps)
        self.assertIn("Calamity Stock ", read(sb.path(".calamity", "stock", "install.ps1")))

    def test_the_skill_is_never_invoked_by_the_model(self):
        from tests.helpers import REPO

        skill = read(os.path.join(REPO, ".claude", "skills", "stock", "SKILL.md"))
        self.assertIn("disable-model-invocation: true", skill)
        self.assertIn("item needs --days 2 --per-topic 3", skill)
