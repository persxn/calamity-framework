# Notes and PDFs

Every skill you study can become a document you keep: one PDF per skill,
built from what actually happened in your sessions. It is made in two steps
so that nothing is lost and nothing is invented.

## 1. Fragments, after every session

At the end of a session Claude saves a short Markdown **fragment** for each
topic you met, in `learner/notes/<skill>/<topic>.md`:

- **Idea**: the point, in a few lines;
- **Worked example**: yours, from the session;
- **My code**: your code as it finally passed;
- **Mistakes I made**: the ones you actually made, from the record;
- **Recall prompts**: two to four questions for later.

They are plain Markdown: read them, edit them, add to them.

## 2. The long form, on request

Ask for it ("write up my Docker notes", "make a PDF of linear algebra"),
or use `/notes`:

1. `notes status <skill>` lists which topics have a fragment and which
   sections still need writing or rewriting.
2. The `notes-writer` agent turns each fragment into a full LaTeX section:
   the key idea, an explanation from first principles, your worked example,
   code, a pitfall box, your mistakes with their corrections, and the recall
   prompts. Anything it adds beyond the fragment is checked against the
   official documentation or run first; what it cannot check, it leaves
   out.
3. `notes stamp <skill>` marks the sections as current, and
   `notes pdf <skill>` builds `learner/notes/<skill>/<skill>-notes.pdf`.

```bash
python3 engine/calamity.py notes status docker
python3 engine/calamity.py notes pdf docker
```

A fragment you change later makes its section **stale**; `notes status`
shows it, and the section is rewritten on the next request.

## A TeX engine

The PDF needs a TeX engine on your computer; the engine uses the first one
it finds: Tectonic, then `latexmk`, `pdflatex`, `xelatex` or `lualatex`.

| System | Smallest choice | Also works |
|---|---|---|
| Linux | Tectonic | TeX Live: `sudo apt install texlive-latex-recommended latexmk` on Debian or Ubuntu |
| macOS | `brew install tectonic` | MacTeX |
| Windows | `winget install MiKTeX.MiKTeX` (installs missing packages on demand) | Tectonic |

Tectonic downloads the LaTeX packages it needs the first time it builds a
document, so that first build needs the internet. Without any TeX engine
the `.tex` files are still written and ready; `notes pdf` says so.

`python3 engine/calamity.py doctor` reports which TeX engine it found.

## Rules

- Notes record what you did and understood. They never copy course
  material, slides or a book's text.
- Do not edit `main.tex` or `calamity-preamble.tex`: the engine rewrites
  them on every build. Edit the sections in `tex/`.
- Fragments and sections are part of your record and are synced; the built
  PDF and LaTeX's working files are not (`.gitignore`).

The conventions the notes writer follows are in
`framework/rules/notes-latex.md`.
