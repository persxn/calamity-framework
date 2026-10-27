"""The key guard and the scratch folder: worked answers and sealed keys stay out of the conversation."""
import io
import json
import os
import subprocess
import sys
import time

from tests.helpers import ENGINE, Case, write

from cal import guard, scratch
from cal.store import Repo


class Decide(Case):
    def call(self, tool, agent=None, cwd=None, **tool_input):
        payload = {"tool_name": tool, "tool_input": tool_input, "cwd": cwd or self.sb.root}
        if agent:
            payload["agent_type"] = agent
        return guard.decide(payload, self.sb.root)

    def test_nobody_reads_the_item_files(self):
        item = self.sb.path("learner", "items", "shell", "it-0123456789.json")
        self.assertIn("learner/items", self.call("Read", file_path=item))
        self.assertIn("examiner", self.call("Read", agent="examiner", file_path=item))
        self.assertTrue(self.call("Read", agent="checker", file_path=item))
        self.assertTrue(self.call("Read", file_path="learner/items/shell/x.json"))           # a relative path
        self.assertTrue(self.call("Read", cwd=self.sb.path("learner"), file_path="items/shell/x.json"))
        self.assertTrue(self.call("Glob", pattern="learner/items/**/*.json"))
        self.assertIsNone(self.call("Read", file_path=self.sb.path("framework", "config.md")))
        self.assertIsNone(self.call("Glob", pattern="**/*.md"))                                # names, not keys

    def test_each_agent_keeps_its_own_scratch(self):
        mine = self.sb.path(".calamity", "tmp", "examiner", "batch-1", "work.py")
        theirs = self.sb.path(".calamity", "tmp", "checker", "it-0123456789", "solve.py")
        self.assertIsNone(self.call("Read", agent="examiner", file_path=mine))
        self.assertIsNone(self.call("Read", agent="calamity:examiner", file_path=mine))     # as a plugin agent
        self.assertTrue(self.call("Read", agent="examiner", file_path=theirs))
        self.assertIsNone(self.call("Read", agent="checker", file_path=theirs))
        self.assertTrue(self.call("Read", agent="checker", file_path=mine))
        self.assertTrue(self.call("Read", file_path=mine))                                     # nor the tutor
        self.assertTrue(self.call("Read", agent="Explore", file_path=theirs))
        self.assertIsNone(self.call("Read", file_path=self.sb.path(".calamity", "tmp", "course.json")))

    def test_shell_commands_that_name_a_sealed_folder(self):
        self.assertTrue(self.call("Bash", command="cat learner/items/shell/it-0123456789.json"))
        self.assertTrue(self.call("Bash", command="type learner\\items\\shell\\x.json"))      # Windows separators
        self.assertTrue(self.call("PowerShell", command="Get-Content learner/items/x.json"))
        self.assertTrue(self.call("Bash", command="python3 .calamity/tmp/checker/it-1/solve.py"))
        self.assertIsNone(self.call("Bash", agent="checker", command="python3 .calamity/tmp/checker/it-1/solve.py"))
        self.assertIsNone(self.call("Bash", agent="examiner", command=(
            "python3 engine/calamity.py item import --file .calamity/tmp/examiner/b1/drafts.json --by examiner")))
        self.assertIsNone(self.call("Bash", command="python3 engine/calamity.py item show it-0123456789"))
        self.assertIsNone(self.call("Bash", command="git add learner && git status --short"))

    def test_searches_that_would_reach_the_items(self):
        root = self.sb.root
        self.assertIsNone(self.call("Grep", pattern="lambda", path=root))               # no items yet: nothing to reach
        write(self.sb.path("learner", "items", "shell", "it-0123456789.json"), "{}")
        self.assertIn("narrower folder", self.call("Grep", pattern="lambda", path=root))
        self.assertTrue(self.call("Grep", pattern="lambda"))                              # the default path is cwd
        self.assertTrue(self.call("Grep", pattern="lambda", path=self.sb.path("learner")))
        self.assertTrue(self.call("Grep", pattern="lambda", path=root, glob="*.json"))
        self.assertTrue(self.call("Grep", pattern="lambda", path=root, glob="**/*"))
        self.assertIsNone(self.call("Grep", pattern="lambda", path=root, glob="*.md"))
        self.assertIsNone(self.call("Grep", pattern="lambda", path=root, type="py"))
        self.assertIsNone(self.call("Grep", pattern="lambda", path=self.sb.path("framework")))
        self.assertIsNone(self.call("Grep", pattern="lambda", path=self.sb.path("learner", "notes")))

    def test_other_tools_and_odd_input_pass(self):
        self.assertIsNone(self.call("Edit", file_path=self.sb.path("learner", "items", "x.json")))  # settings deny it
        self.assertIsNone(guard.decide({"tool_name": "Read"}, self.sb.root))
        self.assertIsNone(guard.decide({"tool_name": "Read", "tool_input": "nonsense"}, self.sb.root))
        self.assertTrue(guard.works(self.sb.root))


