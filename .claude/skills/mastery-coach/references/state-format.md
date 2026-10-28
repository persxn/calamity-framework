# The coach's narrative state

The engine is the record of everything that counts: what was taught (`ask --taught`), every answer,
the schedule, where each topic stands, when a unit is done (`unit`). The coach keeps beside it only
the narrative the engine cannot hold — the story of the teaching, which the book is written from.
It is plain Markdown under `learner/coach/<topic-slug>/`, inside `learner/`, the only folder `/sync`
commits, so it travels to the learner's other machines. Books go to `learner/books/<topic-slug>/`
(mastery-textbook), projects to `learner/projects/<slug>/` (build-it-yourself). Never a repo-root
`.mastery/`, which is not backed up, and never `learner/notes/`, which belongs to the notes skill.

```
learner/coach/<topic-slug>/
├── learner.md      why they are learning it, the mode, what they hate or skipped, how it is going
├── curriculum.md   the units: their topic keys, prerequisites, surface, field reading, mode
├── log.md          one entry per session: what was taught and how (models, examples, traces)
├── glossary.md     every term, as it was defined
├── reading.md      field reading assigned and done, with links checked when assigned
└── seeds.md        question ideas for the examiner: type and topic keys, never an answer
```

Write after every chunk, not at the end: a session can be cut off.

## curriculum.md

```markdown
# Docker — curriculum (mode: in-depth)
skill: docker

## U03 — Images are filesystem diffs
- topics: docker/images, docker/layers
- prereqs: U01 (processes), U02 (namespaces)
- surface: docker image ls|inspect|history, --format, --no-trunc
- field reading: OCI image spec, layer section
```

Balanced mode is written here (`mode: balanced`); the engine sees it as `mastery`. Brush-up is the
engine's `brushup` mode (`enroll <skill> --mode brushup`).

## log.md

```markdown
## 2026-10-25 — U07 Pointer arithmetic (chunks 1–3 of 5)
- taught: p+n scaling, array decay (ask --taught: c-pointers/arithmetic, 35 min)
- how: the "ruler vs. tape measure" model; traced `p+2` on an int array at 0x1000 → 0x1008
- shaky: pointer subtraction type → seed added
- engine: 4 answers, 3 right; unit U07 open (bounds not consolidated)
- next: chunk 4 (out-of-bounds UB), then U07's items
```

Log the substance — the mental model, the example and the trace actually used, the analogy that
landed — because the book reproduces the lesson from it. Record only what was said or happened, never
guesses about the learner.

## Someone else in the same checkout

The engine's log belongs to the framework's own learner. To coach someone else here, keep their
narrative under `learner/coach/people/<who-slug>/<topic>/`, ask your formative questions only, and
record nothing in the engine; a person studying seriously is better served by their own clone.
