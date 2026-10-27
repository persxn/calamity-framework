"""What a learner's machine does to the engine: damaged files, bad settings, two commands at once,
Windows code pages and file locks, interrupted writes. Nothing here may end in a traceback."""
import json
import os
import re
import subprocess
import sys
import unittest
from unittest import mock

from tests.helpers import ENGINE, Case, read, write

from cal import cli, notes, store
from cal.store import Repo

SCRIPT = os.path.join(ENGINE, "calamity.py")


def call(sb, *args, stdin=None, env=None):
    """Run the engine as a separate process, the way Claude Code and the hook run it."""
    full = {k: v for k, v in os.environ.items() if not k.startswith("CALAMITY_")}
    full.update({"CALAMITY_ROOT": sb.root, "CALAMITY_NOW": sb.now()})
    full.update(env or {})
    proc = subprocess.run([sys.executable, SCRIPT] + list(args), input=stdin, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, env=full, cwd=sb.root, timeout=120)
    # A text-mode child on Windows writes "\r\n"; compare text, not line endings.
    return (proc.returncode, proc.stdout.decode("utf-8").replace("\r\n", "\n"),
            proc.stderr.decode("utf-8").replace("\r\n", "\n"))


class DamagedData(Case):
    def test_malformed_event_lines_are_reported_not_fatal(self):
        sb = self.sb
        sb.onboard()
        sb.run("observe", "a real event before the damage")
        before = sb.state().n_events
        lines = [
            '{"id":[1],"ts":"2026-03-02T09:00:00+05:30","t":"note","text":"id is a list"}',
            '{"id":"a1","ts":"2026-03-02T09:00:00+05:30","t":"note","k":{"x":1}}',
            '{"id":"a2","ts":12345,"t":"note"}',
            '{"id":"a3","ts":"2026-03-02T09:00:00+05:30","t":5}',
            '{"id":"a4","ts":"2026-03-02T09:00:00+05:30","t":"note","q":"7"}',
            '{"id":"a5","ts":"yesterday","t":"note"}',
            '[1, 2, 3]',
            '"just a string"',
        ]
        write(sb.path("learner", "events", "2026-03.damaged.jsonl"), "\n".join(lines) + "\n")
        for args, code in ((["today"], 0), (["brief"], 0), (["next"], 0), (["dash", "all"], 0),
                           (["statusline"], 0), (["doctor"], 1), (["rebuild"], 2)):
            out = sb.run(*args, expect=code)
            self.assertNotIn("Traceback", out + sb.err)
        doctor = sb.run("doctor", expect=1)
        self.assertIn("FAIL  event log", doctor)
        self.assertIn("'id' is missing or not a string", doctor)
        self.assertIn("Data notes: 8 event line(s) could not be read", sb.run("brief"))
        self.assertEqual(sb.state().n_events, before)   # every good event still counts


