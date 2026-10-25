# The skill map

The skill map answers: *what must this learner know, in what order, and how deeply, to build this project alone?* It turns a stack into a prerequisite graph, so nothing has to be filled in by the learner (or an AI) later.

## 1. Break the stack down, three layers deep

For every element of the stack (from the teardown or the design doc):

1. **Tool / technology**: Prisma, Express, React Query, Docker Compose, GitHub Actions…
2. **Concepts the project actually uses from it**: for Prisma, the schema language, migrations, relations, transactions, the generated client, connection pooling.
3. **Foundations under those concepts**: for Prisma, relational modelling, SQL joins, indexes, ACID; for React Query, HTTP caching, promises, stale-while-revalidate; for Docker, processes, namespaces, layered filesystems.

Also add the **techniques** found in the teardown (rate limiting, slug generation, JWT rotation, optimistic updates…) as their own nodes, **cross-cutting skills** the build needs (Git workflow, debugging with a debugger, reading docs, testing, the terminal), and the **shipping skills** for the target platform (packaging, signing, store or registry publishing, update mechanisms, CI releases, hosting). `build-path.md` lists them per platform.

## 2. Mark what is known

- Read mastery-coach state: topics marked done, and how well recall is going on them.
- For anything uncertain, run a 2–3 question diagnostic (mastery-coach style, from basic to sharp). Mark each node as **known**, **shaky** or **unknown**. Don't trust self-reporting alone.

## 3. Assign depth tiers

| Tier | Meaning | mastery-coach mode |
|---|---|---|
| **core** | The project's heart, and in line with the learner's goals. They should be able to explain it in an interview and build it again blind. | in-depth |
| **supporting** | Used meaningfully, but not the point. | balanced |
| **peripheral** | Needed, but small (one config file, one library call). | brush-up now, flagged for later mastery |

The learner can move anything up a tier. Mastery is the default for anything they care about.

## 4. Order and link to milestones

- Sort the graph topologically (foundations before concepts before tools).
- Then attach each node to the **first milestone that needs it** (`build-path.md`). Teaching happens just before that milestone. This keeps learning tied to immediate use, and spreads the map across the project instead of front-loading months of theory.
- Foundations shared by many nodes come first, as their own short units.

## 5. Write `skill-map.md`

```markdown
| # | Node | Layer | Tier | Status | Prereqs | First needed in |
|---|------|-------|------|--------|---------|-----------------|
| S01 | Relational modelling | foundation | core | shaky | — | M2 |
| S02 | SQL joins & indexes | foundation | core | unknown | S01 | M2 |
| S03 | Prisma schema & migrations | concept | core | unknown | S01,S02 | M2 |
| S11 | Sliding-window rate limiting | technique | supporting | unknown | S07 | M5 |
```

Add a Mermaid graph of the nodes and their prerequisite arrows (render it with `mmdc` to check). Present it to the learner as a short roadmap: "Before milestone 2 you'll learn S01–S03; before milestone 5, S11."

## 6. Handoff to mastery-coach

For each skill to teach, hand mastery-coach a scoped topic:

- **topic**: the node, such as "Prisma migrations"
- **depth tier → mode**
- **project context**: what the project uses it for, so mastery-coach's case studies and exercises can be *about similar situations*, **not** the project itself
- **must cover**: the specific concepts from step 1, plus everything mastery-coach's completeness checklist adds at that depth

When it's done, mark the node **known** and record which recall items cover it.
