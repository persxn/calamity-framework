"""Calamity Paper (WP-27): the generated outputs match the tokens, and every callout reaches every output."""
import contextlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest

from tests.helpers import REPO, read

DESIGN = os.path.join(REPO, "framework", "design")


def generator():
    spec = importlib.util.spec_from_file_location("design_tool", os.path.join(REPO, "tools", "design.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Design(unittest.TestCase):
    def test_outputs_match_the_tokens(self):
        self.assertEqual(generator().stale(), [], "run python3 tools/design.py after editing the tokens")

    def test_every_callout_reaches_the_sty_and_the_css(self):
        tokens = json.loads(read(os.path.join(DESIGN, "tokens.json")))
        sty, css = read(os.path.join(DESIGN, "calamity.sty")), read(os.path.join(DESIGN, "calamity.css"))
        for c in tokens["callouts"]:
            self.assertIn("\\cal@callout{%s}" % c["env"], sty, c["env"])
            self.assertIn(".callout.%s" % c["env"], css, c["env"])
            for alias in c.get("aliases", []):
                self.assertIn("\\cal@alias{%s}{%s}" % (alias, c["env"]), sty)
        for name in tokens["palette"]["light"]:
            self.assertRegex(sty, r"\\definecolor\{cal[A-Za-z]+\}\{HTML\}\{%s\}" % tokens["palette"]["light"][name])
        self.assertNotRegex(sty, r"%%[A-Z_]+%%")
        # the names the old notes preamble and mastery-book.sty used still exist
        for old in ("calrule", "calidea", "calwarn", "calcode", "mbAccent", "mbCodeBg"):
            self.assertIn("{%s}" % old, sty)
        # notes use \code{...} inline; a book's listing environment is codeblock, not code
        self.assertIn("\\newcommand{\\code}", sty)
        self.assertNotIn("lstnewenvironment{code}", sty)

    def test_both_themes_and_the_terminal_schemes(self):
        css = read(os.path.join(DESIGN, "calamity.css"))
        self.assertIn("prefers-color-scheme: dark", css)
        self.assertIn(':root[data-theme="dark"]', css)
        schemes = json.loads(read(os.path.join(DESIGN, "calamity-terminal.json")))["schemes"]
        self.assertEqual([s["name"] for s in schemes], ["Calamity Paper Light", "Calamity Paper Dark"])
        for s in schemes:
            self.assertEqual(len([k for k in s if re.match(r"^(bright)?(black|red|green|yellow|blue|purple|cyan|white)$",
                                                        k, re.I)]), 16)
        self.assertTrue(read(os.path.join(DESIGN, "palette.svg")).startswith("<svg"))

    @unittest.skipUnless(shutil.which("tectonic") or shutil.which("pdflatex") or shutil.which("xelatex"),
                         "no TeX engine on this machine")
    def test_the_notebook_builds(self):
        out = tempfile.mkdtemp(prefix="calamity-design-")
        self.addCleanup(shutil.rmtree, out, True)
        mod = generator()
        found = [(n, argv) for n, argv in mod.ENGINES if shutil.which(argv[0])][:1]
        mod.ENGINES = tuple(found)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(mod.qa(out), 0)
        self.assertTrue(os.path.isfile(os.path.join(out, "notebook.%s.pdf" % found[0][0])))


if __name__ == "__main__":
    unittest.main()