class Settings(Case):
    def test_bad_configuration_override_is_refused(self):
        sb = self.sb
        for key, value in (("cfg.new_per_day", "lots"), ("cfg.new_per_day", "2.5"), ("cfg.no_such_setting", "3"),
                           ("cfg.retention.mastery", "1.5"), ("cfg.fuzz", "maybe"), ("cfg.schema", "2"),
                           ("cfg.day_start_hour", "-1")):
            sb.run("profile", "set", key, value, expect=2)
            self.assertTrue(sb.err.startswith("error: "), sb.err)
        self.assertEqual(sb.run("profile", "set", "cfg.new_per_day", "5").strip(), "cfg.new_per_day: 5")
        self.assertEqual(Repo(sb.root).cfg("new_per_day"), 5)
        sb.run("profile", "set", "cfg.gate.daily_hours", "7.5")
        self.assertEqual(Repo(sb.root).cfg("gate.daily_hours"), 7.5)
        sb.run("profile", "set", "cfg.fuzz", "false")
        self.assertIs(Repo(sb.root).cfg("fuzz"), False)

    def test_bad_override_already_stored_is_survived_and_reported(self):
        sb = self.sb
        sb.onboard()
        profile = sb.path("learner", "profile.md")
        write(profile, read(profile).replace("---\n", "---\ncfg.new_per_day: lots\ncfg.nonsense: 3\n", 1))
        repo = Repo(sb.root)
        self.assertEqual(repo.cfg("new_per_day"), 8)                  # the default stands in
        self.assertEqual(len(repo.config_errors), 2)
        for args in (["today"], ["next"], ["dash"], ["brief"]):
            self.assertNotIn("Traceback", sb.run(*args) + sb.err)
        self.assertIn("configuration overrides: 2 ignored", sb.run("doctor"))
        self.assertIn("Data notes: 2 configuration override(s) ignored", sb.run("brief"))

    def test_profile_values_mean_what_the_learner_typed(self):
        sb = self.sb
        cases = (
            (["name", "Rao, Asha"], "Rao, Asha"), (["name", "Asha", "Rao"], "Asha Rao"), (["name", "Yes"], "Yes"),
            (["teach.style", "examples first, then rules"], "examples first, then rules"),
            (["tracks", "10x cp"], ["10x", "cp"]), (["tracks", "[10x, gate-cs]"], ["10x", "gate-cs"]),
            (["tracks", "10x"], ["10x"]), (["gate.papers", "cs,da"], ["CS", "DA"]),
            (["reminders.times", "09:00,21:30"], ["09:00", "21:30"]), (["sleep.start", "23:30"], "23:30"),
            (["workout.minutes", "45"], 45), (["daily.target_hours", "7.5"], 7.5),
            (["gate.exam_date.CS", "2027-02-07"], "2027-02-07"), (["onboarded", "true"], True),
            (["gate.target_marks.CS", "72"], 72), (["cp.target_rating", "1800"], 1800),
        )
        for words, expected in cases:
            sb.run("profile", "set", *words)
            self.assertEqual(Repo(sb.root).prof(words[0]), expected, words)
        for words in (["sleep.start", "25:00"], ["sleep.end", "late"], ["gate.exam_date.CS", "2027-02-30"],
                      ["gate.exam_date.DA", "next week"], ["workout.minutes", "lots"], ["onboarded", "maybe"],
                      ["mode.default", "cram"], ["gate.papers", "computer science"], ["reminders.times", "9am"],
                      ["gate.target_marks.CS", "120"], ["cp.target_date", "2027"]):
            sb.run("profile", "set", *words, expect=2)
        self.assertEqual(Repo(sb.root).prof("sleep.start"), "23:30")   # a refused value changes nothing

    def test_several_keys_in_one_call_all_or_nothing(self):
        sb = self.sb
        out = sb.run("profile", "set", "name=Robin", "tracks=gate-da,cp", "teach.style=examples first, then rules",
                     "sleep.start=00:30", "cfg.new_per_day=6")
        self.assertIn("teach.style: \"examples first, then rules\"", out)
        repo = Repo(sb.root)
        self.assertEqual((repo.prof("name"), repo.prof("tracks"), repo.cfg("new_per_day")), ("Robin", ["gate-da", "cp"], 6))
        sb.run("profile", "set", "name=Kim", "sleep.end=late", expect=2)  # one bad value: nothing is written
        self.assertEqual(Repo(sb.root).prof("name"), "Robin")
        sb.run("profile", "set", "name=Kim", "oops", expect=2)

    def test_text_flag_anywhere_none_unsets_and_unknown_keys_are_flagged(self):
        sb = self.sb
        # the onboard skill writes `profile set teach.style --text "..."`: the flag may stand anywhere
        for args in (["teach.style", "--text", "Examples, then rules."], ["--text", "teach.style", "Examples, then rules."],
                     ["teach.style", "Examples, then rules.", "--text"]):
            sb.run("profile", "set", *args)
            self.assertEqual(Repo(sb.root).prof("teach.style"), "Examples, then rules.", args)
        sb.run("profile", "--text", "set", "gate.target_source", "rank 1000, about N marks")
        self.assertEqual(Repo(sb.root).prof("gate.target_source"), "rank 1000, about N marks")
        sb.run("profile", "set", "reminders.times", "09:00,21:00")
        self.assertEqual(sb.run("profile", "set", "reminders.times", "none").strip(), "unset: reminders.times")
        self.assertIsNone(Repo(sb.root).prof("reminders.times"))
        sb.run("profile", "set", "name", "None")
        self.assertEqual(Repo(sb.root).prof("name"), "None")                # a name stays a name
        out = sb.run("profile", "set", "gate.target", "a good score")
        self.assertIn("note: the engine does not read 'gate.target'", out)
        self.assertNotIn("note:", sb.run("profile", "set", "gate.target_marks.DA", "70"))


