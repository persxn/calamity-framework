"""framework/scripts/watch.py, the live watch of a coding exercise: one line per real change, nothing else."""
import contextlib
import importlib.util
import io
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

from tests.helpers import REPO

SCRIPT = os.path.join(REPO, "framework", "scripts", "watch.py")


def load():
    spec = importlib.util.spec_from_file_location("calamity_watch", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Watch(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="calamity-watch-")
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.file = os.path.join(self.dir, "lex.c")
        self.mod = load()

    def write(self, text):
        with open(self.file, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)

    def run_polls(self, actions, *args):
        """Run the watcher; each poll first does the next action, and the watch stops after the last one."""
        queue = list(actions)

        def fake_sleep(_seconds):
            if not queue:
                raise KeyboardInterrupt
            queue.pop(0)()

        out = io.StringIO()
        with mock.patch.object(self.mod.time, "sleep", fake_sleep), contextlib.redirect_stdout(out):
            self.assertEqual(self.mod.main([self.file] + list(args)), 0)
        return out.getvalue().splitlines()

    def test_one_line_per_real_change_and_none_for_an_unchanged_save(self):
        self.write("int main(void)\n{\n    return 0;\n}\n")
        lines = self.run_polls([
            lambda: self.write("int main(void)\n{\n    int x\n    return 0;\n}\n"),   # a change
            lambda: self.write("int main(void)\n{\n    int x\n    return 0;\n}\n"),   # saved again, same bytes
            lambda: None,                                                             # nothing at all
            lambda: os.remove(self.file),
            lambda: self.write("x\n"),
        ])
        self.assertIn("watching 1 file(s) every 30s: lex.c", lines[0])
        self.assertEqual(len(lines), 4, lines)
        self.assertIn("changed", lines[1])
        self.assertIn("+1 -0 lines from line 3 (now 5)", lines[1])
        self.assertIn("deleted", lines[2])
        self.assertIn("created", lines[3])

    def test_the_check_joins_the_event(self):
        self.write("a\n")
        check = '"%s" -c "print(\'error: expected ;\'); raise SystemExit(3)"' % sys.executable
        lines = self.run_polls([lambda: self.write("b\n")], "--check", check)
        self.assertEqual(len(lines), 2, lines)
        self.assertIn("check: exit 3: error: expected ;", lines[1])

    def test_a_folder_is_watched_without_build_output(self):
        os.makedirs(os.path.join(self.dir, ".git"))
        for name in ("lex.c", "lex.o", "a.out", os.path.join(".git", "HEAD"), "notes.md~"):
            with open(os.path.join(self.dir, name), "w", encoding="utf-8") as fh:
                fh.write("x\n")
        found = [os.path.basename(p) for p in self.mod.files_under([self.dir])]
        self.assertEqual(found, ["lex.c"])


if __name__ == "__main__":
    unittest.main()
