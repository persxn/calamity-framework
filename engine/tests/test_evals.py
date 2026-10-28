"""The behaviour evals (evals/, WP-30) without a model: every case is well formed, and the fixtures set up the
situation its graders assume. The cases themselves run with `claude plugin eval` (evals/README.md)."""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

from tests.helpers import REPO, read

EVALS = os.path.join(REPO, "evals")
GRADER_TYPES = ("tool_used", "llm", "regex")


def cases():
    return sorted(d for d in os.listdir(EVALS) if os.path.isfile(os.path.join(EVALS, d, "prompt.md")))


def front(text):
    m = re.match(r"(?s)^---\n(.*?)\n---\n", text)
    return m.group(1) if m else None


class Cases(unittest.TestCase):
    def test_every_case_is_well_formed_and_listed(self):
        readme = read(os.path.join(EVALS, "README.md"))
        sys.path.insert(0, EVALS)
        try:
            import fixture
        finally:
            sys.path.remove(EVALS)
        scenarios = set(fixture.SCENARIOS) | {"recall", "study", "review"}
        for case in cases():
            folder = os.path.join(EVALS, case)
            self.assertIn("`%s`" % case, readme, "evals/README.md does not list %s" % case)
            meta = front(read(os.path.join(folder, "prompt.md")))
            self.assertIsNotNone(meta, case)
            self.assertIn("description:", meta, case)
            graders = sorted(os.listdir(os.path.join(folder, "graders")))
            self.assertTrue(graders, case)
            for name in graders:
                g = front(read(os.path.join(folder, "graders", name)))
                kind = re.search(r"(?m)^type: (\S+)$", g or "")
                self.assertTrue(kind and kind.group(1) in GRADER_TYPES, "%s/%s" % (case, name))
                for key in ("input_match", "pattern"):
                    m = re.search(r"(?m)^%s: '(.*)'$" % key, g)
                    if m:
                        re.compile(m.group(1).replace("''", "'"))
            scaffold = os.path.join(folder, "scaffold.sh")
            if os.path.isfile(scaffold):
                used = re.search(r"evals/fixture\.py\" (\S+)", read(scaffold))
                self.assertTrue(used and used.group(1) in scenarios, case)
                self.assertIn("scaffold_script: scaffold.sh", read(os.path.join(folder, "case.yaml")), case)


class Runner(unittest.TestCase):
    """tools/evals.py picks the cases a branch touches; nothing here calls a model."""

    def test_a_branch_runs_the_cases_it_touches(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location("eval_runner", os.path.join(REPO, "tools", "evals.py"))
        runner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runner)
        cases = runner.all_cases()
        self.assertEqual(runner.select(["evals/gates-respected/graders/consolidate-first.md", "README.md"], cases),
                         ["gates-respected"])
        self.assertEqual(runner.select([".claude/skills/study/SKILL.md"], cases), cases)
        self.assertEqual(runner.select(["framework/method.md"], cases), cases)
        self.assertEqual(runner.select(["engine/cal/career.py", "CHANGELOG.md"], cases), [])
        self.assertFalse(os.path.exists(os.path.join(REPO, ".github", "workflows", "evals.yml")),
                         "evals run on this machine's Claude login (tools/evals.py), never in CI")


class Fixtures(unittest.TestCase):
    """The cheap scenarios, built for real: what the engine says there is what the graders expect."""

    def build(self, scenario):
        path = tempfile.mkdtemp(prefix="calamity-eval-")
        self.addCleanup(shutil.rmtree, path, True)
        env = {k: v for k, v in os.environ.items() if not k.startswith("CALAMITY_")}
        subprocess.run([sys.executable, os.path.join(EVALS, "fixture.py"), scenario], cwd=path, env=env, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        return path, env

    def cal(self, path, env, *args):
        proc = subprocess.run([sys.executable, os.path.join("engine", "calamity.py")] + list(args), cwd=path, env=env,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return proc.stdout.decode("utf-8", "replace")

    def test_gates_has_a_topic_to_consolidate_first(self):
        path, env = self.build("gates")
        out = self.cal(path, env, "next")
        self.assertIn("NEXT: consolidate", out)
        self.assertIn("gate.cs.digital-logic/boolean-algebra", out)

    def test_contest_is_running(self):
        path, env = self.build("contest")
        out = self.cal(path, env, "cf", "contests")
        self.assertIn("RUNNING NOW", out)
        self.assertIn("2190", out)

    def test_drill_is_verified_and_open(self):
        path, env = self.build("drill")
        ident = read(os.path.join(path, ".calamity", "eval", "open-item")).strip()
        self.assertRegex(ident, r"^it-[a-z0-9]{10}$")
        out = self.cal(path, env, "item", "show", ident)
        self.assertIn("audit", out)
        self.assertNotIn("apt lists", out)                 # the sealed solution stays sealed
        self.assertIn("open: waiting for the learner's answer. Never solve it", out)


if __name__ == "__main__":
    unittest.main()
