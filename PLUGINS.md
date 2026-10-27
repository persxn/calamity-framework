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

Calamity ships three **added** skills beside the engine's set — `mastery-coach`,
`mastery-textbook` and `build-it-yourself`. They run their own loops and state,
outside the engine's event log and the examiner/checker pipeline, so they are
not in the engine's `SKILLS` tuple. But to fit the ecosystem they all keep to
one contract, and any future companion skill should too:

1. **One depth standard.** Teach and write to the single bar in
   `framework/method-teaching.md` — the same bar the default `study` path is
   now held to. There is no "lite" tier of *understanding*; there are only
   fuller and quicker *write-ups* (see tiers below). A shallow summary is a
   failure of the standard, never a faster option.
2. **One synced, learner-aware store.** All state and output go under
   `learner/mastery/` (topics in `learner/mastery/<topic>/`, projects in
   `learner/mastery/projects/<slug>/`), inside the only tree `/sync` commits,
   written as the work happens. Never a repo-root `.mastery/`, which is not
   backed up. Record who the learner is in the store; a session for someone
   other than the framework's own learner stays in the store only.
3. **Bridge tracked work into the engine.** When the topic is one the skill
   tree tracks and the learner is the framework's own, surface it with
   `observe --tag coach` and `quick`, so it shows on the roadmap, recall queue
   and dashboards and lands in the synced event log. The engine stays the
   system of record for verified, blind-checked items.
4. **Held to the framework's doc standard.** They are listed in `test_docs.py`'s
   `ADDED_SKILLS`, so their front matter is valid and every engine command and
   framework link they quote is checked — the same net as the shipped skills.

**Two write-up tiers, one standard.** The engine's `notes`/`notes-writer`
produce the learner's per-skill *notebook* (seeded from their own session,
analytical to the one bar). `mastery-textbook` produces the deluxe per-topic
*book* to a bestseller standard, and can build from **either** teaching path —
`mastery-coach` state, or the engine's notes fragments and verified item bank
for a topic taught through `/study`. So whichever way a topic was taught, both
a notebook and, on request, a full book are available, and both are analytical.

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
  the tree does not track. It keeps its state under `learner/mastery/<topic>/`
  — **inside Calamity's synced `learner/` store**, never a repo-root `.mastery/`
  — so `/sync` (which runs `git add learner`) backs every bit of it up and
  carries it to the learner's other machines.
- The engine-backed `study` skill stays the **system of record** for verified,
  blind-checked items and the numbers on the roadmap, GATE board and recall
  queue. `mastery-coach` does not write its own inline questions into the event
  log. But so that deep coaching still *shows* there, it bridges tracked topics
  into the engine with `observe --tag coach` (what was taught) and `quick`
  (oral checks). Untracked or someone-else's sessions stay in `learner/mastery/`
  alone, so they never pollute the tracked learner's record.

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
set) and engine-independent. The two work **hand in hand**: `mastery-coach`
hands it each unit once taught and records every question it asked in
`recall.md`; `mastery-textbook` turns each unit into a chapter and every
question into a graded exercise with a worked solution, so nothing taught or
asked is left only in chat. The book lives beside the coach state, under
`learner/mastery/<topic>/book/`, so `/sync` saves it with the rest of
`learner/`; only its regenerable `book/build/` (PDF, page images, logs) is
git-ignored — the `.tex` sources, SVG and figure PDFs, and `book-state.md` are
kept and rebuild deterministically.

It **overlaps** the engine's `notes` skill and `notes-writer` agent (which also
produce LaTeX notes and a PDF per skill): use `mastery-textbook` for a
from-scratch, bestseller-standard book grown alongside `mastery-coach`; use
`notes`/`notes-writer` for the engine-tracked per-topic notes fragments and
skill PDFs. The two stores stay separate — `learner/mastery/` versus
`learner/notes/` — because `learner/notes/`'s `.gitignore` drops the `main.tex`
and PDF it rebuilds from fragments, which would delete the hand-authored book.

## The `build-it-yourself` skill (an added skill)

`.claude/skills/build-it-yourself/` turns a project into a learning path and
coaches the learner to build and **ship** it *with their own hands* — no AI
writing the project's code. **Reverse mode** tears down a source repository or a
shipped app (Electron, APK/IPA, CLI binary, web app, game) with read-only recon
(`scripts/repo_recon.py`: `git clone --filter=blob:none` and `gh api` reads, no
execution of the target's own scripts; `scripts/artifact_recon.py`: static
byte-scanning only, no network), recovers the architecture and teaches every
concept behind it. **Idea mode** architects the learner's own idea and coaches
the build. It respects authorisation and never bypasses DRM or extracts secrets.

It sits on top of `mastery-coach` and `mastery-textbook`, not beside them: it
decides *what* skills a project needs and *in what order*, hands the actual
teaching to `mastery-coach` at each node's tier, and adds chapters through
`mastery-textbook` on request. It follows the companion-skill contract above —
state under `learner/mastery/projects/<slug>/` (the cloned source and binaries
are scratch, never committed), skills learned recorded as `mastery-coach`
topics, and listed in `ADDED_SKILLS`.

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
