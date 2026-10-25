# Learner state

State makes the coaching continuous: recall, weak-spot tracking and resuming mid-unit all depend on it. Keep it in plain markdown so it travels with the repo and works on any OS.

## Adopting an existing framework first

Before creating anything, look for an existing learner-state store in the repo: a framework README, a learner or progress directory, a skill tree file, or agent instructions that describe where progress lives (for example, the Calamity Framework). If you find one:

- Read its conventions and write in *its* format and locations.
- Map this skill's concepts onto its structure: curriculum units become its skill-tree nodes or topics, the recall bank becomes its revision or question store, and the glossary goes wherever it keeps notes.
- Add only what it lacks, and say what you added.

Only if nothing exists, use the layout below.

## Default layout

```
.mastery/
├── learner.md              # who the learner is, as they've told you
├── glossary.md             # every vocabulary term, across topics
└── topics/
    └── <topic-slug>/
        ├── curriculum.md   # numbered units, prereqs, status (see curriculum-design.md)
        ├── recall.md       # question bank with history and next_due
        ├── log.md          # one short entry per session
        └── reading.md      # field reading assigned / done, with links
```

### learner.md

```markdown
# Learner
- goals: (as stated)
- default mode: in-depth | balanced | brush-up
- hated or skipped topics: (as stated)
- known well (confirmed by diagnostic): …
- notes on how they learn best: (as stated or as they confirm)
```

### log.md entry

```markdown
## 2026-10-25 — U07 Pointer arithmetic (chunks 1–3 of 5)
- taught: p+n scaling, array decay
- shaky: pointer subtraction type → added R051
- recall run: R012 ✓, R018 ✗ (reset)
- next: chunk 4 (out-of-bounds UB), then U07 exercises
```

## Session routine

1. **Start**: read `learner.md`, the topic's `curriculum.md`, the latest `log.md` entry, and the items due in `recall.md`. Open with the due recall items, then resume exactly where the log says.
2. **During**: update unit status and recall history as you go, not only at the end.
3. **End**: write the log entry and set the next step.

Record only what the learner said or what happened in the session. Don't write guesses about their personality or abilities.
