import json
import os
import plistlib
import shutil
import subprocess
import sys
import unittest

from tests.helpers import ENGINE, Case, write

from cal import machine, remind
from cal.store import Repo

SHIM = """import os, sys
sys.path.insert(0, %r)
os.environ.setdefault("CALAMITY_ROOT", %r)
from cal.cli import main
sys.exit(main())
"""


class Setup(Case):
    def shim(self):
        """Give the sandbox its own engine/calamity.py so hook and reminder paths point at something real."""
        write(self.sb.path("engine", "calamity.py"), SHIM % (ENGINE, self.sb.root))

    def settings(self):
        with open(self.sb.path(".claude", "settings.local.json"), "r", encoding="utf-8") as fh:
            return json.load(fh)

    def test_setup_creates_machine_and_folders(self):
        sb = self.sb
        out = sb.run("setup", "--machine", "Study Laptop")
        self.assertIn("machine: study-laptop", out)
        self.assertIn("engine command on this machine:", out)
        self.assertIn("session-start hook: missing (install with: setup --hook)", out)
        with open(sb.path(".calamity", "machine.json"), "r", encoding="utf-8") as fh:
            machine = json.load(fh)
        self.assertEqual(machine["id"], "study-laptop")
        self.assertIn("engine/calamity.py", machine["cmd"])
        for folder in ("events", "items", "syllabus", "tree", "sources", "notes", "work", os.path.join("cp", "solutions")):
            self.assertTrue(os.path.isdir(sb.path("learner", folder)), folder)
        self.assertFalse(os.path.exists(sb.path(".claude", "settings.local.json")))   # nothing installed unasked
        self.assertIn("engine: " + machine["cmd"], sb.run("brief"))
        self.assertIn("machine: study-laptop", sb.run("setup"))                        # the name is kept

    def test_hook_is_installed_in_exec_form_and_merged(self):
        sb = self.sb
        self.shim()
        existing = {"permissions": {"allow": ["Bash(ls *)"]},
                    "hooks": {"SessionStart": [{"hooks": [{"type": "command", "command": "echo other"}]}],
                              "Stop": [{"hooks": [{"type": "command", "command": "echo bye"}]}]}}
        write(sb.path(".claude", "settings.local.json"), json.dumps(existing))
        out = sb.run("setup", "--hook")
        self.assertIn("session-start hook written to .claude/settings.local.json", out)
        data = self.settings()
        self.assertEqual(data["permissions"], existing["permissions"])
        self.assertEqual(data["hooks"]["Stop"][0], existing["hooks"]["Stop"][0])    # the learner's own hook stays first
        self.assertEqual(data["hooks"]["Stop"][1]["hooks"][0]["args"][1:], ["guard", "stop"])
        for event, args in (("UserPromptSubmit", ["guard", "prompt"]), ("PreCompact", ["snapshot", "--session"]),
                            ("SessionEnd", ["guard", "end"])):
            self.assertEqual(data["hooks"][event][0]["hooks"][0]["args"][1:], args, event)
        entries = data["hooks"]["SessionStart"]
        self.assertEqual(len(entries), 2)
        ours = entries[-1]["hooks"][0]
        self.assertEqual(ours["type"], "command")
        self.assertEqual(ours["command"], sys.executable)             # a real executable, no shell involved
        self.assertEqual(ours["args"], [sb.path("engine", "calamity.py"), "brief", "--hook"])
        self.assertTrue(os.path.isabs(ours["args"][0]))
        self.assertEqual(ours["timeout"], 30)
        guard = data["hooks"]["PreToolUse"]                          # the key guard comes with it
        self.assertEqual(len(guard), 1)
        self.assertEqual(guard[0]["matcher"], "Read|Grep|Glob|Bash|PowerShell")
        self.assertEqual(guard[0]["hooks"][0]["command"], sys.executable)
        self.assertEqual(guard[0]["hooks"][0]["args"], [sb.path("engine", "calamity.py"), "guard", "tool"])
        sb.run("setup", "--hook")                                     # installing again does not duplicate it
        self.assertEqual(len(self.settings()["hooks"]["SessionStart"]), 2)
        self.assertEqual(len(self.settings()["hooks"]["PreToolUse"]), 1)
        self.assertEqual(len(self.settings()["hooks"]["Stop"]), 2)
        self.assertEqual(self.settings()["outputStyle"], "Calamity Tutor")   # how a study session teaches
        out = sb.run("setup")
        self.assertIn("session-start hook: ok", out)
        self.assertIn("key guard: ok", out)
        self.assertRegex(sb.run("doctor", expect=None), r"OK +key guard")

        # the hook as Claude Code would run it: the executable with its arguments, JSON on stdin
        sb.onboard()
        proc = subprocess.run([ours["command"]] + ours["args"], input=json.dumps({"source": "startup"}).encode("utf-8"),
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=sb.root, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stderr.decode("utf-8", "replace"))
        text = proc.stdout.decode("utf-8")
        self.assertTrue(text.startswith("=== CALAMITY BRIEF ==="))
        self.assertLess(len(text), 10000)

        self.assertIn("session-start hook removed", sb.run("setup", "--remove-hook"))
        data = self.settings()
        self.assertEqual(data["hooks"]["SessionStart"], existing["hooks"]["SessionStart"])
        self.assertNotIn("PreToolUse", data["hooks"])
        self.assertNotIn("outputStyle", data)
        self.assertIn("no Calamity hook was installed", sb.run("setup", "--remove-hook"))
        self.assertRegex(sb.run("doctor", expect=None), r"WARN +key guard +missing")

    def test_a_style_the_learner_chose_is_kept(self):
        sb = self.sb
        write(sb.path(".claude", "settings.local.json"), json.dumps({"outputStyle": "Explanatory"}))
        self.assertIn("your own output style (Explanatory) kept", sb.run("setup", "--hook"))
        self.assertEqual(self.settings()["outputStyle"], "Explanatory")
        sb.run("setup", "--remove-hook")
        self.assertEqual(self.settings()["outputStyle"], "Explanatory")      # not ours to remove
        write(sb.path(".claude", "output-styles", "calamity-tutor.md"), "---\nname: Calamity Tutor\n---\n")
        self.assertIn("Explanatory, chosen here", sb.run("doctor", expect=None))

    def test_hook_state_detects_a_moved_repository(self):
        sb = self.sb
        sb.run("setup", "--hook")                                      # no engine/ in this sandbox
        self.assertIn("no longer exists", sb.run("setup"))
        self.shim()
        self.assertIn("session-start hook: ok", sb.run("setup"))
        write(sb.path(".claude", "settings.local.json"), "{not json")
        sb.run("setup", "--hook", expect=2)                            # never overwrite a file it cannot read
        self.assertIn("not valid JSON", sb.run("setup"))

    def test_statusline(self):
        sb = self.sb
        self.shim()
        out = sb.run("setup", "--statusline")
        if "NOT written" in out:                    # Windows, a path with spaces and no short name
            self.assertIn("contains spaces", out)  # refused rather than written wrongly, after the rest
            return
        command = self.settings()["statusLine"]
        self.assertEqual(command["type"], "command")
        self.assertIn("statusline", command["command"])
        self.assertIn("CAL · not onboarded", sb.run("statusline"))
        sb.onboard()
        self.assertIn("CAL · due 0 · new 0/0", sb.run("statusline"))

    def test_statusline_answer_is_kept_until_something_changes(self):
        sb = self.sb
        sb.onboard()
        sb.run("enroll", "shell")
        first = sb.run("statusline")
        self.assertIn("new 0/2", first)
        kept = sb.path(".calamity", "cache", "statusline.json")
        with open(kept, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertEqual(data["text"], first.strip())
        data["text"] = "CAL · kept"
        write(kept, json.dumps(data))
        self.assertIn("CAL · kept", sb.run("statusline"))               # nothing changed: no replay
        sb.advance(minutes=1)
        self.assertIn("new 0/2", sb.run("statusline"))                  # a new minute: worked out again
        sb.item("shell/pipes")
        sb.do("shell/pipes")
        self.assertIn("new 1/2", sb.run("statusline"))                  # an answer: worked out again
        sb.run("profile", "set", "cfg.new_per_day", "1")
        self.assertIn("new 1/1", sb.run("statusline"))                  # a setting: worked out again
        write(kept, "{broken")
        self.assertIn("new 1/1", sb.run("statusline"))                  # a damaged file is ignored

    @unittest.skipIf(sys.platform.startswith("win"), "the alias is for bash and zsh")
    def test_alias(self):
        sb = self.sb
        home = sb.path("home")
        sb.env.update({"HOME": home, "SHELL": "/bin/zsh", "ZDOTDIR": ""})
        dotfiles = sb.path("dotfiles", "zshrc")                        # a dotfile manager's symbolic link
        write(dotfiles, "export EDITOR=vim")
        os.chmod(dotfiles, 0o640)
        os.makedirs(home)
        os.symlink(dotfiles, os.path.join(home, ".zshrc"))
        self.assertIn("not installed (optional: setup --alias)", sb.run("doctor", expect=None))
        self.assertIn("alias written to ~/.zshrc", sb.run("setup", "--alias"))
        sb.run("setup", "--alias")                                     # installing again does not duplicate it
        self.assertTrue(os.path.islink(os.path.join(home, ".zshrc")))
        self.assertEqual(os.stat(dotfiles).st_mode & 0o777, 0o640)
        with open(dotfiles, "r", encoding="utf-8") as fh:
            text = fh.read()
        self.assertTrue(text.startswith("export EDITOR=vim\n# >>> calamity alias >>>\nalias calamity="))
        self.assertEqual(text.count("alias calamity="), 1)
        self.assertIn("claude --dangerously-skip-permissions", text)
        self.assertRegex(sb.run("doctor", expect=None), r"OK +shell alias +installed \(~/\.zshrc\)")

        moved = text.replace(sb.root, sb.root + "-old")                # the folder was moved or copied
        write(dotfiles, moved)
        self.assertIn("points at a different copy", sb.run("doctor", expect=None))
        sb.run("setup", "--alias")
        with open(dotfiles, "r", encoding="utf-8") as fh:
            self.assertEqual(fh.read(), text)

        self.assertIn("alias removed from ~/.zshrc", sb.run("setup", "--remove-alias"))
        with open(dotfiles, "r", encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "export EDITOR=vim\n")
        self.assertIn("no Calamity alias was installed", sb.run("setup", "--remove-alias"))

        sb.env["SHELL"] = "/usr/bin/fish"
        self.assertIn("alias NOT written: the alias is written for bash and zsh", sb.run("setup", "--alias"))
        self.assertIn("not available for this shell", sb.run("doctor", expect=None))

    # Windows runners carry WSL's bash.exe launcher, which exists but runs no Linux; the alias is never written there.
    @unittest.skipIf(os.name == "nt" or not shutil.which("bash"), "the alias is written for Linux and macOS")
    def test_alias_changes_folder_and_starts_claude(self):
        class Odd:
            root = os.path.join(self.sb.root, "it's a folder with spaces")
        os.makedirs(Odd.root)
        script = "shopt -s expand_aliases\nclaude() { printf '%%s|%%s' \"$PWD\" \"$*\"; }\n%s\ncalamity\n" \
                 % machine.alias_line(Odd)
        proc = subprocess.run(["bash", "-c", script], stdout=subprocess.PIPE, cwd=self.sb.root, timeout=30)
        self.assertEqual(proc.stdout.decode("utf-8"), "%s|--dangerously-skip-permissions" % Odd.root)

    def test_doctor(self):
        sb = self.sb
        out = sb.run("doctor")
        self.assertIn("OK    Python", out)
        self.assertIn("skill tree: 14 skills, 21 topics", out)
        self.assertTrue(all(line == line.rstrip() for line in out.split("\n")))
        self.assertIn("WARN  learner profile", out)
        self.assertIn("WARN  session-start hook", out)
        self.assertIn("0 problem(s)", out)
        write(sb.path(".gitattributes"), "learner/events/*.jsonl merge=union\n")
        write(sb.path(".gitignore"), ".calamity/\n")
        sb.onboard()
        out = sb.run("doctor")
        self.assertIn("OK    .gitattributes union merge", out)
        self.assertIn("OK    .gitignore covers .calamity/", out)
        self.assertIn("OK    learner profile", out)
        write(sb.path("framework", "tree", "dev", "bad.md"), "---\nid: bad\nprereqs: [ghost]\n---\n")
        out = sb.run("doctor", expect=1)
        self.assertIn("FAIL  skill tree", out)
        self.assertIn("1 problem(s)", out)

    def test_version_and_help(self):
        sb = self.sb
        self.assertRegex(sb.run("version"), r"Calamity framework \S+ · state schema 1 · Python 3\.\d+")
        self.assertIn("usage: calamity", sb.run())
        sb.run("no-such-command", expect=2)


class Reminders(Case):
    def setUp(self):
        super().setUp()
        sb = self.sb
        sb.onboard()
        sb.run("enroll", "shell")
        write(sb.path("engine", "calamity.py"), SHIM % (ENGINE, sb.root))

    def test_check(self):
        sb = self.sb
        self.assertIn("Calamity: 2 new topics left today", sb.run("remind", "check"))
        sb.run("profile", "set", "cfg.new_per_day", "0")
        self.assertEqual(sb.run("remind", "check", expect=3), "")      # nothing due: stay quiet
        self.assertIn("nothing due right now", sb.run("remind", "check", "--always"))
        sb.run("profile", "unset", "onboarded")                         # a reminder before onboarding says so
        self.assertEqual(sb.run("remind", "check", expect=3), "")
        self.assertIn("not set up yet", sb.run("remind", "check", "--always"))

    def test_render_needs_times(self):
        sb = self.sb
        sb.run("remind", "render", expect=2)
        sb.run("remind", "render", "--times", "9am", expect=2)
        sb.run("profile", "set", "reminders.times", "21:00,09:00")
        self.assertIn("09:00, 21:00", sb.run("remind", "render", "--os", "linux"))

    def test_linux(self):
        sb = self.sb
        out = sb.run("remind", "render", "--times", "09:00,20:30", "--os", "linux")
        self.assertIn("crontab -", out)
        self.assertIn("remove:", out)
        folder = sb.path(".calamity", "reminders")
        with open(os.path.join(folder, "crontab.txt"), "r", encoding="utf-8") as fh:
            cron = fh.read().strip().split("\n")
        self.assertEqual(len(cron), 2)
        self.assertTrue(cron[0].startswith("0 9 * * * /bin/sh '"))
        self.assertTrue(cron[1].startswith("30 20 * * * /bin/sh '"))
        tag = remind.clone_tag(Repo(sb.root))
        self.assertTrue(all(line.endswith("# calamity-remind-%s" % tag) for line in cron))   # this clone only
        script = os.path.join(folder, "notify.sh")
        with open(script, "r", encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("remind check", text)
        self.assertNotIn("%(", text)
        sh, tr = shutil.which("sh"), shutil.which("tr")
        if sh and tr and os.name == "posix":
            self.assertEqual(subprocess.run([sh, "-n", script]).returncode, 0)        # it parses
            # Run it with a PATH that holds `tr` and nothing else: whatever this machine has installed,
            # the script then finds no notify-send and no osascript, and prints the message instead.
            bin_dir = sb.path("bin")
            os.makedirs(bin_dir)
            os.symlink(tr, os.path.join(bin_dir, "tr"))
            env = {k: v for k, v in os.environ.items() if not k.startswith("CALAMITY_")}
            env["PATH"] = bin_dir
            proc = subprocess.run([sh, script], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, timeout=60)
            self.assertEqual(proc.returncode, 0, proc.stderr.decode("utf-8", "replace"))
            self.assertIn("Calamity:", proc.stdout.decode("utf-8"))

    def test_macos(self):
        sb = self.sb
        out = sb.run("remind", "render", "--times", "07:15", "--os", "darwin")
        self.assertIn("launchctl load", out)
        label = "com.calamity.remind.%s" % remind.clone_tag(Repo(sb.root))
        with open(sb.path(".calamity", "reminders", label + ".plist"), "rb") as fh:
            plist = plistlib.load(fh)
        self.assertEqual(plist["Label"], label)
        self.assertEqual(plist["StartCalendarInterval"], [{"Hour": 7, "Minute": 15}])
        self.assertEqual(plist["ProgramArguments"][0], "/bin/sh")
        self.assertTrue(plist["ProgramArguments"][1].endswith("notify.sh"))

    def test_windows(self):
        sb = self.sb
        out = sb.run("remind", "render", "--times", "09:00,21:45", "--os", "windows")
        self.assertIn("install.cmd", out)
        folder = sb.path(".calamity", "reminders")
        with open(os.path.join(folder, "install.cmd"), "rb") as fh:
            self.assertIn(b"\r\n", fh.read())
        with open(os.path.join(folder, "install.ps1"), "r", encoding="utf-8-sig") as fh:
            install = fh.read()
        self.assertEqual(install.count("'09:00'") + install.count("'21:45'"), 2)
        self.assertIn("Register-ScheduledTask", install)
        prefix = "Calamity Remind %s" % remind.clone_tag(Repo(sb.root))
        self.assertIn("$prefix = '%s'" % prefix, install)
        self.assertIn("notify.ps1", install)
        # installing again with other times must not leave the old tasks behind: both scripts first
        # remove this clone's tasks, whatever times were installed before, and nobody else's
        clear = 'Where-Object { $_.TaskName -like "$prefix *" } | Unregister-ScheduledTask'
        self.assertLess(install.index(clear), install.index("Register-ScheduledTask "))
        with open(os.path.join(folder, "remove.ps1"), "r", encoding="utf-8-sig") as fh:
            remove = fh.read()
        self.assertIn(clear, remove)
        self.assertNotIn("Register-ScheduledTask ", remove)
        with open(os.path.join(folder, "notify.ps1"), "r", encoding="utf-8-sig") as fh:
            ps1 = fh.read()
        self.assertIn("remind check", ps1)
        self.assertIn(sys.executable.replace('"', ""), ps1)


class Views(Case):
    def setUp(self):
        super().setUp()
        sb = self.sb
        sb.onboard(tracks="dev")
        sb.run("enroll", "shell")
        sb.run("enroll", "java", "--mode", "brushup")
        for topic in ("shell/pipes", "shell/perms", "java/classes"):
            sb.item(topic)
            sb.do(topic)
        sb.advance(days=4)

    def test_dashboards(self):
        sb = self.sb
        progress = sb.run("dash")
        self.assertIn("CALAMITY · Tester", progress)
        self.assertIn("reviews", progress)
        self.assertIn("Developer", progress)
        self.assertIn("shell", progress)
        self.assertIn("0/2 solid", progress)
        self.assertIn("brush-up", progress)
        self.assertIn("due", progress)
        ascii_out = sb.run("dash", "progress", "--ascii")
        ascii_out.encode("ascii")                                        # --ascii really is ASCII
        roadmap = sb.run("dash", "roadmap", "--ascii", "--width", "50")
        roadmap.encode("ascii")
        self.assertIn("Developer\n  [6 skills: 2 learning, 1 open, 3 locked]", roadmap)   # too wide for one line
        self.assertTrue(all(len(line) <= 50 for line in roadmap.split("\n")), roadmap)
        self.assertIn("Developer  [6 skills: 2 learning, 1 open, 3 locked]", sb.run("dash", "roadmap", "--width", "78"))
        self.assertNotIn("GATE", roadmap)                                # only the learner's tracks ...
        self.assertIn("GATE CS", sb.run("dash", "roadmap", "--all-tracks"))   # ... unless asked
        self.assertIn("Competitive programming", sb.run("dash", "roadmap", "--track", "cp"))
        queue = sb.run("dash", "queue")
        self.assertIn("REVISION QUEUE · 3 due now", queue)
        self.assertIn("coming up", queue)
        self.assertIn("in rotation: 3 topics across 2 skill(s)", queue)
        # a topic key is what gets typed, so it is never cut short: the title gives way first,
        # and on a very narrow screen each topic takes two lines
        self.assertRegex(queue, r"(?m)^topic +title +recall +due +status$")
        self.assertRegex(queue, r"(?m)^shell/pipes +Pipes")
        narrow = sb.run("dash", "queue", "--width", "40")
        self.assertRegex(narrow, r"(?m)^topic +recall +due +status$")
        self.assertRegex(narrow, r"(?m)^java/classes +\d+%")
        self.assertTrue(all(len(line) <= 40 for line in narrow.split("\n")), narrow)
        from cal import dash
        rows = [["a.very.long.skill.id/and-a-long-topic-id", "81%", "2d ago", "learning"]]
        self.assertEqual(dash._queue_rows(rows, ["Title"], 40),
                         ["a.very.long.skill.id/and-a-long-topic-id", "    recall 81% · due 2d ago · learning"])
        self.assertIn("Title", dash._queue_rows(rows, ["Title"], 100)[2])
        week = sb.run("dash", "week")
        self.assertIn("accuracy by part of day", week)
        self.assertIn("accounted", week)
        everything = sb.run("dash", "all", "--width", "70")
        self.assertIn("REVISION QUEUE", everything)
        self.assertIn("No GATE papers set", sb.run("dash", "gate"))
        self.assertIn("No Codeforces handle linked", sb.run("dash", "cp"))

    def test_stats_and_observations(self):
        sb = self.sb
        self.assertIn("morning", sb.run("stats", "hours"))
        self.assertIn("No failed answers recorded", sb.run("stats", "errors"))
        self.assertTrue(sb.run("stats").strip())
        self.assertIn("No observations recorded", sb.run("observations"))
        sb.run("observe", "prefers worked examples before theory", "--skill", "shell")
        sb.run("observe", "x", expect=2)
        sb.run("observe", "about a ghost", "--topic", "ghost/topic", expect=2)
        out = sb.run("observations")
        self.assertIn("[teaching shell] prefers worked examples before theory", out)
        self.assertIn("No observations recorded", sb.run("observations", "--tag", "coach"))
        sb.run("workout", "0", expect=2)
        sb.run("workout", "45", "--note", "gym")
        self.assertIn("45m", sb.run("stats", "week"))


class CoachPatterns(Case):
    def test_patterns_need_history_then_raise_one_at_a_time(self):
        sb = self.sb
        sb.onboard(sleep__start="23:30", sleep__end="07:00", workout__minutes="60")
        sb.run("enroll", "shell")
        sb.item("shell/pipes")
        self.assertIn("Not enough history yet", sb.run("stats", "patterns"))
        # a week with four nights of study after midnight, two days of nothing, never a workout
        for day, hour in ((3, 21), (4, 0), (5, 1), (6, 1), (7, 1), (9, 20)):
            stamp = "2026-03-%02dT%02d:10:00+05:30" % (day, hour)
            sb.at(stamp)
            sb.do("shell/pipes")
        sb.at("2026-03-09T20:30:00+05:30")
        text = sb.run("stats", "patterns")
        self.assertIn("late-night: studied inside the sleep window (23:30-07:00) on 4 of the last 7 days", text)
        self.assertIn("zero-days", text)
        self.assertIn("no-workout", text)
        self.assertEqual(text.count("[RAISE NOW]"), 1)
        self.assertIn("[RAISE NOW] late-night", text)
        self.assertIn("Behaviour pattern not yet raised today: studied inside the sleep window", sb.run("brief"))
        sb.run("observe", "raised late nights; will stop at 23:00", "--tag", "coach", "--pattern", "late-night")
        text = sb.run("stats", "patterns")
        self.assertNotIn("RAISE NOW", text)                              # one a day
        self.assertNotIn("Behaviour pattern", sb.run("brief"))
        sb.at("2026-03-10T20:30:00+05:30")
        sb.do("shell/pipes")
        text = sb.run("stats", "patterns")
        self.assertIn("[hold] late-night", text)                         # it rests for a few days
        self.assertEqual(text.count("[RAISE NOW]"), 1)                   # the next one comes up instead
        self.assertIn("coach", sb.run("observations", "--tag", "coach"))


if __name__ == "__main__":
    unittest.main()
