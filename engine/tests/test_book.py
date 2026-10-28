"""Study books in Markdown (the default) and a PDF made from them by the engine."""
import os
import unittest

from tests.helpers import Case, read, write

from cal import mdbook

SECTION = """## Pipes

> **Key idea** — a pipe connects one program's output to the next one's input.

1. `ls` lists files
   - one per line with `-1`
2. `grep` keeps the lines that match

```console
$ ls -1 | grep md
notes.md
```

| Sign | Meaning |
|---|---|
| `|` | pipe |
| `>` | redirect 100% & $5 #1 |

<details>
<summary>Answer</summary>

The shell starts both programs. ✓ 💧
</details>
"""


class Convert(unittest.TestCase):
    def test_the_subset_becomes_latex(self):
        tex = mdbook.to_latex("# The book\n\n" + SECTION, ".", "fallback")
        self.assertIn(r"\title{The book}", tex)
        self.assertIn(r"\section{Pipes}", tex)
        self.assertIn(r"\begin{mdframed}[style=calquote", tex)                # a block quote is a callout
        self.assertIn(r"\usepackage{calamity}", tex)                           # Calamity Paper
        self.assertEqual(mdbook.quote_colour("**Common misconception** — no"), "calAmber")
        self.assertEqual(mdbook.quote_colour("**Note** — yes"), "calSlate")
        self.assertEqual(mdbook.quote_colour("**Key idea**: this"), "calAccent")
        self.assertIn(r"\begin{enumerate}", tex)
        self.assertIn(r"\begin{itemize}", tex)                    # the nested list
        self.assertIn(r"\texttt{ls}", tex)
        self.assertIn("$ ls -1 | grep md", tex)                    # code is kept verbatim
        self.assertIn(r"\begin{longtable}", tex)
        self.assertIn(r"100\% \& \$5 \#1", tex)                    # escaped outside code
        self.assertIn(r"\textbf{Answer}", tex)
        self.assertIn(r"{\symbolfont ✓}", tex)
        self.assertNotIn("💧", tex)                               # no font has every emoji
        self.assertTrue(tex.rstrip().endswith(r"\end{document}"))
        self.assertEqual(tex.count(r"\begin{enumerate}"), tex.count(r"\end{enumerate}"))
        self.assertEqual(tex.count(r"\begin{itemize}"), tex.count(r"\end{itemize}"))

    def test_links_and_missing_images(self):
        tex = mdbook.inline("see [the docs](https://example.com/a_b#c) and [a file](notes.md)")
        self.assertIn(r"\href{https://example.com/a_b\#c}{the docs}", tex)
        self.assertIn("a file", tex)
        self.assertIn(r"\textit{[figure: a diagram]}", mdbook.to_latex("![a diagram](missing.png)\n", ".", "t"))


class Book(Case):
    def setUp(self):
        super().setUp()
        self.sb.onboard()

    def test_the_format_is_asked_once_and_validated(self):
        sb = self.sb
        self.assertIn("Study books: format not chosen", sb.run("brief"))
        sb.run("profile", "set", "book.format", "epub", expect=2)
        sb.run("profile", "set", "book.format", "markdown")
        self.assertNotIn("Study books", sb.run("brief"))

    def test_markdown_sections_are_the_default_book(self):
        sb = self.sb
        sb.run("enroll", "shell")
        path = sb.run("notes", "section", "shell/pipes").strip().split()[-1]
        self.assertTrue(path.endswith("md/pipes.md"), path)
        write(sb.path("learner", "notes", "shell", "pipes.md"), "---\ntopic: shell/pipes\n---\n## Idea\npipes\n")
        write(sb.path("learner", "notes", "shell", "md", "pipes.md"), SECTION)
        self.assertIn("to write", sb.run("notes", "status", "shell").replace("stale", "to write"))
        sb.run("notes", "stamp", "shell")
        self.assertIn("ok", sb.run("notes", "status", "shell"))
        out = sb.run("notes", "assemble", "shell")
        book = read(sb.path("learner", "notes", "shell", "shell-notes.md"))
        self.assertIn("shell-notes.md", out)
        self.assertIn("# Shell", book)
        self.assertIn("## Contents", book)
        self.assertIn("## Pipes", book)
        self.assertFalse(os.path.exists(sb.path("learner", "notes", "shell", "main.tex")))

    @unittest.skipUnless(mdbook.unicode_engine(), "needs Tectonic, XeLaTeX or LuaLaTeX")
    def test_a_book_folder_becomes_a_pdf(self):
        sb = self.sb
        book = sb.path("learner", "mastery", "linux", "book")
        write(os.path.join(book, "README.md"), "# Linux\n\nFrom the kernel up.\n")
        write(os.path.join(book, "01-pipes.md"), SECTION)
        self.assertIn("book.pdf", sb.run("book", "pdf", book))
        self.assertTrue(os.path.getsize(os.path.join(book, "book.pdf")) > 1000)
        self.assertEqual(os.listdir(sb.path(".calamity", "tmp")), [])     # the joined copy is gone

    def test_no_engine_says_the_markdown_is_the_book(self):
        sb = self.sb
        write(sb.path("learner", "b.md"), "# B\n")
        saved = mdbook.unicode_engine
        mdbook.unicode_engine = lambda: None
        try:
            sb.run("book", "pdf", sb.path("learner", "b.md"), expect=2)
        finally:
            mdbook.unicode_engine = saved
        self.assertIn("complete as it is", sb.err)
        sb.run("book", "pdf", sb.path("learner", "missing"), expect=2)
        sb.run("enroll", "shell")
        write(sb.path("learner", "notes", "shell", "md", "pipes.md"), SECTION)
        mdbook.unicode_engine = lambda: None
        try:
            out = sb.run("notes", "pdf", "shell")              # no engine: the Markdown book, and how to get a PDF
        finally:
            mdbook.unicode_engine = saved
        self.assertIn("shell-notes.md is assembled (the Markdown is the book)", out)
