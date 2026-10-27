"""The framework repository ships no study record.

A clone whose origin is the framework repository (or a fork of it: any repository named
calamity-framework) tracks nothing under learner/ but learner/README.md, and the git hooks in
tools/git-hooks refuse to commit or push a study record there. A learner's own study repository
is named otherwise, so its record is committed and pushed as usual.
"""
import os
import shutil
import subprocess
import tempfile
import unittest

from tests.helpers import REPO, write

HOOKS = os.path.join(REPO, "tools", "git-hooks")
FRAMEWORK_URL = "https://github.com/persxn/calamity-framework.git"
GIT = ["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "-c", "init.defaultBranch=main",
       "-c", "commit.gpgsign=false"]


def git(cwd, *args):
    proc = subprocess.run(GIT + list(args), cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def is_framework(url: str) -> bool:
    """The same test the hooks make."""
    name = url.rstrip("/").replace("\\", "/").replace(":", "/").rsplit("/", 1)[-1]
    return name in ("calamity-framework", "calamity-framework.git")


@unittest.skipUnless(shutil.which("git"), "needs git")
class FrameworkCheckout(unittest.TestCase):
    def test_only_the_readme_of_learner_is_tracked(self):
        code, top = git(REPO, "rev-parse", "--show-toplevel")
        if code != 0 or os.path.normcase(os.path.realpath(top.strip())) != os.path.normcase(os.path.realpath(REPO)):
            self.skipTest("not a git checkout of its own")
        code, url = git(REPO, "remote", "get-url", "origin")
        if code != 0 or not is_framework(url.strip()):
            self.skipTest("a learner's own repository: their record is meant to be committed here")
        code, out = git(REPO, "ls-files", "learner")
        self.assertEqual(code, 0, out)
        self.assertEqual(out.split(), ["learner/README.md"],
                         "the framework repository tracks a study record; remove it with: git rm --cached <path>")

    def test_the_hooks_recognise_the_framework_repository(self):
        for url in (FRAMEWORK_URL, "https://github.com/someone/calamity-framework", "git@github.com:persxn/calamity-framework.git",
                    "C:\\work\\calamity-framework.git"):
            self.assertTrue(is_framework(url), url)
        for url in ("https://github.com/persxn/calamity-study.git", "/tmp/origin.git", "https://x.org/calamity-framework-notes"):
            self.assertFalse(is_framework(url), url)


@unittest.skipUnless(shutil.which("git"), "needs git")
class Hooks(unittest.TestCase):
    def setUp(self):
        self.base = tempfile.mkdtemp(prefix="calamity-hooks-")
        self.addCleanup(shutil.rmtree, self.base, True)
        self.clone = os.path.join(self.base, "clone")
        os.makedirs(self.clone)
        self.run_git("init", "-q")
        self.run_git("config", "core.hooksPath", HOOKS)
        write(os.path.join(self.clone, "learner", "README.md"), "what each folder holds\n")
        write(os.path.join(self.clone, "engine.txt"), "framework\n")
        self.run_git("add", "-A")
        self.run_git("commit", "-q", "-m", "framework")

    def run_git(self, *args, expect=0):
        code, out = git(self.clone, *args)
        if expect is not None:
            self.assertEqual(code, expect, "git %s\n%s" % (" ".join(args), out))
        return out

    def stage_record(self):
        write(os.path.join(self.clone, "learner", "profile.md"), "---\nname: Asha\n---\n")
        self.run_git("add", "learner")

    def test_pre_commit_refuses_a_study_record_when_origin_is_the_framework(self):
        self.run_git("remote", "add", "origin", FRAMEWORK_URL)
        self.stage_record()
        out = self.run_git("commit", "-q", "-m", "study log", expect=1)
        self.assertIn("learner/profile.md", out)
        self.assertIn("git restore --staged learner", out)
        self.run_git("restore", "--staged", "learner")
        write(os.path.join(self.clone, "learner", "README.md"), "what each folder holds, and why\n")
        self.run_git("add", "learner/README.md")
        self.run_git("commit", "-q", "-m", "the README ships with the framework")

    def test_pre_commit_allows_the_record_in_the_learners_own_repository(self):
        self.run_git("remote", "add", "origin", "https://github.com/asha/calamity-study.git")
        self.stage_record()
        self.run_git("commit", "-q", "-m", "study log")

    def test_pre_push_refuses_a_study_record_bound_for_the_framework(self):
        framework = os.path.join(self.base, "calamity-framework.git").replace(os.sep, "/")
        study = os.path.join(self.base, "calamity-study.git").replace(os.sep, "/")
        for bare in (framework, study):
            code, out = git(self.base, "init", "-q", "--bare", bare)
            self.assertEqual(code, 0, out)
        self.run_git("remote", "add", "origin", study)
        self.run_git("remote", "add", "upstream", framework)
        self.run_git("push", "-q", "upstream", "main")                # the framework alone goes up
        self.stage_record()
        self.run_git("commit", "-q", "-m", "study log")
        self.run_git("push", "-q", "origin", "main")                  # the record goes to the learner's repository
        out = self.run_git("push", "upstream", "main", expect=1)      # and never to the framework
        self.assertIn("learner/profile.md", out)
        self.run_git("push", "upstream", "main:refs/heads/feature", expect=1)  # nor on a new branch


if __name__ == "__main__":
    unittest.main()
