"""Plugin mode (WP-29): the framework as an installed plugin, the learner's repository somewhere else, the engine
reached through bin/calamity. A fresh learner onboards and studies with no clone; the framework copy is untouched."""
import json
import os
import shutil
import subprocess
import tempfile
import unittest

from tests.helpers import REPO, read

SHIM = os.path.join(REPO, "bin", "calamity")


def listing(path):
    out = []
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        out += [os.path.relpath(os.path.join(root, f), path) for f in files]
    return sorted(out)


@unittest.skipIf(os.name == "nt", "the POSIX shim; Windows uses bin/calamity.cmd")
class PluginMode(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="calamity-plugin-")
        self.addCleanup(shutil.rmtree, self.home, True)
        self.learner = os.path.join(self.home, "my-study")
        os.makedirs(self.learner)
        self.env_file = os.path.join(self.home, "claude-env.sh")
        self.env = {k: v for k, v in os.environ.items() if not k.startswith(("CALAMITY_", "CLAUDE_"))}
        self.env.update({"HOME": self.home, "SHELL": "", "CLAUDE_CONFIG_DIR": os.path.join(self.home, ".claude-home")})
        self.before = listing(os.path.join(REPO, "learner"))

    def cal(self, *args, cwd=None, plugin=True, expect=0):
        env = dict(self.env)
        if plugin:                               # what Claude Code sets for the plugin's hooks
            env.update({"CLAUDE_PLUGIN_ROOT": REPO, "CLAUDE_ENV_FILE": self.env_file})
        proc = subprocess.run([SHIM] + list(args), cwd=cwd or self.learner, env=env, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, timeout=300)
        out = proc.stdout.decode("utf-8", "replace")
        self.assertEqual(proc.returncode, expect, out)
        return out

    def test_a_fresh_learner_onboards_and_studies_without_a_clone(self):
        out = self.cal("setup", "--hook", "--permissions")
        self.assertIn("the plugin runs them", out)
        self.assertIn("framework: linked to the plugin's", out)
        self.assertFalse(os.path.exists(os.path.join(self.learner, ".claude", "settings.local.json")))
        settings = json.loads(read(os.path.join(self.learner, ".claude", "settings.json")))
        self.assertIn("Bash(calamity *)", settings["permissions"]["allow"])
        self.assertIn("Read(/learner/items/**)", settings["permissions"]["deny"])
        self.assertTrue(os.path.islink(os.path.join(self.learner, "framework")))
        self.assertIn("/framework", read(os.path.join(self.learner, ".gitignore")))
        self.cal("setup", "--permissions")                                   # again: nothing doubled
        settings = json.loads(read(os.path.join(self.learner, ".claude", "settings.json")))
        self.assertEqual(settings["permissions"]["allow"].count("Bash(calamity *)"), 1)

        self.cal("profile", "set", "name", "Plugin Learner")
        self.cal("profile", "set", "tracks", "10x")
        self.cal("profile", "set", "onboarded", "true")
        self.cal("enroll", "linux-shell", "--force")
        brief = self.cal("brief", "--hook")
        self.assertIn("Learner: Plugin Learner", brief)
        self.assertIn("engine: calamity", brief)
        self.assertIn("export CALAMITY_ROOT=", read(self.env_file))        # the session's shell finds this learner
        self.assertIn(self.learner, read(self.env_file))
        self.assertIn("NEXT:", self.cal("next"))

        sub = os.path.join(self.learner, "notes-in-progress")
        os.makedirs(sub)
        self.assertIn("Plugin Learner", self.cal("profile", "get", "name", cwd=sub, plugin=False))  # found walking up
        self.assertTrue(os.path.isfile(os.path.join(self.learner, "learner", "profile.md")))
        self.assertEqual(listing(os.path.join(REPO, "learner")), self.before)  # the framework copy is untouched

    def test_the_learner_dir_setting_wins_over_the_folder(self):
        elsewhere = os.path.join(self.home, "elsewhere")
        os.makedirs(elsewhere)
        env = dict(self.env, CLAUDE_PLUGIN_OPTION_LEARNER_DIR=self.learner)
        subprocess.run([SHIM, "profile", "set", "name", "Set Learner"], cwd=elsewhere, env=env, check=True,
                       stdout=subprocess.DEVNULL)
        self.assertIn("Set Learner", read(os.path.join(self.learner, "learner", "profile.md")))
        self.assertFalse(os.path.exists(os.path.join(elsewhere, "learner")))

    def test_the_package_declares_what_plugin_mode_needs(self):
        hooks = json.loads(read(os.path.join(REPO, "hooks", "hooks.json")))["hooks"]
        from cal.machine import HOOKS

        self.assertEqual(sorted(hooks), sorted(HOOKS))
        for event, (matcher, args, _) in HOOKS.items():
            command = hooks[event][0]["hooks"][0]["command"]
            self.assertEqual(command, '"${CLAUDE_PLUGIN_ROOT}/bin/calamity" ' + " ".join(args))
            self.assertEqual(hooks[event][0].get("matcher"), matcher)
        manifest = json.loads(read(os.path.join(REPO, ".claude-plugin", "plugin.json")))
        self.assertEqual(manifest["userConfig"]["learner_dir"]["type"], "directory")
        self.assertEqual(manifest["outputStyles"], "./.claude/output-styles/")
        style = read(os.path.join(REPO, ".claude", "output-styles", "calamity-tutor.md"))
        self.assertIn("force-for-plugin: true", style)
        self.assertIn("Rules that do not bend".lower(), style.lower())
        self.assertTrue(os.access(SHIM, os.X_OK))
        self.assertTrue(os.path.isfile(os.path.join(REPO, "bin", "calamity.cmd")))


if __name__ == "__main__":
    unittest.main()
