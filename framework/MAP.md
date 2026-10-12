# Map

The index of this repository. Nothing here needs embeddings or a database:
every fact has one home, the homes are listed below, and the engine's `find`
command searches them by name and alias. Look up, then read the one file
you need. Do not read whole directories into context.

## How to look something up

1. **By name**: `python3 engine/calamity.py find <words>` searches skills
   (ids, titles, aliases), topics, lectures of connected sources, and notes.
2. **A skill**: `python3 engine/calamity.py tree show <skill>` prints its
   status, prerequisites, what it unlocks, and every topic with the
   learner's standing on it. The line `file:` names the markdown file behind
   it.
3. **A topic**: its objectives are in the skill's syllabus (the `file:`
   above, or `learner/syllabus/<skill>.md`). The learner's own notes on it
   are in `learner/notes/<skill>/<topic>.md`. Their mistakes on it:
   `python3 engine/calamity.py stats errors`.
4. **The learner right now**: `brief`, `today`, `dash`.
5. **The learner over time**: `stats week`, `stats hours`, `observations`,
   and `learner/PROGRESS.md`.
6. **A rule**: the table at the end of this file.

The chain is always index, then skill file, then topic, then notes or
evidence. Stop as soon as the question is answered.

## Layout

```
CLAUDE.md                  what loads every session (imports framework/method.md)
README.md                  for people: install, first run, daily use
.claude/
  settings.json            permissions shared by everyone who clones the repo
  settings.local.json      this machine only (session-start hook); never committed
  skills/<name>/SKILL.md   the slash commands
  agents/<name>.md         the specialist agents
engine/
  calamity.py              entry point of the CLI
  cal/                     the engine (Python standard library only)
  tests/                   run with: python3 engine/calamity.py selftest
framework/                 shipped with the framework; the same for every learner
  method.md                the method (always in context)
  MAP.md                   this file
  config.md                default numbers; a learner overrides with cfg.<key> in the profile
  VERSION
  rules/                   rule books, loaded by the skills that need them
  tree/tracks.md           the tracks and the order of their groups
  tree/<track>/<skill>.md  one file per skill: prerequisites, scope, boss, weave, topics
  gate/<year>.md           what the organisers published for that year
  notes/preamble.tex       LaTeX preamble for study notes
learner/                   everything about one learner; this is what they sync
  profile.md               answers from onboarding (keys) and free notes about the learner
  schedule.md              the current day shape, written with the learner (coach skill)
  PROGRESS.md              generated snapshot of progress (never edited by hand)
  events/                  the append-only log: <YYYY-MM>.<machine>.jsonl (engine only)
  items/<skill>/           practice items with sealed keys (engine only; never read)
  syllabus/<skill>.md      this learner's syllabus for a skill
  tree/<skill>.md          skills this learner added, changed or dropped
  sources/<id>.md          a course, playlist or book: its lectures and the topics they cover
  notes/<skill>/           notes: <topic>.md fragments, tex/ sections, main.tex, the PDF
  work/<skill>/            exercise and project workspaces
  cp/                      competitive programming: plan.md, solutions/, reviews/
  gate/                    plan.md, <year>.md corrections, mock reviews
  bridges/<source>/        generated code that connects one study source, with its README
.calamity/                 machine-local and never committed: machine id, caches, scratch
```

Tracks shipped: `10x` (the developer path), `ai` (maths, ML, LLM
engineering), `cp` (competitive programming), `gate` (General Aptitude),
`gate-cs` and `gate-da` (the two papers). A learner's own skills may use
these or any new track name.

## What is stored where, and why

- **The event log is the truth.** Schedules, mastery, statistics and
  dashboards are recomputed from `learner/events/` on every run. Each
  machine appends to its own file, so two laptops never edit the same file
  and git merges them without conflicts.
- **Shipped files are never edited for one learner.** A learner's syllabus,
  tree changes, exam-year corrections and configuration overrides live under
  `learner/` and take precedence. A framework update therefore never
  touches a learner's data.
- **Skill ids** are lower-case with `-` and `.`; a topic is addressed as
  `<skill>/<topic>`, for example `docker/multi-stage` or
  `gate.cs.toc/pumping-lemma`.

## Rule books

| File | Read it when |
|---|---|
| `framework/rules/engine.md` | you need a command, a flag or an exit code |
| `framework/rules/verification.md` | making, checking or disputing an item; judging hands-on work; recording a boss |
| `framework/rules/items.md` | writing an item draft (format, types, quality bar) |
| `framework/rules/syllabus.md` | writing a learner's syllabus for a skill; placement tests; renaming topics |
| `framework/rules/tree-editing.md` | adding, changing, dropping or restoring a skill; slots and weaving |
| `framework/rules/scheduler.md` | the day plan, the finish line, the schedule file, behaviour patterns, reminders |
| `framework/rules/bridge-rulebook.md` | connecting a course site, a playlist or any other study source |
| `framework/rules/gate-playbook.md` | anything about GATE: onboarding, phases, triage, mocks, targets |
| `framework/rules/cp-playbook.md` | anything about competitive programming and Codeforces |
| `framework/rules/notes-latex.md` | writing notes fragments, LaTeX sections and PDFs |
