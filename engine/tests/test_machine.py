import json
import os
import plistlib
import shutil
import subprocess
import sys
import unittest

from tests.helpers import ENGINE, Case, write

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
        self.assertEqual(data["hooks"]["Stop"], existing["hooks"]["Stop"])
        entries = data["hooks"]["SessionStart"]
        self.assertEqual(len(entries), 2)
        ours = entries[-1]["hooks"][0]
        self.assertEqual(ours["type"], "command")
        self.assertEqual(ours["command"], sys.executable)             # a real executable, no shell involved
        self.assertEqual(ours["args"], [sb.path("engine", "calamity.py"), "brief", "--hook"])
        self.assertTrue(os.path.isabs(ours["args"][0]))
        self.assertEqual(ours["timeout"], 30)
        sb.run("setup", "--hook")                                     # installing again does not duplicate it
        self.assertEqual(len(self.settings()["hooks"]["SessionStart"]), 2)
        self.assertIn("session-start hook: ok", sb.run("setup"))

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
        self.assertIn("no Calamity hook was installed", sb.run("setup", "--remove-hook"))

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
        if os.name == "nt" and (" " in sys.executable or " " in sb.root):
            sb.run("setup", "--statusline", expect=2)                  # refused rather than written wrongly
            self.assertIn("contains spaces", sb.err)
            return
        sb.run("setup", "--statusline")
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
        self.assertTrue(all(line.endswith("# calamity-remind") for line in cron))
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
        with open(sb.path(".calamity", "reminders", "com.calamity.remind.plist"), "rb") as fh:
            plist = plistlib.load(fh)
        self.assertEqual(plist["Label"], "com.calamity.remind")
        self.assertEqual(plist["StartCalendarInterval"], [{"Hour": 7, "Minute": 15}])
        self.assertEqual(plist["ProgramArguments"][0], "/bin/sh")
        self.assertTrue(plist["ProgramArguments"][1].endswith("notify.sh"))

    def test_windows(self):
        sb = self.sb
        out = sb.run("remind", "render", "--times", "09:00,21:45", "--os", "windows")
        self.assertIn("install.cmd", out)
        folder = sb.path(".calamity", "reminders")
        with open(os.path.join(folder, "install.cmd"), "rb") as fh:
            install = fh.read().decode("utf-8")
        self.assertIn("\r\n", install)
        self.assertEqual(install.count("schtasks /Create"), 2)
        self.assertIn("/SC DAILY /ST 21:45", install)
        self.assertIn('/TN "Calamity\\Remind-2145"', install)
        self.assertIn("notify.ps1", install)
        with open(os.path.join(folder, "remove.cmd"), "rb") as fh:
            self.assertEqual(fh.read().decode("utf-8").count("schtasks /Delete"), 2)
        with open(os.path.join(folder, "notify.ps1"), "r", encoding="utf-8") as fh:
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
