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
CLAUDE.md                  what loads every session, agents included: session start, the rules that never bend
README.md                  for people: what it is, installation, first session, daily use
docs/                      guides for people: setup per system, daily use, the three tools, troubleshooting
  maintainers/             token-baseline.md: what sessions cost, measured with tools/baseline.py
evals/                     behaviour cases for claude plugin eval (README.md says how to run them)
CONTRIBUTING.md            for contributors: checks and rules; SECURITY.md: what runs where, reporting
CHANGELOG.md               what changed in each version (framework/VERSION); LICENSE: MIT
.github/workflows/         continuous integration: tests on Linux, macOS and Windows
.claude/
  settings.json            permissions shared by everyone who clones the repo
  settings.local.json      this machine only (session-start hook); never committed
  skills/<name>/SKILL.md   the slash commands
  agents/<name>.md         the specialist agents
  output-styles/           calamity-tutor.md: how a study session teaches (setup --hook selects it)
engine/
  CLAUDE.md                guidance for maintainers; loads only when a session works in engine/
  calamity.py              entry point of the CLI
  cal/                     the engine (Python standard library only)
  tests/                   run with: python3 engine/calamity.py selftest
tools/                     development checks: end-to-end run, fuzzer, sample output, timing, token use
  README.md                what each tool checks and how to run it
  git-hooks/               keep study records out of the framework repository (core.hooksPath)
framework/                 shipped with the framework; the same for every learner
  method.md                the method (loop, asking, judging, modes): study, recall, boss, gate, cp
  method-teaching.md       the teaching standard: loaded only when teaching new material
  MAP.md                   this file
  config.md                default numbers; a learner overrides with cfg.<key> in the profile
  VERSION
  rules/                   rule books, loaded by the skills that need them
  tree/tracks.md           the tracks and the order of their groups
  tree/<track>/<skill>.md  one file per skill: prerequisites, scope, boss, weave, topics
  gate/<year>.md           what the organisers published for that year
  notes/preamble.tex       LaTeX preamble for study notes
learner/                   everything about one learner; this is what they sync
  README.md                what each folder holds (ships with the framework)
  profile.md               answers from onboarding (keys) and free notes about the learner
  schedule.md              the current day shape, written with the learner (coach skill); its blocks drive `day`
  timetable.json           per-date notes, goals and shifted days (day note, day goal, tools/timetable.py)
  PROGRESS.md              generated snapshot of progress (never edited by hand)
  events/                  the append-only log: <YYYY-MM>.<machine>.jsonl (engine only)
  items/<skill>/           practice items with sealed keys (engine only; never read)
  syllabus/<skill>.md      this learner's syllabus for a skill
  tree/<skill>.md          skills this learner added, changed or dropped
  sources/<id>.md          a course, playlist or book: its lectures and the topics they cover
  notes/<skill>/           notes: <topic>.md fragments, tex/ sections, main.tex, the PDF
  mastery/<topic>/         deep coaching: curriculum.md, recall.md, log.md and book/ (mastery-coach/-textbook)
  mastery/projects/<slug>/ build-it-yourself: brief, teardown/design, skill-map, build-path, log
  work/<skill>/            exercise and project workspaces
  cp/                      competitive programming: plan.md, solutions/, reviews/
  gate/                    plan.md, <year>.md corrections, mock reviews
  bridges/<source>/        generated code that connects one study source, with its README
.calamity/                 machine-local and never committed: machine id, caches (the replay snapshot),
                           scratch in tmp/ (the examiner's and checker's folders are sealed: guard tool)
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

## Skills and agents

Claude Code lists these with their descriptions in every session; this is
the registry the self-test holds them to. A learner's own additions live
beside them and are not listed here.

| Skill (`/name`) | What it is for |
|---|---|
| `onboard` | first-run setup: a new learner, a new track, a new machine |
| `study` | a study session: surprise recall, then small chunks tested at once |
| `recall` | a review round: only what is due, no new material |
| `today` | today's finish line and the single next thing to do |
| `dash` | progress, roadmap, revision queue, GATE and Codeforces boards, the week |
| `tree` | the skill tree: routes, prerequisites, add, swap, drop, skip |
| `boss` | the project or timed test that proves a skill |
| `notes` | notes per topic, LaTeX sections, a PDF per skill |
| `gate` | the GATE companion: plan, triage, mocks, past papers |
| `cp` | the competitive programming coach on Codeforces |
| `coach` | the weekly review and the day shape in `learner/schedule.md` |
| `remind` | study reminders from the operating system |
| `practice` | questions from outside material (previous papers, a book, a PDF): log them, revisit each |
| `stock` | stock the item bank ahead, headless at night (`stock render`); run by the learner or the scheduler only |
| `bridge` | connect a course, playlist or book by a route its terms allow |
| `log` | record study done outside the session: a lecture, a chapter, a workout |
| `sync` | save progress to the learner's own repository and merge other laptops |
| `update-framework` | bring in a new framework version, never touching `learner/` |
| `mastery-coach` | deep coaching of any tool or topic, with its own loop and state |
| `mastery-textbook` | a LaTeX study book that grows with the coaching |
| `build-it-yourself` | learn a project by rebuilding or designing it and shipping it |

| Agent | What it does |
|---|---|
| `examiner` | writes practice items as sealed drafts |
| `checker` | verifies drafts blind, without their keys |
| `curriculum-architect` | syllabi, placement tests, new tree nodes, lecture mappings |
| `cp-coach` | the Codeforces training plan from the learner's record |
| `gate-strategist` | the GATE plan back from the exam date, triage, targets |
| `habit-coach` | how the learner actually works, against their schedule |
| `bridge-engineer` | the one-off tool that connects a study source |
| `notes-writer` | long-form LaTeX sections from a topic's notes |

## Rule books

| File | Read it when |
|---|---|
| `framework/rules/engine.md` | you need a command, a flag or an exit code |
| `framework/rules/verification.md` | making, checking or disputing an item; judging hands-on work; recording a boss |
| `framework/rules/items.md` | writing an item draft (format, types, quality bar) |
| `framework/rules/syllabus.md` | writing a learner's syllabus for a skill; placement tests; renaming topics |
| `framework/rules/tree-editing.md` | adding, changing, dropping or restoring a skill; the four skill-file shapes; slots and weaving |
| `framework/rules/scheduler.md` | the day plan, the finish line, the schedule file, behaviour patterns, reminders |
| `framework/rules/bridge-rulebook.md` | connecting a course site, a playlist or any other study source |
| `framework/rules/gate-onboarding.md` | setting up a GATE learner |
| `framework/rules/gate-planning.md` | GATE targets, the plan, phases, triage, two papers |
| `framework/rules/gate-playbook.md` | the GATE daily loop, mocks and test series, past papers |
| `framework/rules/cp-onboarding.md` | setting up a Codeforces learner, placement from the record |
| `framework/rules/cp-planning.md` | CP levels, the week, reading `cf analyse`, pace |
| `framework/rules/cp-playbook.md` | a CP coaching turn: one problem, contests, teaching |
| `framework/rules/markdown-books.md` | writing study books and long-form notes in Markdown (the default format) |
| `framework/rules/notes-latex.md` | writing notes fragments, LaTeX sections and PDFs (`book.format pdf`) |
