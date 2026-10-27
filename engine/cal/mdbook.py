"""Study books in Markdown, and a PDF of one without writing LaTeX by hand.

Markdown is the primary format of a study book (`book.format` in the profile; markdown unless the
learner chose pdf): it costs a fraction of the tokens of LaTeX, renders on GitHub and in any editor,
and stays easy to edit. When the learner asks for a PDF, `book pdf <file.md>` turns the Markdown into
LaTeX here, deterministically, and compiles it with the TeX engine `notes` uses (Tectonic, TeX Live or
MiKTeX): no model writes or reviews LaTeX for it.

The subset understood is the one `framework/rules/markdown-books.md` asks books to keep to: headings,
paragraphs, **bold**, *italic*, `code`, links, bullet and numbered lists (nested by two or more
spaces), fenced code blocks (a ```mermaid block is kept as its source), tables, block quotes
(`> **Note**` callouts), horizontal rules, images that exist on disk, and `<details>` blocks (their
summary becomes a bold line). Anything else is printed as text.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile

from .store import read_text, write_text
from .util import CalError

SPECIAL = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_", "{": r"\{",
           "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
PREAMBLE = r"""\documentclass[11pt,a4paper]{article}
\usepackage[margin=2.2cm]{geometry}
\usepackage{fontspec}
\setmainfont{DejaVu Serif}
\setsansfont{DejaVu Sans}
\setmonofont{DejaVu Sans Mono}[Scale=0.86]
\newfontfamily\symbolfont{DejaVu Sans}
\usepackage{xcolor}
\definecolor{ink}{HTML}{1F2933}\definecolor{accent}{HTML}{2F5D8A}\definecolor{paper}{HTML}{F4F6F8}
\color{ink}
\usepackage[hidelinks]{hyperref}
\hypersetup{colorlinks=true,linkcolor=accent,urlcolor=accent}
\usepackage{fancyvrb,fvextra}
\fvset{breaklines=true,breakanywhere=true,fontsize=\small}
\usepackage{longtable,booktabs,array}
\usepackage{graphicx}
\usepackage{enumitem}
\setlist{itemsep=2pt}
\usepackage{mdframed}
\newmdenv[backgroundcolor=paper,linewidth=0pt,innerleftmargin=10pt,innerrightmargin=10pt]{callout}
\usepackage{titlesec}
\titleformat{\section}{\Large\bfseries\color{accent}}{}{0pt}{}
\titleformat{\subsection}{\large\bfseries}{}{0pt}{}
\setlength{\parskip}{6pt}\setlength{\parindent}{0pt}
\title{%(title)s}\date{}
\begin{document}
\maketitle
\tableofcontents
\newpage
"""


def _escape(text: str) -> str:
    out = []
    for ch in text:
        code = ord(ch)
        if ch in SPECIAL:
            out.append(SPECIAL[ch])
        elif code > 0xFFFF or 0xFE00 <= code <= 0xFE0F:
            continue                                  # emoji and variation selectors: no font has them all
        elif 0x2190 <= code <= 0x27BF or 0x2900 <= code <= 0x2BFF:
            out.append(r"{\symbolfont %s}" % ch)      # arrows, ticks, dingbats: the serif lacks some
        else:
            out.append(ch)
    return "".join(out)


INLINE = re.compile(r"(`[^`]+`)|(\*\*[^*]+\*\*)|(\*[^*\s][^*]*\*|_[^_\s][^_]*_)|(\[[^\]]+\]\([^)\s]+\))")


def inline(text: str) -> str:
    """Bold, italic, code and links inside a line; everything else escaped."""
    out, pos = [], 0
    for m in INLINE.finditer(text):
        out.append(_escape(text[pos:m.start()]))
        token = m.group(0)
        if m.group(1):
            out.append(r"\texttt{%s}" % _escape(token[1:-1]))
        elif m.group(2):
            out.append(r"\textbf{%s}" % inline(token[2:-2]))
        elif m.group(3):
            out.append(r"\emph{%s}" % inline(token[1:-1]))
        else:
            label, url = re.match(r"\[([^\]]+)\]\(([^)\s]+)\)", token).groups()
            if url.startswith(("http://", "https://")):
                out.append(r"\href{%s}{%s}" % (url.replace("%", r"\%").replace("#", r"\#"), inline(label)))
            else:
                out.append(inline(label))
        pos = m.end()
    out.append(_escape(text[pos:]))
    return "".join(out)


def _table(rows) -> list:
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    head, body = cells[0], [r for r in cells[2:]]
    n = len(head)
    width = max(0.12, round(0.92 / n, 3))
    spec = "".join(r">{\raggedright\arraybackslash}p{%.3f\linewidth}" % width for _ in range(n))
    lines = [r"\begin{longtable}{%s}" % spec, r"\toprule",
             " & ".join(r"\textbf{%s}" % inline(c) for c in head) + r" \\", r"\midrule", r"\endhead"]
    for r in body:
        r = (r + [""] * n)[:n]
        lines.append(" & ".join(inline(c) for c in r) + r" \\")
    lines += [r"\bottomrule", r"\end{longtable}"]
    return lines


def to_latex(markdown: str, base_dir: str, title: str) -> str:
    lines = markdown.replace("\r\n", "\n").split("\n")
    out = [PREAMBLE % {"title": _escape(title)}]
    para, stack, i = [], [], 0      # stack: the open lists, as (kind, indent)

    def flush():
        if para:
            out.append(inline(" ".join(p.strip() for p in para)) + "\n")
            para.clear()

    def close_lists(indent=-1):
        while stack and stack[-1][1] > indent:
            kind, _ = stack.pop()
            out.append(r"\end{%s}" % kind)

    title_used = False
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        fence = re.match(r"^\s*(```|~~~)\s*([\w+-]*)", line)
        if fence:
            flush()
            close_lists()
            mark, lang = fence.group(1), fence.group(2)
            body, i = [], i + 1
            while i < len(lines) and not lines[i].strip().startswith(mark):
                body.append(lines[i])
                i += 1
            i += 1
            if lang == "mermaid":
                out.append(r"\textit{Diagram (Mermaid source; it renders in a Markdown viewer):}")
            out.append(r"\begin{Verbatim}")
            out.extend(body)
            out.append(r"\end{Verbatim}")
            continue
        if not stripped:
            flush()
            i += 1
            continue
        heading = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", stripped)
        if heading:
            flush()
            close_lists()
            level, text = len(heading.group(1)), heading.group(2)
            if level == 1 and not title_used:
                title_used = True                      # the book's title is the document title
                out[0] = PREAMBLE % {"title": inline(text)}
            else:
                command = {1: "section", 2: "section", 3: "subsection", 4: "subsubsection"}.get(level, "paragraph")
                out.append("\\%s{%s}" % (command, inline(text)))
            i += 1
            continue
        if re.match(r"^\s*([-*_])(\s*\1){2,}\s*$", line):
            flush()
            close_lists()
            out.append(r"\noindent\rule{\linewidth}{0.4pt}")
            i += 1
            continue
        if stripped.startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|?\s*:?-{3,}", lines[i + 1]):
            flush()
            close_lists()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(lines[i])
                i += 1
            out.extend(_table(rows))
            continue
        if stripped.startswith(">"):
            flush()
            close_lists()
            quote = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip()[1:].strip())
                i += 1
            out.append(r"\begin{callout}")
            out.extend(inline(q) + ("\n" if not q else "") for q in quote)
            out.append(r"\end{callout}")
            continue
        details = re.match(r"^\s*<summary>(.*?)</summary>\s*$", line)
        if details:
            flush()
            out.append(r"\textbf{%s}" % inline(details.group(1)))
            i += 1
            continue
        if re.match(r"^\s*</?details>\s*$", line):
            flush()
            i += 1
            continue
        image = re.match(r"^\s*!\[([^\]]*)\]\(([^)\s]+)\)\s*$", line)
        if image:
            flush()
            path = os.path.join(base_dir, image.group(2))
            if os.path.isfile(path) and path.lower().endswith((".png", ".jpg", ".jpeg", ".pdf")):
                out.append(r"\begin{center}\includegraphics[width=0.8\linewidth]{%s}\\\small %s\end{center}"
                           % (os.path.abspath(path).replace("\\", "/"), inline(image.group(1))))
            else:
                out.append(r"\textit{[figure: %s]}" % inline(image.group(1) or image.group(2)))
            i += 1
            continue
        item = re.match(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$", line)
        if item:
            flush()
            indent = len(item.group(1).replace("\t", "    "))
            kind = "enumerate" if item.group(2)[0].isdigit() else "itemize"
            close_lists(indent)
            if not stack or stack[-1][1] < indent:
                out.append(r"\begin{%s}" % kind)
                stack.append((kind, indent))
            text = [item.group(3)]
            i += 1
            while i < len(lines) and lines[i].strip() and not re.match(r"^\s*([-*+]|\d+[.)])\s+", lines[i]) \
                    and len(lines[i]) - len(lines[i].lstrip()) > indent and not lines[i].strip().startswith("```"):
                text.append(lines[i].strip())
                i += 1
            out.append(r"\item " + inline(" ".join(text)))
            continue
        if stack and len(line) - len(line.lstrip()) == 0:
            close_lists()
        para.append(line)
        i += 1
    flush()
    close_lists()
    out.append(r"\end{document}")
    return "\n".join(out) + "\n"


def source(repo, target: str) -> str:
    """A book's Markdown as one file: the file itself, or for a folder its README.md (or index.md) and then its
    chapters in name order, joined into .calamity/tmp/<folder>.md."""
    path = os.path.abspath(target)
    if os.path.isfile(path):
        return path
    if not os.path.isdir(path):
        raise CalError("no such book: %s" % target)
    names = sorted(n for n in os.listdir(path) if n.lower().endswith(".md"))
    first = [n for n in ("README.md", "index.md") if n in names][:1]
    chapters = first + [n for n in names if n not in first]
    if not chapters:
        raise CalError("%s holds no Markdown files" % target)
    joined = "\n\n".join(read_text(os.path.join(path, n)).strip() for n in chapters) + "\n"
    out = os.path.join(repo.local, "tmp", os.path.basename(path.rstrip(os.sep)) + ".md")
    write_text(out, joined)
    return out


def unicode_engine():
    """(name, argv) of a TeX engine that reads Unicode and system fonts (the book uses fontspec), or None."""
    for name, argv in (("tectonic", ["tectonic", "book.tex"]),
                       ("latexmk", ["latexmk", "-xelatex", "-interaction=nonstopmode", "-halt-on-error", "book.tex"]),
                       ("xelatex", ["xelatex", "-interaction=nonstopmode", "-halt-on-error", "book.tex"]),
                       ("lualatex", ["lualatex", "-interaction=nonstopmode", "-halt-on-error", "book.tex"])):
        if shutil.which(argv[0]):
            return name, argv
    return None


def pdf(repo, source: str, out: str | None = None, base: str | None = None) -> str:
    """Compile a Markdown book to PDF next to it (or at `out`; images are looked up from `base`, default the
    file's folder). Returns a one-line report."""
    path = os.path.abspath(source)
    if not os.path.isfile(path) or not path.lower().endswith((".md", ".markdown")):
        raise CalError("give a Markdown file: book pdf learner/mastery/<topic>/book/book.md")
    engine = unicode_engine()
    if not engine:
        raise CalError("no TeX engine that reads Unicode was found (Tectonic, XeLaTeX or LuaLaTeX); the Markdown "
                       "book is complete as it is")
    text = read_text(path)
    first = next((l[2:].strip() for l in text.split("\n") if l.startswith("# ")), os.path.basename(path)[:-3])
    target = os.path.abspath(out) if out else path.rsplit(".", 1)[0] + ".pdf"
    work = tempfile.mkdtemp(prefix="calamity-book-")
    try:
        write_text(os.path.join(work, "book.tex"), to_latex(text, base or os.path.dirname(path), first))
        name, argv = engine
        for _ in range(1 if name in ("tectonic", "latexmk") else 2):   # a second pass fills in the contents
            try:
                proc = subprocess.run(argv, cwd=work, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=600)
            except subprocess.TimeoutExpired:
                raise CalError("%s did not finish within 10 minutes" % name)
            if proc.returncode != 0:
                tail = proc.stdout.decode("utf-8", "replace").strip().split("\n")[-12:]
                raise CalError("%s failed on %s:\n%s" % (name, os.path.basename(path), "\n".join(tail)))
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copyfile(os.path.join(work, "book.pdf"), target)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return "wrote %s (%s)" % (repo.rel(target), name)