class Writes(unittest.TestCase):
    def setUp(self):
        import tempfile

        self.dir = tempfile.mkdtemp(prefix="calamity-writes-")
        self.addCleanup(lambda: __import__("shutil").rmtree(self.dir, ignore_errors=True))

    def test_replace_is_retried_while_another_program_holds_the_file(self):
        path = os.path.join(self.dir, "profile.md")
        real = os.replace
        failures = {"left": 3}

        def flaky(src, dst):
            if failures["left"]:
                failures["left"] -= 1
                raise PermissionError(13, "The process cannot access the file", dst)
            return real(src, dst)

        with mock.patch.object(store.os, "replace", flaky), mock.patch.object(store.time, "sleep"):
            store.write_text(path, "first\n")
        self.assertEqual(read(path), "first\n")
        with mock.patch.object(store.os, "replace", side_effect=PermissionError(13, "held", path)), \
                mock.patch.object(store.time, "sleep"):
            with self.assertRaises(PermissionError):
                store.write_text(path, "second\n")
        self.assertEqual(read(path), "first\n")                      # the old file is intact
        self.assertEqual(sorted(os.listdir(self.dir)), ["profile.md"])  # and no temporary file is left

    def test_durable_writes_reach_the_disk_before_they_replace_anything(self):
        synced = []
        with mock.patch.object(store.os, "fsync", side_effect=lambda fd: synced.append(fd)):
            store.write_text(os.path.join(self.dir, "a.md"), "x")
            self.assertEqual(len(synced), 1)
            store.write_text(os.path.join(self.dir, "cache.json"), "{}", durable=False)
            self.assertEqual(len(synced), 1)

    def test_engine_writes_files_only_through_the_atomic_writer(self):
        folder = os.path.join(ENGINE, "cal")
        writes = re.compile(r"""open\([^)]*['"][wax]b?['"]""")
        for name in sorted(os.listdir(folder)):
            if not name.endswith(".py") or name == "store.py":
                continue
            with open(os.path.join(folder, name), "r", encoding="utf-8") as fh:
                for n, line in enumerate(fh, 1):
                    self.assertIsNone(writes.search(line), "%s:%d writes a file directly: %s" % (name, n, line.strip()))


class Concurrent(Case):
    """Two engine commands at once: a background examiner storing items while the tutor records answers."""

    WRITER = """
import sys
sys.path.insert(0, %(engine)r)
from cal.store import Repo
repo = Repo()
tag, size, mode = sys.argv[1], int(sys.argv[2]), sys.argv[3]
for i in range(%(count)d):
    if mode == "log":
        repo.append("note", text="%%s-%%d " %% (tag, i) + "x" * size)
    else:
        repo.set_profile("key%%s.n%%d" %% (tag, i), i)
"""

    def test_parallel_writers_lose_and_damage_nothing(self):
        sb = self.sb
        Repo(sb.root).machine()                       # one machine id, as on a set-up laptop
        env = dict({k: v for k, v in os.environ.items() if not k.startswith("CALAMITY_")}, CALAMITY_ROOT=sb.root)
        code = self.WRITER % {"engine": ENGINE, "count": 60}
        jobs = [("a", 10, "log"), ("b", 9000, "log"), ("c", 20000, "log"), ("d", 300, "log"),
                ("e", 0, "profile"), ("f", 0, "profile"), ("g", 0, "profile")]
        procs = [subprocess.Popen([sys.executable, "-c", code, tag, str(size), mode], env=env)
                 for tag, size, mode in jobs]
        for proc in procs:
            self.assertEqual(proc.wait(timeout=300), 0)
        repo = Repo(sb.root)
        events = repo.events()
        self.assertEqual(repo.event_errors, [])
        self.assertEqual(sum(1 for e in events if e["t"] == "note"), 4 * 60)
        for tag in "abcd":
            self.assertEqual(sum(1 for e in events if e.get("text", "").startswith(tag + "-")), 60)
        profile = repo.profile()
        for tag in "efg":
            self.assertEqual(sum(1 for k in profile if k.startswith("key%s." % tag)), 60, tag)


