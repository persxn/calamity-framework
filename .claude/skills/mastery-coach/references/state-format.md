# Learner state

State makes the coaching continuous: recall, weak-spot tracking and resuming mid-unit all depend on it. Keep it in plain markdown so it travels with the repo and works on any OS.

## Adopting an existing framework first

Before creating anything, look for an existing learner-state store in the repo: a framework README, a learner or progress directory, a skill tree file, or agent instructions that describe where progress lives (for example, the Calamity Framework). If you find one:

- Read its conventions and **write inside the part of it that gets backed up.** In the Calamity Framework that is `learner/` (and nothing else): `/sync` runs `git add learner`, so only files under `learner/` reach the learner's own repository and their other machines. Keep all mastery state and books under `learner/mastery/<topic-slug>/`, using the layout below. A repo-root `.mastery/` would work for one session but is never synced, so progress and materials there are silently lost — do not use it when a `learner/` store exists.
- Do **not** put the book under `learner/notes/`: that store belongs to the engine's `notes` skill and its `.gitignore` drops `main.tex` and the PDF (they are rebuilt from fragments). The mastery book's `main.tex` is hand-authored and must be kept, so it lives under `learner/mastery/`.
- Add only what the framework lacks, and say what you added.

Only if nothing exists, use the layout below at the repo root instead.

## Default layout

Inside Calamity, the root is `learner/mastery/` (synced). Standalone, the root is `.mastery/` at the repo root. The layout is the same:

```
<root>/
├── learner.md              # who the learner is, as they've told you
├── glossary.md             # every vocabulary term, across topics
└── <topic-slug>/           # (standalone: topics/<topic-slug>/)
    ├── curriculum.md       # numbered units, prereqs, status (see curriculum-design.md)
    ├── recall.md           # question bank with history and next_due — read by mastery-textbook
    ├── log.md              # one short entry per session
    ├── reading.md          # field reading assigned / done, with links
    └── book/               # the mastery-textbook LaTeX book, if one is being grown
```

Write every question you ask into `recall.md` with its worked answer, so the companion book can turn the whole bank into graded exercises.

## Recording into the engine (tracked topics)

When the repo is an engine-backed framework (Calamity) and the topic is one its skill tree tracks, the markdown state above is not enough on its own: the roadmap, recall queue, dashboards and the synced event log all come from the engine. So also tell the engine what happened, with its own CLI (`python3 engine/calamity.py <command>`):

- `observe "<what was taught / how it went>" --tag coach --skill <skill> [--topic <key>]` after each unit, so the coaching is on the record and visible to the next session.
- `quick <topic-key> pass|fail [--err KIND]` for an oral check when the learner explains an idea in their own words. It schedules the topic for review but never counts as mastery evidence — only the engine's blind-verified items do.

Do this only for the framework's own learner and the skills its tree tracks. A different person, or a topic the tree does not track, stays in `learner/mastery/` alone — never write someone else's ad-hoc session into the tracked learner's event log.

### learner.md

```markdown
# Learner
- who: (name or handle — who is being coached)
- is the framework's own learner: yes | no
- goals: (as stated)
- default mode: in-depth | balanced | brush-up
- hated or skipped topics: (as stated)
- known well (confirmed by diagnostic): …
- notes on how they learn best: (as stated or as they confirm)
```

`who` and `is the framework's own learner` keep a shared checkout honest. The default store (`learner/mastery/<topic>/`) is the framework's own learner; if you coach a **different** person in the same repo, namespace their state under `learner/mastery/people/<who-slug>/<topic>/` and never bridge their sessions into the engine — the roadmap, recall queue and event log belong to the one learner the engine tracks. A separate person studying seriously is better served by their own fresh install.

### log.md entry

```markdown
## 2026-10-25 — U07 Pointer arithmetic (chunks 1–3 of 5)
- taught: p+n scaling, array decay
- how: the "ruler vs. tape measure" model; traced `p+2` on an int array at 0x1000 → 0x1008
- shaky: pointer subtraction type → added R051
- recall run: R012 ✓, R018 ✗ (reset)
- next: chunk 4 (out-of-bounds UB), then U07 exercises
```

Log the **substance**, not just labels: the mental model, the example and the trace you actually used, and any analogy that landed. This is what `mastery-textbook` reads to reproduce the lesson faithfully in the chapter, so the book reflects what was really taught — not a fresh generic write-up. Keep the questions you asked, with answers, in `recall.md`; they become the chapter's exercises.

## Session routine

1. **Start**: read `learner.md`, the topic's `curriculum.md`, the latest `log.md` entry, and the items due in `recall.md`. Open with the due recall items, then resume exactly where the log says.
2. **During**: update unit status and recall history as you go, not only at the end.
3. **End**: write the log entry and set the next step.

Record only what the learner said or what happened in the session. Don't write guesses about their personality or abilities.
