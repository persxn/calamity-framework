import os
import unittest

from tests.helpers import Case, write

from cal import notes

SECTION = r"""\section{%(title)s}\label{sec:docker:%(topic)s}

\begin{keyidea}
An image is a read-only template; a container is a running instance of one. 100\%% of this is \code{docker_run --rm}.
\end{keyidea}

\begin{example}
Build, then run.
\begin{lstlisting}[language=Dockerfile]
FROM alpine:3.20
CMD ["echo", "hello"]
\end{lstlisting}
\end{example}

\begin{pitfall}
Forgetting \code{--rm} leaves stopped containers behind.
\end{pitfall}

\begin{mistakes}
\item Confused the image id with the container id.
\end{mistakes}

\begin{recall}
\item What is the difference between an image and a container?
\end{recall}
"""


class Notes(Case):
    def setUp(self):
        super().setUp()
        self.sb.onboard()

    def test_fragment_and_status(self):
        sb = self.sb
        self.assertIn("No notes yet", sb.run("notes", "status"))
        rel = sb.run("notes", "fragment", "docker/images").strip()
        self.assertEqual(rel, "learner/notes/docker/images.md")
        with open(sb.path(rel), "r", encoding="utf-8") as fh:
            text = fh.read()
        for part in ("topic: docker/images", "## Idea", "## Worked example", "## My code", "## Mistakes I made",
                     "## Recall prompts"):
            self.assertIn(part, text)
        status = sb.run("notes", "status", "docker")
        self.assertNotIn("to write", status)                     # an untouched skeleton is not a fragment yet
        with open(sb.path(rel), "a", encoding="utf-8") as fh:
            fh.write("\nAn image is a template; a container runs it.\n")
        sb.run("notes", "fragment", "docker/images")             # asking again never overwrites
        with open(sb.path(rel), "r", encoding="utf-8") as fh:
            self.assertIn("An image is a template", fh.read())
        status = sb.run("notes", "status", "docker")
        self.assertIn("to write", status)
        self.assertIn("sections to (re)write from their fragments: images", status)
        self.assertIn("docker: 1 fragment(s), 0 section(s), 1 to (re)write", sb.run("notes", "status"))
        sb.run("notes", "fragment", "docker/nope", expect=2)
        sb.run("notes", "fragment", expect=2)

    def test_sections_stamps_and_staleness(self):
        sb = self.sb
        frag = sb.path(sb.run("notes", "fragment", "docker/images").strip())
        with open(frag, "a", encoding="utf-8") as fh:
            fh.write("\nfirst version\n")
        sect = sb.path(sb.run("notes", "section", "docker/images").strip())
        self.assertTrue(sect.replace(os.sep, "/").endswith("learner/notes/docker/tex/images.tex"))
        write(sect, SECTION % {"title": "Images and containers", "topic": "images"})
        self.assertIn("stale", sb.run("notes", "status", "docker"))     # written, but not stamped as current
        self.assertIn("stamped 1 section(s)", sb.run("notes", "stamp", "docker"))
        rows = [line.split() for line in sb.run("notes", "status", "docker").split("\n")]
        self.assertIn(["images", "yes", "yes", "ok"], rows)
        with open(frag, "a", encoding="utf-8") as fh:
            fh.write("\nlearnt something new today\n")
        self.assertIn("stale", sb.run("notes", "status", "docker"))     # the fragment moved on

    def test_assemble_orders_by_syllabus(self):
        sb = self.sb
        sb.run("notes", "assemble", "docker", expect=2)                  # nothing written yet
        for topic in ("multi-stage", "images", "old-topic"):
            write(sb.path("learner", "notes", "docker", "tex", topic + ".tex"),
                  SECTION % {"title": topic, "topic": topic})
        out = sb.run("notes", "assemble", "docker")
        self.assertIn("assembled: learner/notes/docker/main.tex", out)
        with open(sb.path("learner", "notes", "docker", "main.tex"), "r", encoding="utf-8") as fh:
            main = fh.read()
        self.assertLess(main.index(r"\input{tex/images}"), main.index(r"\input{tex/multi-stage}"))
        self.assertLess(main.index(r"\appendix"), main.index(r"\input{tex/old-topic}"))  # no longer in the syllabus
        self.assertIn(r"\title{Docker}", main)
        self.assertIn(r"\author{Tester", main)
        self.assertTrue(os.path.isfile(sb.path("learner", "notes", "docker", "calamity-preamble.tex")))

    def test_tex_escape(self):
        self.assertEqual(notes.tex_escape("50% of A&B_c #1 {x} ~ ^ \\ $"),
                         r"50\% of A\&B\_c \#1 \{x\} \textasciitilde{} \textasciicircum{} \textbackslash{} \$")

    @unittest.skipUnless(notes.tex_engine(), "no TeX engine on this machine")
    def test_pdf_build(self):
        sb = self.sb
        for topic, title in (("images", "Images and containers"), ("dockerfile", "Writing a Dockerfile")):
            write(sb.path("learner", "notes", "docker", "tex", topic + ".tex"), SECTION % {"title": title, "topic": topic})
        out = sb.run("notes", "pdf", "docker", expect=None)
        if sb.code != 0 and ("lacks a LaTeX package" in sb.err or "tectonic" in sb.err.lower()):
            self.skipTest("the TeX installation on this machine cannot build the sample: " + sb.err.strip()[:200])
        self.assertEqual(sb.code, 0, sb.err)
        self.assertIn("built learner/notes/docker/docker-notes.pdf", out)
        pdf = sb.path("learner", "notes", "docker", "docker-notes.pdf")
        with open(pdf, "rb") as fh:
            self.assertEqual(fh.read(5), b"%PDF-")
        self.assertGreater(os.path.getsize(pdf), 10000)
        # a broken section is reported with its file and line, not as a wall of log
        write(sb.path("learner", "notes", "docker", "tex", "images.tex"), "\\section{Broken}\n\\undefinedmacro here\n")
        failed = sb.run("notes", "pdf", "docker", expect=None) + sb.err
        self.assertEqual(sb.code, 2)
        self.assertIn("PDF build failed", failed)
        self.assertIn("Undefined control sequence", failed)

    def test_pdf_without_a_tex_engine(self):
        sb = self.sb
        write(sb.path("learner", "notes", "docker", "tex", "images.tex"), SECTION % {"title": "Images", "topic": "images"})
        original = notes.tex_engine
        notes.tex_engine = lambda: None
        try:
            out = sb.run("notes", "pdf", "docker")
        finally:
            notes.tex_engine = original
        self.assertIn("no TeX engine is installed", out)
        self.assertTrue(os.path.isfile(sb.path("learner", "notes", "docker", "main.tex")))

    def test_skill_ids_with_dots(self):
        sb = self.sb
        rel = sb.run("notes", "fragment", "gate.cs.os/deadlock").strip()
        self.assertEqual(rel, "learner/notes/gate.cs.os/deadlock.md")
        self.assertIn("deadlock", sb.run("find", "deadlock"))


if __name__ == "__main__":
    unittest.main()