class Hook(Case):
    def run_hook(self, payload, raw=None):
        env = dict(os.environ, CALAMITY_ROOT=self.sb.root)
        data = raw if raw is not None else json.dumps(payload).encode("utf-8")
        start = time.time()
        proc = subprocess.run([sys.executable, os.path.join(ENGINE, "calamity.py"), "guard", "tool"], input=data,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc.stdout.decode("utf-8"), time.time() - start

    def test_the_hook_as_claude_code_runs_it(self):
        out, _ = self.run_hook({"tool_name": "Read", "cwd": self.sb.root,
                                "tool_input": {"file_path": self.sb.path("learner", "items", "a", "b.json")}})
        decision = json.loads(out)["hookSpecificOutput"]
        self.assertEqual((decision["hookEventName"], decision["permissionDecision"]), ("PreToolUse", "deny"))
        self.assertIn("learner/items", decision["permissionDecisionReason"])
        out, _ = self.run_hook({"tool_name": "Read", "cwd": self.sb.root,
                                "tool_input": {"file_path": self.sb.path("framework", "config.md")}})
        self.assertEqual(out, "")                                  # silence: the normal permission flow goes on
        self.assertEqual(self.run_hook(None, raw=b"{not json")[0], "")  # a fault never blocks every tool

    def test_the_hook_answers_in_process_too(self):
        out = io.StringIO()
        stream = io.BytesIO(json.dumps({"tool_name": "Bash", "tool_input": {"command": "cat learner/items/x"}}).encode())
        saved, sys.stdout = sys.stdout, out
        os.environ["CALAMITY_ROOT"] = self.sb.root
        try:
            self.assertEqual(guard.hook_main(stream), 0)
        finally:
            sys.stdout = saved
            os.environ.pop("CALAMITY_ROOT", None)
        self.assertIn('"deny"', out.getvalue())


class Scratch(Case):
    def setUp(self):
        super().setUp()
        self.sb.onboard()
        self.sb.run("enroll", "shell")

    def drafts(self, n=2):
        return json.dumps([{"type": "mcq", "topics": ["shell/pipes"], "difficulty": 2,
                            "stem": "Question %d: which option is right?" % i,
                            "options": ["one %d" % i, "two %d" % i, "three %d" % i, "four %d" % i],
                            "answer": "B", "solution": "Option B, because that is how pipes work.", "expect_s": 60}
                           for i in range(n)])

    def test_an_import_takes_the_examiners_batch_folder_with_it(self):
        batch = self.sb.path(".calamity", "tmp", "examiner", "pipes-1")
        write(os.path.join(batch, "work.py"), "print(2 + 2)\n")
        write(os.path.join(batch, "drafts.json"), self.drafts())
        other = self.sb.path(".calamity", "tmp", "examiner", "pipes-2", "work.py")
        write(other, "print(3)\n")
        self.sb.run("item", "import", "--file", os.path.join(batch, "drafts.json"), "--by", "examiner")
        self.assertFalse(os.path.exists(batch))
        self.assertTrue(os.path.exists(other))                       # another batch is left alone

    def test_a_failed_import_keeps_the_batch_for_the_fix(self):
        batch = self.sb.path(".calamity", "tmp", "examiner", "pipes-1")
        write(os.path.join(batch, "drafts.json"), json.dumps([{"type": "mcq"}]))
        self.sb.run("item", "import", "--file", os.path.join(batch, "drafts.json"), "--by", "examiner", expect=2)
        self.assertTrue(os.path.exists(os.path.join(batch, "drafts.json")))

    def test_single_drafts_and_loose_files_go_one_by_one(self):
        batch = self.sb.path(".calamity", "tmp", "examiner", "b")
        first, second = os.path.join(batch, "one.json"), os.path.join(batch, "two.json")
        for path in (first, second):
            write(path, json.dumps(json.loads(self.drafts(1))[0]))
        self.sb.run("item", "draft", "--file", first, "--by", "examiner")
        self.assertFalse(os.path.exists(first))
        self.assertTrue(os.path.exists(second))                      # still to be stored
        loose = self.sb.path(".calamity", "tmp", "drafts.json")
        write(loose, self.drafts())
        self.sb.run("item", "import", "--file", loose, "--by", "examiner")
        self.assertFalse(os.path.exists(loose))

    def test_recording_a_result_removes_the_checkers_folder(self):
        verified, rejected = self.sb.draft("shell/pipes"), self.sb.draft("shell/pipes")
        for ident in (verified, rejected):
            write(self.sb.path(".calamity", "tmp", "checker", ident, "solve.py"), "print('B')\n")
        self.sb.run("item", "verify", "%s=B" % verified, "--by", "checker")
        self.assertFalse(os.path.exists(self.sb.path(".calamity", "tmp", "checker", verified)))
        self.assertTrue(os.path.exists(self.sb.path(".calamity", "tmp", "checker", rejected)))
        self.sb.run("item", "reject", rejected, "--reason", "two options are defensible")
        self.assertFalse(os.path.exists(self.sb.path(".calamity", "tmp", "checker", rejected)))

    def test_doctor_warns_about_old_scratch_and_clean_removes_it(self):
        old = self.sb.path(".calamity", "tmp", "compute.py")
        write(old, "print(42)\n")
        self.assertIn("OK    scratch folder (.calamity/tmp)", self.sb.run("doctor", expect=None))
        long_ago = time.time() - 3 * 86400
        os.utime(old, (long_ago, long_ago))
        write(self.sb.path(".calamity", "tmp", "checker", "it-1", "solve.py"), "print(1)\n")
        out = self.sb.run("doctor", expect=None)
        self.assertRegex(out, r"WARN  scratch folder \(\.calamity/tmp\) +1 file\(s\) older than a day")
        self.assertEqual(scratch.stale(Repo(self.sb.root)), ["compute.py"])
        listing = self.sb.run("clean", "tmp", "--dry-run")
        self.assertIn("would remove 2 file(s)", listing)
        self.assertIn("  checker/", listing)
        self.assertTrue(os.path.exists(old))
        self.assertIn("removed 2 file(s) from .calamity/tmp", self.sb.run("clean", "tmp"))
        self.assertEqual(os.listdir(self.sb.path(".calamity", "tmp")), [])
        self.assertIn("nothing to remove", self.sb.run("clean", "tmp"))
