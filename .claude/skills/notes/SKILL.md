---
name: notes
description: "Notes from what was studied: a fragment per topic, and on request a long-form notebook per skill (Markdown, or PDF)."
when_to_use: "When the learner asks to save notes, write up a topic, update study material or make a PDF of a skill's notes."
argument-hint: "[skill | skill/topic | pdf <skill>]"
---

# Notes

The long form follows the learner's `book.format`: `markdown` (the
default, `framework/rules/markdown-books.md`) or `pdf` (LaTeX,
`framework/rules/notes-latex.md`). If the brief says the format is not
chosen, ask once before writing anything long and record it with
`calamity profile set book.format markdown` (or `pdf`).

## After a session: fragments

For each topic taught or tested today:

    calamity notes fragment <skill>/<topic>

Open the file it names and fill in or extend the five parts: Idea, Worked
example, My code, Mistakes I made, Recall prompts. Ten to twenty-five
lines, from this session: the learner's example, their code as it finally
passed, the mistakes they actually made
(`calamity stats errors` lists them), two to four
questions for later. Set `updated` to today. Do not pad a fragment with
textbook material; that belongs in the section. For a GATE topic, add a
`## Formulas` section with the formulas and results worth knowing by
heart, one line each: `gate pack <subject>` collects them into the
subject's formula sheet.

## On request: the long-form document

1. See what needs writing:

       calamity notes status <skill>

2. For every topic marked `to write` or `stale`, delegate to the
   `notes-writer` agent: "Write the section for `<skill>/<topic>` from its
   fragment." Several topics can go in one request. The agent writes it
   where `notes section` says: `md/<topic>.md`, or `tex/<topic>.tex` for a
   learner who chose PDF.

3. Mark them current and put the book together:

       calamity notes stamp <skill>
       calamity notes assemble <skill>

   In Markdown that writes `<skill>-notes.md`, and that is the book: tell
   the learner where it is. Build a PDF only when they ask for one, or
   when their format is `pdf`:

       calamity notes pdf <skill>

   - Success prints the path of `<skill>-notes.pdf`: tell the learner
     where it is.
   - A LaTeX error: hand the build to the `notes-writer` agent ("build the
     PDF of `<skill>` and fix what fails"), so build logs and page checks
     stay out of this conversation; pass on the path it returns.
   - No TeX engine on this machine: say so, say the `.tex` files are ready,
     and that Tectonic, TeX Live or MiKTeX will build them. Do not install
     anything without being asked.


**A cheat sheet** (one landscape page for revision; when a skill is ready, or
before an exam, or when asked): the `notes-writer` agent in its cheat-sheet
mode ("cheat sheet for `<skill>`") writes `learner/notes/<skill>/cheatsheet.tex`
from the skill's notes, then

    calamity notes cheatsheet <skill>

builds `<skill>-cheatsheet.pdf`. If it says the page runs over, send it back
to the agent to cut.
## Asked for "all my notes"

    calamity notes status

lists every skill that has notes; build each in turn.

## Rules

- Notes record what the learner did and understood. Anything added beyond
  the session must be checked before it is written down.
- Never copy course material, slides or a book's text into notes. A
  lecture is summarised in the learner's own words.
- Do not edit `main.tex` or `calamity.sty`; the engine rewrites
  them on every build.
