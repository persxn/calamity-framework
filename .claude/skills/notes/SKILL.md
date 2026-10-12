---
name: notes
description: Turn what the learner has studied into notes they keep - a short Markdown fragment per topic after each session, a full LaTeX section per topic on request, and one PDF per skill. Use when the learner asks to save notes, write up a topic, build or update study material, or make a PDF of a skill.
argument-hint: "[skill | skill/topic | pdf <skill>]"
---

# Notes

Conventions for both steps are in `framework/rules/notes-latex.md`. Read
it before writing a section.

## After a session: fragments

For each topic taught or tested today:

    python3 engine/calamity.py notes fragment <skill>/<topic>

Open the file it names and fill in or extend the five parts: Idea, Worked
example, My code, Mistakes I made, Recall prompts. Ten to twenty-five
lines, from this session: the learner's example, their code as it finally
passed, the mistakes they actually made
(`python3 engine/calamity.py stats errors` lists them), two to four
questions for later. Set `updated` to today. Do not pad a fragment with
textbook material; that belongs in the section.

## On request: the long-form document

1. See what needs writing:

       python3 engine/calamity.py notes status <skill>

2. For every topic marked `to write` or `stale`, delegate to the
   `notes-writer` agent: "Write the LaTeX section for `<skill>/<topic>`
   from its fragment." Several topics can go in one request. The agent
   writes `learner/notes/<skill>/tex/<topic>.tex`.

3. Mark them current and build:

       python3 engine/calamity.py notes stamp <skill>
       python3 engine/calamity.py notes pdf <skill>

   - Success prints the path of `<skill>-notes.pdf`: tell the learner
     where it is.
   - A LaTeX error names the section and line: fix that section (or send it
     back to the notes writer with the error) and build again.
   - No TeX engine on this machine: say so, say the `.tex` files are ready,
     and that Tectonic, TeX Live or MiKTeX will build them. Do not install
     anything without being asked.

## Asked for "all my notes"

    python3 engine/calamity.py notes status

lists every skill that has notes; build each in turn.

## Rules

- Notes record what the learner did and understood. Anything added beyond
  the session must be checked before it is written down.
- Never copy course material, slides or a book's text into notes. A
  lecture is summarised in the learner's own words.
- Do not edit `main.tex` or `calamity-preamble.tex`; the engine rewrites
  them on every build.
