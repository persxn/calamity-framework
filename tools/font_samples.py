"""Font samples for the Calamity Paper design system (WP-27, decision D12): the same notes page set in each
candidate family, so the learner chooses from what they see.

    python3 tools/font_samples.py --out <folder outside the checkout> [--set libertinus ...]

Each set is a body face, a heading face, a code face and a maths face, all OpenType fonts shipped with
TeX Live (and so in Tectonic's bundle), each with a pdfLaTeX package of the same design for the
notebook's pdfLaTeX route. The page holds what the notes and books hold: headings, body text with
inline code and terms, a definition, a key idea and a pitfall box, display maths of the kind GATE
asks, a table, a code listing and recall questions.

Built with every engine found: Tectonic, then XeLaTeX and LuaLaTeX from TeX Live. Writes
<set>.<engine>.pdf, a PNG of each page when pdftoppm is installed, and font-samples.pdf (one page per
set, the first engine that built it) when pdfunite is. Standard library only.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

# id: (name, body, sans, mono, maths, pdfLaTeX packages, one line on its character)
SETS = {
    "latin-modern": ("Latin Modern (today's notes)",
                     ("lmroman10", "-regular", "-bold", "-italic", "-bolditalic"),
                     ("lmsans10", "-regular", "-bold", "-oblique", "-boldoblique"),
                     ("lmmono10", "-regular", "-regular", "-italic", "-italic"),
                     "latinmodern-math.otf", "lmodern",
                     "the classic TeX look; thin strokes, wide; what the notes use now"),
    "libertinus": ("Libertinus",
                   ("LibertinusSerif", "-Regular", "-Bold", "-Italic", "-BoldItalic"),
                   ("LibertinusSans", "-Regular", "-Bold", "-Italic", "-Regular"),
                   ("Inconsolatazi4", "-Regular", "-Bold", "-Regular", "-Bold"),
                   "LibertinusMath-Regular.otf", "libertinus, inconsolata",
                   "warm book serif with a matching sans and maths; compact"),
    "stix-two": ("STIX Two with Source Sans and Source Code",
                 ("STIXTwoText", "-Regular", "-Bold", "-Italic", "-BoldItalic"),
                 ("SourceSansPro", "-Regular", "-Bold", "-RegularIt", "-BoldIt"),
                 ("SourceCodePro", "-Regular", "-Bold", "-RegularIt", "-BoldIt"),
                 "STIXTwoMath-Regular.otf", "stix2, sourcesanspro, sourcecodepro",
                 "a scientific-journal Times; the most complete maths"),
    "charter": ("Charter with Fira Sans and Fira Mono",
                ("XCharter", "-Roman", "-Bold", "-Italic", "-BoldItalic"),
                ("FiraSans", "-Regular", "-SemiBold", "-Italic", "-SemiBoldItalic"),
                ("FiraMono", "-Regular", "-Bold", "-Regular", "-Bold"),
                "XCharter-Math.otf", "XCharter, FiraSans, FiraMono",
                "sturdy, open serif made for low-resolution output; very readable on screens and print"),
    "pagella": ("Palatino (TeX Gyre Pagella) with Source Sans",
                ("texgyrepagella", "-regular", "-bold", "-italic", "-bolditalic"),
                ("SourceSansPro", "-Regular", "-Bold", "-RegularIt", "-BoldIt"),
                ("Inconsolatazi4", "-Regular", "-Bold", "-Regular", "-Bold"),
                "texgyrepagella-math.otf", "newpxtext, newpxmath, sourcesanspro, inconsolata",
                "calligraphic, elegant textbook serif; a little wider"),
    "fira": ("Fira (sans throughout)",
             ("FiraSans", "-Regular", "-SemiBold", "-Italic", "-SemiBoldItalic"),
             ("FiraSans", "-Regular", "-Bold", "-Italic", "-BoldItalic"),
             ("FiraMono", "-Regular", "-Bold", "-Regular", "-Bold"),
             "FiraMath-Regular.otf", "FiraSans, FiraMono, firamath-otf (no pdfLaTeX maths: XeLaTeX or LuaLaTeX only)",
             "a screen-first sans for body and maths; modern, like slides and docs sites"),
}

PREAMBLE = r"""\documentclass[11pt]{article}
\usepackage[a4paper,hmargin=2.0cm,top=1.7cm,bottom=1.6cm,headheight=14pt,headsep=8pt]{geometry}
\usepackage{fontspec}
\usepackage{amsmath}
\usepackage{unicode-math}
\setmainfont{%(body)s}[Extension=.otf,UprightFont=*%(b_r)s,BoldFont=*%(b_b)s,ItalicFont=*%(b_i)s,BoldItalicFont=*%(b_bi)s]
\setsansfont{%(sans)s}[Extension=.otf,UprightFont=*%(s_r)s,BoldFont=*%(s_b)s,ItalicFont=*%(s_i)s,BoldItalicFont=*%(s_bi)s]
\setmonofont{%(mono)s}[Extension=.otf,UprightFont=*%(m_r)s,BoldFont=*%(m_b)s,ItalicFont=*%(m_i)s,BoldItalicFont=*%(m_bi)s,Scale=MatchLowercase]
\setmathfont{%(math)s}
\usepackage{xcolor}
\usepackage{booktabs}
\usepackage{listings}
\usepackage[most]{tcolorbox}
\usepackage{fancyhdr}
\usepackage{titlesec}
\usepackage{enumitem}
\definecolor{calink}{HTML}{1F2328}
\definecolor{calrule}{HTML}{8A8F98}
\definecolor{calidea}{HTML}{EEF3FB}
\definecolor{calideaedge}{HTML}{1F4E8C}
\definecolor{calwarn}{HTML}{FBF1E6}
\definecolor{calwarnedge}{HTML}{A4511B}
\definecolor{caldef}{HTML}{F2F6F1}
\definecolor{caldefedge}{HTML}{3B6E3B}
\definecolor{calcode}{HTML}{F6F6F4}
\definecolor{calkey}{HTML}{1F4E8C}
\definecolor{calstr}{HTML}{8A3B12}
\definecolor{calcom}{HTML}{5F6B5F}
\color{calink}
\setlength{\parindent}{0pt}
\setlength{\parskip}{0.4em}
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\small\sffamily Calamity Paper · font sample · \textbf{%(name)s}}
\fancyfoot[C]{\footnotesize\sffamily\color{calrule} %(pdflatex)s}
\renewcommand{\headrulewidth}{0.3pt}
\titleformat{\section}{\sffamily\bfseries\large}{\thesection}{0.6em}{}
\titleformat{\subsection}{\sffamily\bfseries}{\thesubsection}{0.5em}{}
\titlespacing*{\section}{0pt}{0.7em}{0.2em}
\titlespacing*{\subsection}{0pt}{0.5em}{0.1em}
\newtcolorbox{keyidea}{enhanced,breakable,colback=calidea,colframe=calideaedge,boxrule=0pt,leftrule=2.5pt,arc=1pt,
  left=6pt,right=6pt,top=3pt,bottom=3pt,fontupper=\normalsize,before upper={\textsf{\textbf{Key idea.}}\ }}
