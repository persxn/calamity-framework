"""The command line as a learner's machine runs it: a separate process, through engine/calamity.py."""
import json
import os
import subprocess
import sys
import unittest

from tests.helpers import ENGINE, Case, read, write

SCRIPT = os.path.join(ENGINE, "calamity.py")


class Process(Case):
    def call(self, *args, stdin=None, env=None, cwd=None):
        full = {k: v for k, v in os.environ.items() if not k.startswith("CALAMITY_")}
        full.update({"CALAMITY_ROOT": self.sb.root, "CALAMITY_NOW": self.sb.now()})
        full.update(env or {})
        proc = subprocess.run([sys.executable, SCRIPT] + list(args), input=stdin, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, env=full, cwd=cwd or self.sb.root, timeout=120)
        return proc.returncode, proc.stdout.decode("utf-8"), proc.stderr.decode("utf-8")

    def test_help_and_version(self):
        code, out, err = self.call("--help")
        self.assertEqual((code, err), (0, ""))
        for name in ("brief", "ask", "answer", "tree", "gate", "cf", "notes", "doctor"):
            self.assertIn(name, out)
        code, out, _ = self.call()
        self.assertEqual(code, 0)
        self.assertIn("usage:", out)
        code, out, _ = self.call("version")
        self.assertEqual(code, 0)
        self.assertIn("Calamity framework", out)

    def test_exit_codes(self):
        self.assertEqual(self.call("brief")[0], 0)
        code, out, err = self.call("tree", "show", "no-such-skill")
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertTrue(err.startswith("error: unknown skill"))
        self.assertNotIn("Traceback", err)
        self.assertEqual(self.call("definitely-not-a-command")[0], 2)
        self.assertEqual(self.call("remind", "check")[0], 3)          # not onboarded: nothing to say
        self.sb.onboard()
        self.sb.run("enroll", "shell")
        self.sb.run("covered", "shell/pipes")
        code, out, _ = self.call("ask", "--topic", "shell/pipes")
        self.assertEqual(code, 4)
        self.assertTrue(out.startswith("NEED_ITEM"))

    def test_output_is_utf8_whatever_the_locale(self):
        self.sb.onboard()
        for env in ({"LC_ALL": "C", "LANG": "C", "PYTHONIOENCODING": "", "PYTHONUTF8": "0"},
                    {"PYTHONIOENCODING": "cp1252"}):
            proc_env = {k: v for k, v in env.items() if v != ""}
            code, out, err = self.call("dash", "roadmap", "--all-tracks", env=proc_env)
            self.assertEqual((code, err), (0, ""))
            self.assertIn("○", out)
            self.assertIn("·", out)

    def test_stdin_json_and_working_directory(self):
        self.sb.onboard()
        draft = {"type": "mcq", "topics": ["shell/pipes"], "stem": "Which symbol pipes one command into another?",
                 "options": [">", "|", "&", ";"], "answer": "B", "solution": "The vertical bar connects stdout to stdin."}
        code, out, err = self.call("item", "draft", "--stdin", stdin=json.dumps(draft).encode("utf-8"), cwd=ENGINE)
        self.assertEqual((code, err), (0, ""))
        self.assertIn("draft stored: it-", out)
        self.assertTrue(os.path.isdir(self.sb.path("learner", "items", "shell")))   # written under the root, not the cwd
        self.assertFalse(os.path.exists(os.path.join(ENGINE, "learner")))

    def test_two_machines_merge(self):
        """Two laptops study separately, their event files are put side by side, and the result is one history."""
        sb = self.sb
        sb.run("setup", "--machine", "laptop-a")
        sb.onboard()
        sb.run("enroll", "shell")
        ident = sb.item("shell/pipes")
        sb.do("shell/pipes")
        other = self.sb.__class__()                       # the second laptop: a clone of the learner folder
        self.addCleanup(other.close)
        write(other.path("learner", "profile.md"), read(sb.path("learner", "profile.md")))
        for folder in ("events", os.path.join("items", "shell")):
            for name in os.listdir(sb.path("learner", folder)):
                write(other.path("learner", folder, name), read(sb.path("learner", folder, name)))
        other.run("setup", "--machine", "laptop-b")
        other.at(sb.now()).advance(days=3)
        other.ask("shell/pipes")
        other.answer(ident, "B")
        # laptop A later receives laptop B's file (git pull): nothing else is needed
        for name in os.listdir(other.path("learner", "events")):
            if "laptop-b" in name:
                write(sb.path("learner", "events", name), read(other.path("learner", "events", name)))
        sb.advance(days=3, hours=1)
        state = sb.state()
        self.assertEqual(state.topics["shell/pipes"].n_vok, 2)
        self.assertEqual(sorted(os.listdir(sb.path("learner", "events"))),
                         ["2026-03.laptop-a.jsonl", "2026-03.laptop-b.jsonl"])
        self.assertIn("from 2 file(s)", sb.run("rebuild"))
        self.assertEqual(read(sb.path("learner", "PROGRESS.md")),
                         (other.run("rebuild"), read(other.path("learner", "PROGRESS.md")))[1])   # both laptops agree


class SelfTest(unittest.TestCase):
    def test_selftest_command_exists_but_is_not_run_from_inside_itself(self):
        from cal import cli
        parser = cli.build_parser()
        args = parser.parse_args(["selftest"])
        self.assertIs(args.func, cli.cmd_selftest)


if __name__ == "__main__":
    unittest.main()