class Process(Case):
    def test_hook_input_is_read_as_utf8_whatever_the_code_page(self):
        sb = self.sb
        sb.onboard()
        payload = json.dumps({"source": "resume", "cwd": "C:\\Users\\Łukasz Żółw\\calamity",
                              "session_title": "Fourier, ő"}, ensure_ascii=False).encode("utf-8")
        # PYTHONIOENCODING=cp1252 makes Python decode pipes the way Windows does by default
        code, out, err = call(sb, "brief", "--hook", stdin=payload, env={"PYTHONIOENCODING": "cp1252"})
        self.assertEqual((code, err), (0, ""))
        self.assertTrue(out.startswith("=== CALAMITY BRIEF ===\nTime:"), out)
        sessions = [e for e in Repo(sb.root).events() if e["t"] == "session"]
        self.assertEqual([e["src"] for e in sessions], ["resume"])

    def test_hook_survives_input_it_does_not_expect(self):
        sb = self.sb
        sb.onboard()
        for stdin in (b"[1, 2]", b"not json", b'{"source": 7}', b"\xff\xfe\x00garbage", b""):
            code, out, err = call(sb, "brief", "--hook", stdin=stdin)
            self.assertEqual(code, 0)
            self.assertNotIn("could not be built", out)
            self.assertIn("=== END BRIEF ===", out)

    def test_json_input_in_utf8_from_a_pipe_and_utf16_from_powershell(self):
        sb = self.sb
        draft = {"type": "mcq", "topics": ["shell/pipes"], "stem": "Łódź or Kraków: which pipe — | or ||?",
                 "options": ["|", "||"], "answer": "A", "solution": "A single bar connects two commands."}
        raw = json.dumps(draft, ensure_ascii=False).encode("utf-8")
        code, out, err = call(sb, "item", "draft", "--stdin", stdin=raw, env={"PYTHONIOENCODING": "cp1252"})
        self.assertEqual((code, err), (0, ""))
        ident = re.search(r"it-[a-z0-9]{10}", out).group(0)
        self.assertIn("Łódź or Kraków", sb.run("item", "show", ident))
        path = sb.path(".calamity", "tmp", "drafts.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as fh:                       # what `... > drafts.json` gives in Windows PowerShell 5
            fh.write(json.dumps([draft], ensure_ascii=False).encode("utf-16"))
        self.assertIn("imported 1 item(s)", sb.run("item", "import", "--file", path))

    def test_unexpected_failures_are_errors_not_tracebacks_with_exit_1(self):
        sb = self.sb
        sb.onboard()
        with mock.patch.object(cli, "cmd_today", side_effect=PermissionError(13, "Permission denied", "/x/profile.md")):
            sb.run("today", expect=2)
        self.assertEqual(sb.err.strip(), "error: /x/profile.md: Permission denied. Another program may have the file "
                                         "open, or it is read-only.")
        with mock.patch.object(cli, "cmd_today", side_effect=ValueError("boom")):
            sb.run("today", expect=2)
        self.assertIn("ValueError: boom", sb.err)
        self.assertIn("error: internal error in the engine", sb.err)
        with mock.patch.object(cli, "cmd_today", side_effect=KeyboardInterrupt):
            sb.run("today", expect=130)

    def test_counts_and_widths_must_make_sense(self):
        sb = self.sb
        sb.onboard()
        for args in (["stats", "week", "--days", "0"], ["item", "needs", "--n", "-1"], ["observations", "--n", "0"],
                     ["dash", "--width", "5"], ["answer", "it-0000000000", "--answer", "A", "--hints", "-2"],
                     ["tree", "suggest", "--n", "0"], ["cf", "analyse", "--days", "x"]):
            sb.run(*args, expect=2)
            self.assertIn("error: argument", sb.err)

    def test_selftest_shows_the_whole_failure(self):
        report = "\n".join(["FAIL: test_%d" % i for i in range(60)] + ["FAILED (failures=60)"])
        done = subprocess.CompletedProcess([], 1, stdout=report.encode("utf-8"))
        with mock.patch.object(cli.subprocess, "run", return_value=done):
            out = self.sb.run("selftest", expect=2)
        self.assertIn("FAIL: test_0", out)
        self.assertIn("FAILED (failures=60)", out)


class Installers(Case):
    def test_status_line_can_be_removed_and_is_checked(self):
        sb = self.sb
        local = sb.path(".claude", "settings.local.json")
        write(local, json.dumps({"permissions": {"allow": ["Bash(ls *)"]}}))
        write(sb.path("engine", "calamity.py"), "# the entry point the status line names\n")
        self.assertIn("status line  ", sb.run("doctor", expect=None))
        self.assertIn("not installed (optional: setup --statusline)", sb.run("doctor", expect=None))
        sb.run("setup", "--statusline")
        self.assertRegex(sb.run("doctor", expect=None), r"OK +status line +installed")
        self.assertEqual(sb.run("setup", "--remove-statusline").strip(), "status line removed")
        data = json.loads(read(local))
        self.assertNotIn("statusLine", data)
        self.assertEqual(data["permissions"], {"allow": ["Bash(ls *)"]})   # everything else is kept
        self.assertEqual(sb.run("setup", "--remove-statusline").strip(), "no Calamity status line was installed")
        # someone else's status line is neither reported as ours nor removed
        write(local, json.dumps({"statusLine": {"type": "command", "command": "~/.claude/mine.sh"}}))
        self.assertIn("another status line is configured", sb.run("doctor", expect=None))
        sb.run("setup", "--remove-statusline")
        self.assertIn("statusLine", json.loads(read(local)))


class Sources(Case):
    def test_import_dry_run_writes_nothing(self):
        sb = self.sb
        sb.run("source", "add", "course", "--title", "Course", "--route", "paste")
        path = sb.path("learner", "sources", "course.md")
        before = read(path)
        rows = sb.path(".calamity", "tmp", "rows.json")
        write(rows, json.dumps([{"id": "l1", "title": "Pipes", "topics": ["shell/pipes"]},
                                {"id": "l2", "title": "Made up", "topics": ["shell/no-such-topic"]},
                                {"id": "l3", "title": "Intro"}]))
        out = sb.run("source", "import", "course", "--file", rows, "--dry-run", expect=2)
        self.assertIn("dry run, nothing written: 3 item(s) would be added, 0 replaced", out)
        self.assertIn("ERROR unknown topic shell/no-such-topic", out)
        self.assertIn("warn  1 item(s) not mapped to any topic", out)
        self.assertEqual(read(path), before)
        write(rows, json.dumps([{"id": "l1", "title": "Pipes", "topics": ["shell/pipes"]}]))
        self.assertIn("1 item(s) would be added", sb.run("source", "import", "course", "--file", rows, "--dry-run"))
        self.assertEqual(read(path), before)
        self.assertTrue(os.path.isfile(rows))              # a dry run keeps its input as well


class Notes(Case):
    def test_a_pdf_held_open_by_a_viewer_is_reported(self):
        sb = self.sb
        sb.onboard(book__format="pdf")
        write(sb.path("learner", "notes", "docker", "tex", "images.tex"), "\\section{Images}\nText.\n")
        fake = [sys.executable, "-c", "open('main.pdf', 'wb').write(b'%PDF-1.4 fake')"]
        with mock.patch.object(notes, "tex_engine", return_value=("tectonic", fake)), \
                mock.patch.object(notes.shutil, "copyfile", side_effect=PermissionError(13, "in use")):
            sb.run("notes", "pdf", "docker", expect=2)
        self.assertIn("the PDF was built", sb.err)
        self.assertIn("If it is open in a PDF viewer, close it", sb.err)
        self.assertNotIn("Traceback", sb.err)


if __name__ == "__main__":
    unittest.main()
