# Study notes: fragments, LaTeX sections, PDF

This is the path for a learner whose `book.format` is `pdf`. The default is
Markdown (`framework/rules/markdown-books.md`); fragments are the same in
both.

Every skill a learner studies becomes a document they can keep: one PDF per
skill, built from what actually happened in their sessions. It is made in
two steps so that nothing is lost and nothing is invented.

```
learner/notes/<skill>/
  <topic>.md              fragment: short, written at the end of a session (the source)
  tex/<topic>.tex         section: the full write-up, derived from the fragment
  tex/stamps.json         which fragment each section was written from (engine)
  main.tex                assembled by the engine, in syllabus order (never edited)
  calamity-preamble.tex   copied from framework/notes/preamble.tex (never edited)
  <skill>-notes.pdf       built on demand
```

## Step 1: the fragment (tutor, at the end of a session)

For each topic taught or tested in the session:

    python3 engine/calamity.py notes fragment <skill>/<topic>

prints the path of the fragment and creates it with this skeleton if it is
new. Fill it in, or add to it, in ten to twenty-five lines:

```markdown
---
topic: docker/multi-stage
title: Multi-stage builds
updated: 2026-10-11
---

## Idea
The final image is the last stage; earlier stages only produce files.

## Worked example
The Java service from today: Maven stage, then a JRE-only stage, 412 MB down to 187 MB.

## My code
(the Dockerfile the learner wrote, as it finally passed)

## Mistakes I made
- used `COPY --from=0`, then reordered the stages and copied from the wrong one

## Recall prompts
- Which stage becomes the image, and what happens to the others?
- Why is the dependency file copied before the sources?
```

- Write what this session established, in the learner's own words where
  they said it well. Use their example, their code, their numbers.
- "Mistakes I made" comes from the session's wrong answers
  (`python3 engine/calamity.py stats errors`). It is the most valuable part.
- Two to four recall prompts: questions only.
- Update the `updated` date. A fragment is plain Markdown and is useful on
  its own; the learner can read it on GitHub.

## Step 2: the section (notes-writer agent, on request)

    python3 engine/calamity.py notes status <skill>

lists each topic as `to write` (a fragment with no section), `stale` (the
fragment changed since the section was written) or `ok`. For each one to
write or rewrite, the `notes-writer` agent gets the path from

    python3 engine/calamity.py notes section <skill>/<topic>

and writes the section there. When the sections are done:

    python3 engine/calamity.py notes stamp <skill>
    python3 engine/calamity.py notes pdf <skill>

`notes pdf` assembles `main.tex` and compiles it with the first TeX engine it
finds (Tectonic, latexmk, pdfLaTeX, XeLaTeX, LuaLaTeX). If it fails it prints
the LaTeX error with the line; fix that section and run it again. If no TeX
engine is installed it says so and leaves the `.tex` files ready; Tectonic is
the smallest thing to install, TeX Live and MiKTeX also work.

### What a section contains

A section is the long form of its fragment: one to three pages that a
learner can study from a year later without the session.

```latex
\section{Multi-stage builds}\label{sec:docker:multi-stage}

\begin{keyidea}
The one thing to remember, in two or three sentences.
\end{keyidea}

Explanation to the one depth bar (framework/method-teaching.md): the problem this solves and what came before, the mental model, the inner mechanics (why it behaves so, not only what it does), and when to use it and when not.

\subsection{How it works}
...

\begin{example}
A complete worked example, with every step shown.
\begin{lstlisting}[language=Dockerfile,caption={Two stages: build, then run}]
FROM maven:3.9-eclipse-temurin-21 AS build
...
\end{lstlisting}
\end{example}

\begin{pitfall}
The usual way to get this wrong, and how to notice.
\end{pitfall}

\begin{mistakes}
\item What the learner got wrong, from the fragment, and the correction.
\end{mistakes}

\begin{recall}
\item A question to answer from memory.
\end{recall}
```

- Start with `\section{<topic title>}\label{sec:<skill>:<topic>}`. Use
  `\subsection` inside. Refer to other topics with `\ref{sec:<skill>:<topic>}`.
- Everything in the fragment appears in the section. What you add beyond
  it (derivations, background, a second example) must be correct and
  checked: run the code, compute the numbers, look up anything that
  changes with versions. If you could not check something, leave it out.
- Keep the learner's own code and mistakes recognisable. These are their
  notes, not a textbook.

### LaTeX rules

The preamble defines everything a section may use. A section must compile
with pdfLaTeX, XeLaTeX and LuaLaTeX alike, without shell escape.

- **No preamble commands in a section**: no `\documentclass`,
  `\usepackage`, `\input`, `\include`, `\newcommand`, `\write18`.
- **Environments available**: `keyidea`, `pitfall` (short, they do not break
  across pages), `example`, `mistakes`, `recall`, `lstlisting`, and standard
  LaTeX (`itemize`, `enumerate`, `tabular` with `\toprule`, `\midrule`,
  `\bottomrule`, `align`, `equation`, `figure`).
- **Inline helpers**: `\code{git rebase -i}` for inline code (it copes with
  `_ ^ & $ ~`; for text containing `%`, `#` or unbalanced braces use
  `\lstinline|...|`), `\term{...}` for a term being defined, `\bigO{n \log n}`.
- **Listings**: `\begin{lstlisting}[language=...]`. Languages: `C`, `C++`,
  `Java`, `Python`, `SQL`, `bash`, `HTML`, `XML`, `Go` (built in) and
  `JavaScript`, `TypeScript`, `Kotlin`, `Dart`, `Dockerfile`, `YAML`, `JSON`,
  `HCL`, `text` (defined in the preamble). Listings contain plain ASCII
  only: replace arrows, curly quotes and accented letters inside code.
- **Escape in running text**: `\&`, `\%`, `\$`, `\#`, `\_`, `\{`, `\}`,
  `\textasciitilde{}`, `\textasciicircum{}`, `\textbackslash{}`. Write
  `<`, `>` and `|` only in math or in code, never bare in text.
- **Maths** in `\( ... \)` and `\[ ... \]` or `align`; amsmath and amssymb
  are loaded.
- **Quotes** as ``` ``like this'' ```. Dashes as `--` and `---`.
- **Images** only if they exist: put the file in
  `learner/notes/<skill>/img/` and include it with
  `\includegraphics[width=0.8\linewidth]{img/<file>}`. Do not reference an
  image that is not there.
- One file per topic, named after the topic id. Never edit `main.tex` or
  `calamity-preamble.tex`: the engine rewrites them.

## What is committed

Fragments, sections and `stamps.json` are the learner's notes and are
tracked. Build products (`main.pdf`, logs, auxiliary files) are ignored by
git; the named PDF `<skill>-notes.pdf` is ignored too by default, because
it can be rebuilt. A learner who wants the PDFs in their repository removes
that line from `.gitignore`.
