"""Study notes: per-topic markdown fragments -> long-form sections -> one book per skill.

Layout, inside learner/notes/<skill>/:
    <topic>.md            fragment saved after a session (idea, example, code, mistakes)
    md/<topic>.md         the full section in Markdown (book.format markdown, the default)
    tex/<topic>.tex       ... or in LaTeX (book.format pdf)
    <skill>-notes.md      assembled from md/, in syllabus order (never hand-edited)
    main.tex              assembled from tex/ (never hand-edited)
    calamity.sty          copied from framework/design/calamity.sty (Calamity Paper, notebook option)
    <skill>-notes.pdf     built on demand; needs a TeX engine on the machine
    cheatsheet.tex        one revision page, by the notes-writer; notes cheatsheet builds <skill>-cheatsheet.pdf

The writing is done by the tutor and the notes-writer agent. This module only
keeps the structure straight: paths, order, staleness, assembly, compilation.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess

from . import fm
from .store import Repo, read_text, write_text
from .util import CalError, now, table

_TEX_SPECIAL = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_",
                "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
FRAGMENT_SKELETON = """## Idea

## Worked example

## My code

## Mistakes I made

## Recall prompts
"""


def tex_escape(text: str) -> str:
    return "".join(_TEX_SPECIAL.get(ch, ch) for ch in str(text))


def skill_dir(repo: Repo, skill_id: str) -> str:
    return os.path.join(repo.notes_dir, skill_id)


def fragment_path(repo: Repo, tree, key: str, create: bool = True) -> str:
    topic = tree.topic(key)
    path = os.path.join(skill_dir(repo, topic.skill), topic.id + ".md")
    if create and not os.path.isfile(path):
        meta = {"topic": topic.key, "title": topic.title, "updated": now().date().isoformat()}
        write_text(path, fm.dump(meta, FRAGMENT_SKELETON))
    return path


def kind(repo: Repo) -> tuple:
    """(folder, extension) of long-form sections: Markdown unless the learner chose PDF (book.format)."""
    return ("tex", ".tex") if repo.prof("book.format") == "pdf" else ("md", ".md")


def section_path(repo: Repo, tree, key: str) -> str:
    topic = tree.topic(key)
    folder, ext = kind(repo)
    d = os.path.join(skill_dir(repo, topic.skill), folder)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, topic.id + ext)


def _sha(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha1(fh.read()).hexdigest()


def _stamps_path(repo: Repo, skill_id: str) -> str:
    return os.path.join(skill_dir(repo, skill_id), kind(repo)[0], "stamps.json")


def _stamps(repo: Repo, skill_id: str) -> dict:
    try:
        with open(_stamps_path(repo, skill_id), "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def rows(repo: Repo, tree, skill_id: str) -> list:
    """One row per topic: {topic, title, fragment, section, state}."""
    node = tree.get(skill_id)
    base = skill_dir(repo, skill_id)
    stamps = _stamps(repo, skill_id)
    out = []
    for topic in node.topics:
        frag = os.path.join(base, topic.id + ".md")
        folder, ext = kind(repo)
        sect = os.path.join(base, folder, topic.id + ext)
        has_f, has_s = os.path.isfile(frag), os.path.isfile(sect)
        if has_f and _is_blank_fragment(frag):
            has_f = False
        if not has_f and not has_s:
            state = "-"
        elif has_f and not has_s:
            state = "to write"
        elif has_s and not has_f:
            state = "ok"
        elif stamps.get(topic.id) == _sha(frag):
            state = "ok"
        else:
            state = "stale"
        out.append({"topic": topic.id, "title": topic.title, "fragment": has_f, "section": has_s, "state": state})
    return out


def _is_blank_fragment(path: str) -> bool:
    try:
        _, body = fm.parse(read_text(path))
    except (CalError, UnicodeDecodeError):
        return False
    text = re.sub(r"^#+ .*$", "", body, flags=re.M)
    return not text.strip()


def status_text(repo: Repo, tree, skill_id: str | None = None) -> str:
    if skill_id is None:
        if not os.path.isdir(repo.notes_dir):
            return "No notes yet. Fragments are saved with: notes fragment <skill>/<topic>"
        lines = []
        for name in sorted(os.listdir(repo.notes_dir)):
            if name in tree.nodes and os.path.isdir(os.path.join(repo.notes_dir, name)):
                r = rows(repo, tree, name)
                todo = sum(1 for x in r if x["state"] in ("to write", "stale"))
                lines.append("%s: %d fragment(s), %d section(s), %d to (re)write" % (
                    name, sum(1 for x in r if x["fragment"]), sum(1 for x in r if x["section"]), todo))
        return "\n".join(lines) or "No notes yet."
    r = rows(repo, tree, skill_id)
    if not r:
        return "%s has no topics yet." % skill_id
    body = [[x["topic"], "yes" if x["fragment"] else "", "yes" if x["section"] else "", x["state"]] for x in r]
    out = [table(body, ["topic", "fragment", "section", "state"])]
    todo = [x["topic"] for x in r if x["state"] in ("to write", "stale")]
    if todo:
        out.append("sections to (re)write from their fragments: %s" % ", ".join(todo))
        out.append("after writing them: notes stamp %s , then: notes pdf %s" % (skill_id, skill_id))
    return "\n".join(out)


def stamp(repo: Repo, tree, skill_id: str) -> str:
    """Record that every existing section is up to date with its fragment."""
    node = tree.get(skill_id)
    base = skill_dir(repo, skill_id)
    stamps = _stamps(repo, skill_id)
    n = 0
    for topic in node.topics:
        frag = os.path.join(base, topic.id + ".md")
        folder, ext = kind(repo)
        sect = os.path.join(base, folder, topic.id + ext)
        if os.path.isfile(frag) and os.path.isfile(sect):
            stamps[topic.id] = _sha(frag)
            n += 1
    os.makedirs(os.path.join(base, kind(repo)[0]), exist_ok=True)
    write_text(_stamps_path(repo, skill_id), json.dumps(stamps, indent=1, sort_keys=True) + "\n")
    return "stamped %d section(s) of %s as current" % (n, skill_id)


def assemble_markdown(repo: Repo, tree, skill_id: str) -> str:
    """Write <skill>-notes.md from the Markdown sections that exist, in syllabus order, with a contents list."""
    node = tree.get(skill_id)
    base = skill_dir(repo, skill_id)
    md_dir = os.path.join(base, "md")
    have = {n[:-3] for n in os.listdir(md_dir) if n.endswith(".md")} if os.path.isdir(md_dir) else set()
    ordered = [t for t in node.topics if t.id in have]
    orphans = sorted(have - {t.id for t in node.topics})
    if not ordered and not orphans:
        raise CalError("no sections written yet for %s (see: notes status %s)" % (skill_id, skill_id))
    learner = repo.prof_text("name")
    parts = ["<!-- Assembled by the Calamity engine (notes assemble). Edit the sections in md/, then assemble again. -->",
             "", "# %s" % node.title, "",
             "*Study notes%s · %s*" % ((" of " + learner) if learner else "", now().strftime("%d %B %Y")), "",
             "## Contents", ""]
    parts += ["- %s" % t.title for t in ordered] + (["- Earlier notes"] if orphans else []) + [""]
    for tid in [t.id for t in ordered] + orphans:
        text = read_text(os.path.join(md_dir, tid + ".md"))
        if text.startswith("---"):
            _, text, _ = fm.split(text)            # a section's own front matter stays out of the book
        parts += [text.strip(), ""]
    path = os.path.join(base, "%s-notes.md" % skill_id)
    write_text(path, "\n".join(parts).rstrip("\n") + "\n")
    return path


def assemble(repo: Repo, tree, skill_id: str) -> str:
    """Write the skill's book from the sections that exist, in syllabus order: <skill>-notes.md for Markdown
    sections, main.tex for LaTeX ones."""
    if kind(repo)[0] == "md":
        return assemble_markdown(repo, tree, skill_id)
    node = tree.get(skill_id)
    base = skill_dir(repo, skill_id)
    tex_dir = os.path.join(base, "tex")
    have = {name[:-4] for name in os.listdir(tex_dir) if name.endswith(".tex")} if os.path.isdir(tex_dir) else set()
    ordered = [t.id for t in node.topics if t.id in have]
    orphans = sorted(have - {t.id for t in node.topics})
    if not ordered and not orphans:
        raise CalError("no sections written yet for %s (see: notes status %s)" % (skill_id, skill_id))
    style = os.path.join(repo.framework, "design", "calamity.sty")
    if not os.path.isfile(style):
        raise CalError("framework/design/calamity.sty is missing")
    write_text(os.path.join(base, "calamity.sty"), read_text(style))
    stale = os.path.join(base, "calamity-preamble.tex")      # the preamble before Calamity Paper (WP-27)
    if os.path.isfile(stale):
        os.remove(stale)
    learner = repo.prof_text("name")
    lines = [
        "% Assembled by the Calamity engine (notes assemble). Do not edit this file:",
        "% edit the sections in tex/ and assemble again.",
        r"\documentclass[11pt,a4paper]{article}",
        r"\usepackage{calamity}",
        r"\title{%s}" % tex_escape(node.title),
        r"\author{%s}" % (tex_escape(learner) + r" \\ \small study notes" if learner else "Study notes"),
        r"\date{%s}" % now().strftime("%d %B %Y"),
        r"\begin{document}",
        r"\maketitle",
        r"\tableofcontents",
        r"\newpage",
    ]
    for tid in ordered:
        lines.append(r"\input{tex/%s}" % tid)
    if orphans:
        lines.append(r"\appendix")
        lines.append(r"\section{Earlier notes}")
        for tid in orphans:
            lines.append(r"\input{tex/%s}" % tid)
    lines.append(r"\end{document}")
    path = os.path.join(base, "main.tex")
    write_text(path, "\n".join(lines) + "\n")
    return path


def tex_engine():
    """(name, argv-prefix) of the first TeX engine found on this machine, or None."""
    for name, argv in (
        ("tectonic", ["tectonic", "--keep-logs", "main.tex"]),
        ("latexmk", ["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", "-no-shell-escape", "main.tex"]),
        ("pdflatex", ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "-no-shell-escape", "main.tex"]),
        ("xelatex", ["xelatex", "-interaction=nonstopmode", "-halt-on-error", "-no-shell-escape", "main.tex"]),
        ("lualatex", ["lualatex", "-interaction=nonstopmode", "-halt-on-error", "-no-shell-escape", "main.tex"]),
    ):
        if shutil.which(argv[0]):
            return name, argv
    return None


def _log_errors(base: str, stem: str = "main") -> list:
    log = os.path.join(base, "%s.log" % stem)
    if not os.path.isfile(log):
        return []
    try:
        with open(log, "r", encoding="utf-8", errors="replace") as fh:
            lines = fh.read().split("\n")
    except OSError:
        return []
    found = []
    for i, line in enumerate(lines):
        if line.startswith("!"):
            context = [l for l in lines[i + 1 : i + 6] if l.startswith("l.") or "tex/" in l]
            found.append((line + (" | " + context[0].strip() if context else "")).strip())
        if len(found) >= 4:
            break
    return found


def pdf(repo: Repo, tree, skill_id: str) -> str:
    base = skill_dir(repo, skill_id)
    if kind(repo)[0] == "md":                      # the Markdown book, converted by the engine (no LaTeX to write)
        from . import mdbook

        book = assemble_markdown(repo, tree, skill_id)
        if mdbook.unicode_engine() is None:      # the Markdown is the book; a PDF waits for a TeX engine
            return ("%s is assembled (the Markdown is the book), but no TeX engine that reads Unicode is installed "
                    "on this machine for a PDF.\nInstall one (tectonic is the smallest; TeX Live or MiKTeX also "
                    "work), then run: notes pdf %s" % (repo.rel(book), skill_id))
        return mdbook.pdf(repo, book, os.path.join(base, "%s-notes.pdf" % skill_id))
    assemble(repo, tree, skill_id)
    engine = tex_engine()
    if engine is None:
        return ("main.tex is assembled at %s, but no TeX engine is installed on this machine.\n"
                "Install one (tectonic is the smallest; TeX Live or MiKTeX also work), then run: notes pdf %s"
                % (repo.rel(os.path.join(base, "main.tex")), skill_id))
    final = os.path.join(base, "%s-notes.pdf" % skill_id.replace(".", "-"))
    name, pages = _compile(repo, base, "main", engine, final, "notes pdf %s" % skill_id)
    return "built %s with %s%s" % (repo.rel(final), name, (", %d pages" % pages) if pages else "")


def _compile(repo: Repo, base: str, stem: str, engine, final: str, again: str):
    """Compile <base>/<stem>.tex with the engine found and copy the PDF to `final`. Returns (engine, pages or None);
    raises CalError with the first errors from the log."""
    name, argv = engine
    argv = [("%s.tex" % stem) if arg == "main.tex" else arg for arg in argv]   # tex_engine() names main.tex
    passes = 1 if name in ("tectonic", "latexmk") else 2
    last = None
    for _ in range(passes):
        try:
            last = subprocess.run(argv, cwd=base, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=300)
        except subprocess.TimeoutExpired:
            raise CalError("%s did not finish within 5 minutes" % name)
        except OSError as exc:
            raise CalError("could not run %s: %s" % (name, exc))
        if last.returncode != 0:
            break
    built = os.path.join(base, "%s.pdf" % stem)
    if last is None or last.returncode != 0 or not os.path.isfile(built):
        errors = _log_errors(base, stem)
        tail = (last.stdout.decode("utf-8", "replace")[-600:] if last is not None else "")
        msg = ["PDF build failed (%s)." % name]
        msg += ["  " + e for e in errors] or ["  " + tail.strip()]
        if any("not found" in e and (".sty" in e or ".cls" in e or ".def" in e) for e in errors):
            msg.append("This TeX installation lacks a LaTeX package the notes need. Install the recommended LaTeX "
                       "collection (TeX Live: latex-recommended; MiKTeX installs packages on demand) or use Tectonic, "
                       "which fetches what it needs. Then run: %s" % again)
        else:
            msg.append("Fix the section named in the error, then run: %s" % again)
        raise CalError("\n".join(msg))
    try:
        shutil.copyfile(built, final)
    except OSError as exc:  # on Windows, a PDF viewer holding the old file open blocks the copy
        raise CalError("the PDF was built (%s) but could not be copied to %s: %s. If it is open in a PDF "
                       "viewer, close it and run: %s" % (repo.rel(built), repo.rel(final), exc.strerror or exc, again))
    m = re.search(r"\((\d+) pages?", last.stdout.decode("utf-8", "replace"))
    if not m:
        log = os.path.join(base, "%s.log" % stem)
        try:
            with open(log, "r", encoding="utf-8", errors="replace") as fh:
                m = re.search(r"\((\d+) pages?", fh.read())
        except OSError:
            m = None
    return name, (int(m.group(1)) if m else None)


SHEET = "cheatsheet.tex"


def cheatsheet(repo: Repo, tree, skill_id: str) -> str:
    """One landscape page for revision: the notes-writer's cheatsheet.tex in the cheatsheet option of calamity.sty."""
    node = tree.get(skill_id)
    base = skill_dir(repo, skill_id)
    body = os.path.join(base, SHEET)
    if not os.path.isfile(body):
        raise CalError("no cheat sheet yet: ask the notes-writer agent for one (\"cheat sheet for %s\"); it writes %s"
                       % (skill_id, repo.rel(body)))
    style = os.path.join(repo.framework, "design", "calamity.sty")
    if not os.path.isfile(style):
        raise CalError("framework/design/calamity.sty is missing")
    write_text(os.path.join(base, "calamity.sty"), read_text(style))
    learner = repo.prof_text("name")
    lines = [
        "% Assembled by the Calamity engine (notes cheatsheet). Do not edit: edit cheatsheet.tex.",
        r"\documentclass[10pt]{article}",
        r"\usepackage[cheatsheet]{calamity}",
        r"\begin{document}",
        r"\noindent{\sffamily\bfseries\large %s \textperiodcentered{} cheat sheet}\hfill"
        r"{\sffamily\small\color{calMuted}%s%s}\par\vspace{2pt}{\color{calRule}\hrule}\vspace{4pt}"
        % (tex_escape(node.title), (tex_escape(learner) + r" \textperiodcentered{} ") if learner else "",
           now().strftime("%d %B %Y")),
        r"\begin{multicols*}{3}",
        r"\input{cheatsheet}",
        r"\end{multicols*}",
        r"\end{document}",
    ]
    write_text(os.path.join(base, "cheatsheet-main.tex"), "\n".join(lines) + "\n")
    engine = tex_engine()
    if engine is None:
        return ("cheatsheet-main.tex is assembled at %s, but no TeX engine is installed on this machine.\n"
                "Install one (tectonic is the smallest), then run: notes cheatsheet %s"
                % (repo.rel(base), skill_id))
    final = os.path.join(base, "%s-cheatsheet.pdf" % skill_id.replace(".", "-"))
    name, pages = _compile(repo, base, "cheatsheet-main", engine, final, "notes cheatsheet %s" % skill_id)
    out = "built %s with %s%s" % (repo.rel(final), name, (", %d pages" % pages) if pages else "")
    if pages and pages > 1:
        out += ("\nA cheat sheet is one page: this one runs to %d. Ask the notes-writer to cut %s to what is looked "
                "up during revision, then run notes cheatsheet %s again." % (pages, SHEET, skill_id))
    return out
