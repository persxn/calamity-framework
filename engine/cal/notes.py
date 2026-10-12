"""Study notes: per-topic markdown fragments -> LaTeX sections -> one PDF per skill.

Layout, inside learner/notes/<skill>/:
    <topic>.md            fragment saved after a session (idea, example, code, mistakes)
    tex/<topic>.tex       the full section written from the fragment
    main.tex              assembled by this module, in syllabus order (never hand-edited)
    calamity-preamble.tex copied from framework/notes/preamble.tex
    <skill>-notes.pdf     built on demand; needs a TeX engine on the machine

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


def section_path(repo: Repo, tree, key: str) -> str:
    topic = tree.topic(key)
    d = os.path.join(skill_dir(repo, topic.skill), "tex")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, topic.id + ".tex")


def _sha(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha1(fh.read()).hexdigest()


def _stamps_path(repo: Repo, skill_id: str) -> str:
    return os.path.join(skill_dir(repo, skill_id), "tex", "stamps.json")


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
        sect = os.path.join(base, "tex", topic.id + ".tex")
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
    except CalError:
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
        sect = os.path.join(base, "tex", topic.id + ".tex")
        if os.path.isfile(frag) and os.path.isfile(sect):
            stamps[topic.id] = _sha(frag)
            n += 1
    os.makedirs(os.path.join(base, "tex"), exist_ok=True)
    write_text(_stamps_path(repo, skill_id), json.dumps(stamps, indent=1, sort_keys=True) + "\n")
    return "stamped %d section(s) of %s as current" % (n, skill_id)


def assemble(repo: Repo, tree, skill_id: str) -> str:
    """Write main.tex for a skill from the sections that exist, in syllabus order."""
    node = tree.get(skill_id)
    base = skill_dir(repo, skill_id)
    tex_dir = os.path.join(base, "tex")
    have = {name[:-4] for name in os.listdir(tex_dir) if name.endswith(".tex")} if os.path.isdir(tex_dir) else set()
    ordered = [t.id for t in node.topics if t.id in have]
    orphans = sorted(have - {t.id for t in node.topics})
    if not ordered and not orphans:
        raise CalError("no sections written yet for %s (see: notes status %s)" % (skill_id, skill_id))
    preamble = os.path.join(repo.framework, "notes", "preamble.tex")
    if not os.path.isfile(preamble):
        raise CalError("framework/notes/preamble.tex is missing")
    write_text(os.path.join(base, "calamity-preamble.tex"), read_text(preamble))
    learner = repo.prof("name", "")
    lines = [
        "% Assembled by the Calamity engine (notes assemble). Do not edit this file:",
        "% edit the sections in tex/ and assemble again.",
        r"\documentclass[11pt,a4paper]{article}",
        r"\input{calamity-preamble}",
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


def _log_errors(base: str) -> list:
    log = os.path.join(base, "main.log")
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
    assemble(repo, tree, skill_id)
    engine = tex_engine()
    if engine is None:
        return ("main.tex is assembled at %s, but no TeX engine is installed on this machine.\n"
                "Install one (tectonic is the smallest; TeX Live or MiKTeX also work), then run: notes pdf %s"
                % (repo.rel(os.path.join(base, "main.tex")), skill_id))
    name, argv = engine
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
    built = os.path.join(base, "main.pdf")
    if last is None or last.returncode != 0 or not os.path.isfile(built):
        errors = _log_errors(base)
        tail = (last.stdout.decode("utf-8", "replace")[-600:] if last is not None else "")
        msg = ["PDF build failed (%s)." % name]
        msg += ["  " + e for e in errors] or ["  " + tail.strip()]
        if any("not found" in e and (".sty" in e or ".cls" in e or ".def" in e) for e in errors):
            msg.append("This TeX installation lacks a LaTeX package the notes need. Install the recommended LaTeX "
                       "collection (TeX Live: latex-recommended; MiKTeX installs packages on demand) or use Tectonic, "
                       "which fetches what it needs. Then run: notes pdf %s" % skill_id)
        else:
            msg.append("Fix the section named in the error, then run: notes pdf %s" % skill_id)
        raise CalError("\n".join(msg))
    final = os.path.join(base, "%s-notes.pdf" % skill_id.replace(".", "-"))
    shutil.copyfile(built, final)
    pages = ""
    m = re.search(r"\((\d+) pages?", last.stdout.decode("utf-8", "replace"))
    if m:
        pages = ", %s pages" % m.group(1)
    return "built %s with %s%s" % (repo.rel(final), name, pages)
