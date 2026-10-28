# The Calamity plugin ecosystem

Calamity is moving toward a **plugin ecosystem**: one marketplace in this
repository (`.claude-plugin/marketplace.json`) that lists Calamity itself and,
in time, companion plugins that share its way of working — teach or coach from
the basics, test or measure at once, surface earlier material unannounced, and
keep an honest, evidence-first record with no points or streaks.

Each companion stays its **own** system with its **own** repository and its
**own** state convention; the marketplace only points at it. Personal data
never lives in a shared repository — the same rule Calamity already follows by
keeping `learner/` out of version control.

## What is scaffolded today

- `.claude-plugin/marketplace.json` — a marketplace named `calamity` with one
  entry, the Calamity plugin, sourced from this repository (`"source": "."`).
- `.claude-plugin/plugin.json` — Calamity's own manifest: its skills
  (`.claude/skills/`) and its agents (`.claude/agents/`).

This is **additive and inert in normal use.** Running `claude` inside this
repository still loads `.claude/` as project configuration exactly as before;
the manifest matters only when Calamity is *installed* as a plugin elsewhere.

Validate the manifest and marketplace from the repository root:

    claude plugin validate .

## The companion-skill contract

Calamity ships three companions beside its study skills — `mastery-coach`,
`mastery-textbook` and `build-it-yourself` — and since framework 1.1 they run
**on the engine**, not beside it. Any future companion keeps to the same
contract:

1. **One record.** Progress is decided by the engine and nothing else. A
   topic the learner works on is a tree skill (`find`, or the
   `curriculum-architect` designs the node and its syllabus with `tree add`);
   teaching is recorded with `ask --taught`; every question that counts is an
   engine item, written by the `examiner` and verified blind by the `checker`;
   reviews come from the engine's schedule. A companion keeps no parallel
   question bank, schedule or "done" flag.
2. **Formative versus summative.** Questions a companion asks inline while
   teaching are formative: they check a chunk landed and decide nothing. Its
   best ones become *seeds* for the examiner (question ideas, never answers).
3. **One depth standard.** `framework/method-teaching.md`, with the deep arc
   in the reference skill `teach-deep` (not a command; `mastery-coach` and
   `study --deep` read it).
4. **Narrative beside the record.** What the engine cannot hold — the story of
   the teaching, which the book is written from — lives in the synced store:
   `learner/coach/<topic>/` (curriculum units, session log, glossary,
   reading, seeds), books in `learner/books/<topic>/`, projects in
   `learner/projects/<slug>/`. `layout migrate` moves an older
   `learner/mastery/`.
5. **Heavy work runs forked.** A book is written and built by the
   `book-builder` agent (`mastery-textbook` has `context: fork`), so drafts,
   builds and page images never enter the tutor's conversation.
6. **Held to the framework's doc standard**: valid front matter, a
   `description` and `when_to_use` that do not collide with another skill's
   requests, and every engine command and framework link they quote checked
   by `test_docs.py`.

## `mastery-coach`

Deep coaching to complete mastery of any tool or topic: the origin story,
vocabulary, a gap-free map, the designer's lens, the whole surface, field
reading, debugging literacy, the AI era, build and ship, and the mastery exam
as the skill's boss. Its routing is narrow on purpose: deep dives, internals
and interview preparation. "Quiz me" belongs to `recall`, "continue" to
`study`.

A unit is done when the engine says so: `unit <skill> <topics>` prints
`UNIT DONE` once every topic is `consolidating` or beyond and the learner has
explained one back (`observe --tag explain`). In-depth mode opens at most one
new unit per session. An account-level copy of a skill with the same name
(for instance synced from claude.ai) competes for the same requests; `doctor`
warns while one is installed.

## `mastery-textbook`

A study book per topic that grows as units are done: Markdown chapters by
default (`framework/rules/markdown-books.md`), a typeset LaTeX/PDF edition
when the learner chose `book.format pdf` (template, SVG figures, `build.sh`,
three review passes). It runs forked through `book-builder`, reads the coach's
narrative, the notes fragments and the seeds, and **never** the item bank: a
key in a book is a key seen before the question. Only the regenerable
`build/` output and `book.pdf` are git-ignored.

It overlaps the `notes` skill on purpose and at a different size: `notes`
keeps the per-topic fragments and the per-skill notebook; the book is the
deluxe per-topic edition. The two stores stay separate (`learner/notes/`
versus `learner/books/`).

## `build-it-yourself`

Turns a project into a learning path the learner builds and ships with their
own hands. **Reverse mode** tears down a repository or a shipped app with
read-only recon (`scripts/repo_recon.py`, `scripts/artifact_recon.py`, REA);
**idea mode** architects the learner's own idea. On the engine: the project
is a tree skill whose topics are the build milestones, each milestone's
acceptance tests are a `task` item checked for real, the skills it needs are
tree skills taught through `mastery-coach` at their tier, and shipping is
recorded as its capstone (`boss record ... --kind capstone`). The cloned
source and binaries are scratch outside `learner/`, never committed.

## Known follow-ups before Calamity installs cleanly as a plugin

These are not blockers for using the repository in project mode; they are what a
full plugin install would need, and they are deliberately left for a later pass:

1. **Root `CLAUDE.md` doctrine.** A plugin does **not** load a plugin-root
   `CLAUDE.md` into context (plugin validate warns about one). Calamity's core
   rules live in `CLAUDE.md`, so to run as an installed plugin that doctrine
   must move into an always-on skill. In project mode it already loads, so
   nothing is lost today.
2. **The session-start brief hook.** The `=== CALAMITY BRIEF ===` hook lives in
   `.claude/settings.json`. As a plugin it would move to a plugin hook
   (`hooks/hooks.json` or the manifest's `hooks` field), using
   `${CLAUDE_PLUGIN_ROOT}` to locate `engine/calamity.py`.
3. **The engine path.** Skills call `python3 engine/calamity.py …` relative to
   the project root. An installed plugin would resolve the engine through
   `${CLAUDE_PLUGIN_ROOT}` instead.

## Adding a companion plugin (for example, Ascend)

A companion such as Ascend (a personal coaching system — training, nutrition,
reading, consistency) is kept as a **separate private repository**. When it has
one, add an entry to `plugins` in `.claude-plugin/marketplace.json` that points
at that repository — do **not** copy its files or its personal state into this
repository:

```json
{
  "name": "ascend",
  "source": { "source": "github", "repo": "<owner>/ascend" },
  "description": "Personal coaching: training, nutrition, appearance, reading and consistency, with evidence grades and a model of you that learns.",
  "category": "coaching",
  "tags": ["coaching", "habits", "health", "reading"]
}
```

Then the companion keeps its own `.claude-plugin/plugin.json`, its own skills
and agents, and its own untracked state. Namespacing (`ascend:coach` versus
`calamity:coach`) keeps commands that share a name from colliding.