\newtcolorbox{pitfall}{enhanced,breakable,colback=calwarn,colframe=calwarnedge,boxrule=0pt,leftrule=2.5pt,arc=1pt,
  left=6pt,right=6pt,top=3pt,bottom=3pt,before upper={\textsf{\textbf{Pitfall.}}\ }}
\newtcolorbox{definition}[1]{enhanced,breakable,colback=caldef,colframe=caldefedge,boxrule=0pt,leftrule=2.5pt,arc=1pt,
  left=6pt,right=6pt,top=3pt,bottom=3pt,before upper={\textsf{\textbf{Definition} (#1).}\ }}
\newcommand{\term}[1]{\emph{#1}}
\lstset{basicstyle=\ttfamily\small,keywordstyle=\color{calkey}\bfseries,stringstyle=\color{calstr},
  commentstyle=\color{calcom}\itshape,backgroundcolor=\color{calcode},frame=none,xleftmargin=6pt,framexleftmargin=6pt,
  columns=fullflexible,keepspaces=true,showstringspaces=false,aboveskip=0.6em,belowskip=0.2em}
"""

BODY = r"""\begin{document}
{\sffamily\bfseries\LARGE Paging and the TLB}\par
\vspace{-0.3em}{\sffamily\color{calrule} Operating systems · memory management · notes for GATE CS}\par
\vspace{0.2em}
\section{Why paging exists}
A process sees one flat \term{virtual address space}; the machine has scattered frames of physical memory.
\textbf{Paging} cuts both into blocks of the same size, a \term{page} and a \term{frame}, and a per-process
\term{page table} maps one to the other. Contiguous allocation needs one hole big enough for the whole
process; paging needs only enough free frames, anywhere. A call such as \texttt{mmap(NULL, 4096, PROT\_READ, MAP\_PRIVATE, fd, 0)} only
adds entries; the frames arrive at the first touch, through a \term{page fault}.

\begin{definition}{effective access time}
With TLB hit ratio $h$, TLB time $t_{\mathrm{TLB}}$ and memory time $t_m$, a single-level table gives
\[
  \mathrm{EAT} = h\,(t_{\mathrm{TLB}} + t_m) + (1-h)\,(t_{\mathrm{TLB}} + 2t_m).
\]
\end{definition}

\begin{keyidea}
A miss costs one extra memory access per level of the page table, so the hit ratio, not the table size,
decides the speed: at $h = 0.98$, $t_{\mathrm{TLB}} = 10$\,ns and $t_m = 100$\,ns, $\mathrm{EAT} = 112$\,ns.
\end{keyidea}

\begin{pitfall}
Counting the TLB lookup only on a hit. The TLB is searched first on every reference, so $t_{\mathrm{TLB}}$
appears in both terms unless the question says the searches run in parallel.
\end{pitfall}

\section{Sizes, and the maths around them}
With a 32-bit address, 4\,KiB pages and 4-byte entries:
\begin{center}\small\vspace{-0.6em}
\begin{tabular}{@{}lrrr@{}}\toprule
Page size & Offset bits & Entries ($2^{32-k}$) & Table size \\\midrule
1 KiB & 10 & 4\,194\,304 & 16 MiB \\
4 KiB & 12 & 1\,048\,576 & 4 MiB \\
16 KiB & 14 & 262\,144 & 1 MiB \\\bottomrule
\end{tabular}
\end{center}
GATE mixes this with the rest of the syllabus; the page has to carry all of it:
\[
  P(A\mid B) = \frac{P(B\mid A)\,P(A)}{\sum_{i=1}^{n} P(B\mid A_i)\,P(A_i)},\qquad
  \int_{0}^{\infty} \lambda e^{-\lambda x}\,dx = 1,\qquad
  \det\!\begin{pmatrix} 2-\lambda & 1\\ 1 & 2-\lambda \end{pmatrix} = 0 \;\Rightarrow\; \lambda \in \{1, 3\}.
\]
\[
  T(n) = 2\,T\!\left(\tfrac{n}{2}\right) + \Theta(n) \in \Theta(n\log n),\qquad
  \sum_{k=0}^{\infty} \alpha^{k} = \frac{1}{1-\alpha}\ \ (|\alpha| < 1),\qquad
  \forall x\,\exists y\; (x \le y) \land \neg(y < x).
\]

\subsection{The lookup, in code}
\begin{lstlisting}[language=C]
/* Translate a virtual address with a two-level table (10 + 10 + 12 bits). */
uint32_t translate(uint32_t va, pde_t *dir) {
    pte_t *table = frame_to_ptr(dir[va >> 22].frame);   // outer index
    uint32_t frame = table[(va >> 12) & 0x3FF].frame;    // inner index
    return (frame << 12) | (va & 0xFFF);                 // keep the offset
}
\end{lstlisting}

\subsection{Recall before the next session}
\begin{enumerate}[nosep,leftmargin=1.4em]
\item Why does paging remove external fragmentation but not internal fragmentation?
\item A three-level table and $h = 0.9$: write the EAT with $t_{\mathrm{TLB}} = 20$\,ns, $t_m = 80$\,ns.
\item Which bits of \texttt{0x00403ABC} index the outer table, and which the inner?
\end{enumerate}
{\small\color{calrule}\sffamily Figures 0123456789 · \textit{italic} · \textbf{bold} · \textbf{\textit{bold italic}} · \texttt{mono 0O1lI} · αβγλπσ · → ≤ ≠ ∞ · “quotes” — dashes}
\end{document}
"""


def tex_for(set_id: str) -> str:
    name, body, sans, mono, maths, pdflatex, _ = SETS[set_id]
    fill = {"name": name, "math": maths, "pdflatex": "pdfLaTeX: " + pdflatex.split(" (")[0]}
    for prefix, spec in (("b", body), ("s", sans), ("m", mono)):
        fill[{"b": "body", "s": "sans", "m": "mono"}[prefix]] = spec[0]
        fill[prefix + "_r"], fill[prefix + "_b"], fill[prefix + "_i"], fill[prefix + "_bi"] = spec[1:]
    return PREAMBLE % fill + BODY


def engines() -> list:
    """(name, command builder) for each TeX engine installed."""
    out = []
    if shutil.which("tectonic"):
        out.append(("tectonic", lambda tex: ["tectonic", "-X", "compile", tex]))
    for prog in ("xelatex", "lualatex"):
        if shutil.which(prog):
            out.append((prog, lambda tex, prog=prog: [prog, "-interaction=nonstopmode", "-halt-on-error", tex]))
    return out


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--out", required=True, help="a folder outside the checkout")
    p.add_argument("--set", nargs="+", choices=sorted(SETS), help="only these sets (default: all)")
    a = p.parse_args(argv)
    out = os.path.abspath(a.out)
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if os.path.commonpath([out, root]) == root:
        print("--out must be outside the checkout")
        return 2
    found = engines()
    if not found:
        print("no TeX engine found (Tectonic, XeLaTeX or LuaLaTeX)")
        return 2
    os.makedirs(out, exist_ok=True)
    firsts, failed = [], []
    for set_id in a.set or list(SETS):
        built = None
        for engine, cmd in found:
            work = tempfile.mkdtemp(prefix="calamity-fonts-")
            try:
                tex = os.path.join(work, "%s.tex" % set_id)
                with open(tex, "w", encoding="utf-8") as fh:
                    fh.write(tex_for(set_id))
                proc = subprocess.run(cmd(tex), cwd=work, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                pdf = os.path.join(work, "%s.pdf" % set_id)
                if proc.returncode != 0 or not os.path.isfile(pdf):
                    tail = proc.stdout.decode("utf-8", "replace").strip().splitlines()[-3:]
                    failed.append("%s on %s: %s" % (set_id, engine, " | ".join(tail)))
                    continue
                target = os.path.join(out, "%s.%s.pdf" % (set_id, engine))
                shutil.copyfile(pdf, target)
                print("built %s" % target)
                built = built or target
            finally:
                shutil.rmtree(work, ignore_errors=True)
        if built:
            firsts.append(built)
            if shutil.which("pdftoppm"):
                subprocess.run(["pdftoppm", "-png", "-r", "110", built, os.path.join(out, set_id)], check=False)
    if len(firsts) > 1 and shutil.which("pdfunite"):
        subprocess.run(["pdfunite"] + firsts + [os.path.join(out, "font-samples.pdf")], check=False)
        print("all sets: %s" % os.path.join(out, "font-samples.pdf"))
    for line in failed:
        print("FAILED " + line)
    print("engines: %s" % ", ".join(e for e, _ in found))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
