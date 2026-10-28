# Moving a study clone from 1.x to 2.0

Your record in `learner/` is never changed by the update itself. A few
things around it move or need installing again, and `doctor` lists each of
them until it is done. This order was run on a copy of a real 1.x study
clone and ended with `0 problem(s)`.

Commands are written in their full form, `python3 engine/calamity.py ...`
(Windows: `python engine/calamity.py ...` or `py -3 engine/calamity.py ...`),
because the `calamity` command only exists after step 3.

## 1. Save your progress

Inside Claude Code: `/sync`. `git status --short` must show nothing
uncommitted before the update.

## 2. Bring in 2.0

Inside Claude Code: `/update-framework`. By hand:

```bash
git fetch upstream --tags
git merge upstream/main
python3 engine/calamity.py selftest
python3 engine/calamity.py doctor
```

`doctor` now shows warnings for the steps below.

## 3. Replace the shell alias first

In 1.x, `calamity` in a terminal was an alias that opened Claude Code here
with permission prompts off. In 2.0 every skill runs the engine as
`calamity <command>`, and Claude Code's shell keeps your aliases, so the old
alias would open a new session instead. Replace it before your next study
session, and put the command on the PATH:

```bash
python3 engine/calamity.py setup --alias --shim
```

Then open a new terminal. `calamity` on its own still opens Claude Code
here with permission prompts off; `calamity today` (any command after it)
runs the engine. Until this step, the brief says `engine:
python3 engine/calamity.py` and warns that `calamity` is still the old
alias. If `~/.local/bin` is not on your PATH, the command says so: add it in
your shell's start-up file.

## 4. Install the hooks again

```bash
python3 engine/calamity.py setup --hook
```

2.0 adds the key guard (item keys stay out of searches and shell commands),
the study hooks (request routing and `!feedback`, the Stop guard,
compaction, session end) and the Calamity Tutor output style. They take
effect in the next session.

## 5. Move the store layout

The deep-coaching files moved out of `learner/mastery/`:

```bash
python3 engine/calamity.py layout migrate            # shows the moves
python3 engine/calamity.py layout migrate --write    # makes them, with git mv
```

`learner/mastery/<topic>/` becomes `learner/coach/<topic>/`, books go to
`learner/books/<topic>/`, projects to `learner/projects/<slug>/`. Nothing is
overwritten; a move that would is reported and skipped.

## 6. Move the day shape (if it is written as tables)

```bash
python3 engine/calamity.py day migrate               # shows the result
python3 engine/calamity.py day migrate --write       # rewrites the front matter; the body is kept
```

## 7. Rebuild

```bash
python3 engine/calamity.py rebuild
```

It writes `learner/journal/<YYYY-MM>.md` (new in 2.0) and `PROGRESS.md`.

## 8. Things that change by themselves

- **Notes PDFs, Markdown-book PDFs and revision packs** are set in Calamity
  Paper (Charter, Fira Sans, Fira Mono). The next `notes pdf` replaces the
  old `calamity-preamble.tex` with `calamity.sty`; every environment the
  sections used is still there.
- **A LaTeX study book** made with 1.x (`mastery-book.sty`): copy
  `framework/design/calamity.sty` beside its `main.tex`, change
  `\usepackage{mastery-book}` to `\usepackage[book]{calamity}`, and rename
  any `\begin{code}` block to `\begin{codeblock}`.
- **The book format** is asked once if it was never chosen
  (`profile set book.format markdown` or `pdf`).

## 9. Check and save

```bash
calamity doctor
```

It should end with `0 problem(s)`. Then `/sync`.

## Optional: the plugin instead of a clone

2.0 also installs as a Claude Code plugin, with your record in a folder of
its own (`PLUGINS.md`). A clone that works needs no change; do not enable
the plugin inside a clone, or its hooks and skills would run twice.
