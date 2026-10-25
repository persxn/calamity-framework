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
  (`.claude/skills/`) and its eight agents (`.claude/agents/`).

This is **additive and inert in normal use.** Running `claude` inside this
repository still loads `.claude/` as project configuration exactly as before;
the manifest matters only when Calamity is *installed* as a plugin elsewhere.

Validate the manifest and marketplace from the repository root:

    claude plugin validate .

## The `mastery-coach` skill (an added skill)

`.claude/skills/mastery-coach/` is a deep-coaching skill that ships with the
Calamity plugin and is invoked as `/mastery-coach`. It takes a learner to
complete mastery of one topic through its history and philosophy, a gap-free
prerequisite roadmap, the mechanism explained from the designer's point of
view, every flag and niche feature, and interview-grade questions with surprise
recall. It is the same depth-first teaching philosophy as the depth contract in
`framework/method.md`, in a self-contained coach.

It is an **added** skill, not part of the engine's shipped set (it is not in the
`SKILLS` tuple the self-test validates), because it runs its **own** session
loop and its **own** markdown state, and asks its **own** questions inline —
outside the engine's event log and the blind examiner/checker verification
pipeline. So:

- Use `/mastery-coach` for coaching a topic deeply or ad hoc, including topics
  the tree does not track. Its own state rules tell it to defer to an existing
  framework's store (Calamity's `learner/`) rather than make a parallel one.
- The engine-backed `study` skill stays the **system of record** for tracked
  progress, verified items, and anything that must show up on the roadmap,
  GATE board or recall queue. `mastery-coach` does not write engine events.

## The `mastery-textbook` skill (an added skill)

`.claude/skills/mastery-textbook/` is `mastery-coach`'s companion: it builds and
grows a polished LaTeX study book (compiled to PDF) as the learner progresses —
SVG figures, flag and comparison tables, real terminal output, graded exercises
with worked solutions, and verified references, to the same first-principles
standard. It ships a LaTeX template, an example chapter, reference guides, and a
build toolchain in `scripts/` (`build.sh` converts SVGs, compiles with
`latexmk`/`pdflatex`, renders pages, and runs `check_build.py`, a read-only
report). The scripts touch only the book root passed as an argument and reach no
network; a full LaTeX toolchain (`pdflatex`, `latexmk`, `pdftoppm`, an SVG
converter) is needed to build, and the skill asks before any system install.

Like `mastery-coach` it is an **added** skill (not in the engine's `SKILLS`
set) and engine-independent: it writes a book into the learner's study-material
store, outside the engine's event log. It **overlaps** the engine's `notes`
skill and `notes-writer` agent (which also produce LaTeX notes and a PDF per
skill): use `mastery-textbook` for a from-scratch, bestseller-standard book
grown alongside `mastery-coach`; use `notes`/`notes-writer` for the
engine-tracked per-topic notes fragments and skill PDFs.

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
