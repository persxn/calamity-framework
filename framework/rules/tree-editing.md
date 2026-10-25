# Changing the skill tree

The tree is the shipped skills in `framework/tree/` plus whatever this
learner has added, changed or dropped in `learner/tree/`. A learner's file
with the same id wins over the shipped one. Never edit `framework/tree/` for
one learner: framework updates would then overwrite, or be blocked by, their
changes.

## A skill file

A skill is one Markdown file: front matter, then sections. Four shapes are in
use. They share a core and differ by what the track needs; pick the shape that
matches the track you add to, or the nearest one for a new track.

**Shared front matter**, in every shape:

| Field | Meaning |
|---|---|
| `id` | Lower-case letters, digits, `-`, `.`. Permanent: progress is stored under it. |
| `title` | What the learner sees. |
| `track`, `group` | Where it appears on the roadmap. Any name works; `framework/tree/tracks.md` orders the shipped ones. An unlisted group is appended after the listed ones. |
| `order` | Position within the group, ascending. |
| `summary` | One line: what mastering it means. |
| `aliases` | Other names it answers to in `find`. |

### Shape 1 — a skill taught from a syllabus (`10x`, `ai`)

Scope, a runnable boss, optional weaving, and `# Topics` when it ships a
syllabus. Extra fields: `prereqs`, `slot`, `tags`, `weaves_into`, `est_hours`.

```markdown
---
id: htmx
title: htmx
track: 10x
group: frontend
prereqs: [html-css, slot:backend-framework]
slot: frontend-framework
tags: [frontend]
weaves_into: [frontend]
aliases: [hypermedia]
est_hours: 15
order: 45
summary: Server-rendered interactivity without a JavaScript framework.
---

# Scope

- what mastery covers, one line each; the learner's syllabus is built from this

# Boss

The project or test that proves the skill.

Passes when:

- a check that can be run
- another check that can be run

# Weave

How this skill should show up inside later exercises.
```

A `# Topics` section may follow `# Scope`; its line format (`## key | Title`,
`level:`, `needs:`, `band:`) is in `framework/rules/syllabus.md`.

### Shape 2 — a milestone or capstone

`kind: milestone` and a boss only: no scope, no topics. `prereqs` are the
skills it proves; it is passed by its boss. A capstone takes a whole group's
skills as prerequisites and a project boss. A rating marker (the `cp` variant)
instead carries `rating:` and a contest boss.

```markdown
---
id: frontend-engineer
title: Frontend engineer
track: 10x
group: milestones
kind: milestone
prereqs: [react, tailwind, tanstack-query, playwright]
aliases: [frontend milestone]
est_hours: 40
order: 10
summary: "Build, test and ship one production-standard frontend alone."
---

# Boss

One project that uses the whole group.

Passes when:

- a check that can be run
- another check that can be run
```

### Shape 3 — a competitive-programming skill (`cp`)

A `band` (the Codeforces rating it is expected from) and `cf_tags` (Codeforces
problem tags) in place of `slot`; practice comes from `cf recommend`, so the
file has a band note, a contest-set boss, and topics.

```markdown
---
id: cp.graphs-basics
title: "Graphs: traversal"
track: cp
group: core
prereqs: [cp.stl, cp.complexity]
tags: [cp]
weaves_into: [cp]
aliases: [graphs, bfs, dfs]
cf_tags: [graphs, dfs and similar]
band: 1200
est_hours: 30
order: 30
summary: "Reachability, shortest unweighted paths, components, cycles and order."
---

`band` is the Codeforces rating from which this skill is expected; a topic's own `band` marks a part that belongs to a later rating. Practice problems come from `cf recommend --skill cp.graphs-basics`.

# Boss

A timed set under contest conditions: 5 unseen problems rated 1300–1600 in 120 minutes, tags hidden.

Passes when:

- after `cf sync`, at least 4 of 5 show an accepted verdict inside the sitting
- each accepted solution is explained in two sentences: the idea and its complexity

# Topics

## representation | Representing a graph
level: 1
- adjacency lists from an edge list; directed versus undirected
```

### Shape 4 — a GATE subject (`gate`, `gate-cs`, `gate-da`)

The official syllabus is the source of truth, so the file records where it came
from (`source_url`, `syllabus_year`), its weight (`marks`, `marks_source`) and
its `paper`. It has topics only: no scope, no boss (the mock and past papers
test it). GATE subjects do not weave. See `framework/rules/gate-planning.md`.

```markdown
---
id: gate.cs.toc
title: Theory of Computation
track: gate-cs
group: core
tags: [gate]
aliases: [toc, automata]
paper: CS
marks: 8
marks_source: prior
source_url: "https://gate2027.iitm.ac.in/static/doc/GATE2027_Syllabus/CS_GATE2027_Syllabus.pdf"
est_hours: 55
syllabus_year: 2027
order: 50
summary: "Regular and context-free languages, Turing machines and undecidability."
---

Topics follow the official GATE <year> syllabus for <paper> (read <date>). If the official document and this file ever differ, the official document wins: write the corrected list to `learner/syllabus/gate.cs.toc.md`. The marks figure is a planning prior; replace it with `gate weight`.

# Topics

## regular-expressions | Regular expressions
level: 2
- write an expression for a language; convert between expressions and automata
```

**Field reference** (beyond the shared set):

| Field | Shapes | Meaning |
|---|---|---|
| `prereqs` | 1, 2, 3 | Skill ids, or `slot:<name>` to accept any one skill of a slot. Unlocked when each is ready, known or mastered. |
| `slot` | 1 | Membership of a group of interchangeable alternatives. |
| `tags`, `weaves_into` | 1, 3 | See "Weaving" below. |
| `est_hours` | all | A planning estimate for routes and GATE triage. Optional on milestones and rating markers. |
| `kind: milestone` | 2 | A capstone with no topics: passed by its boss. |
| `rating` | 2 (`cp`) | The Codeforces rating a rating-marker milestone proves. |
| `optional: true` | 1 | Shown with `?` on the roadmap and suggested last. |
| `band`, `cf_tags` | 3 | Codeforces rating and problem tags; drive `cf recommend`. |
| `paper` | 4 | `CS` or `DA`: which GATE paper. |
| `marks`, `marks_source` | 4 | Expected marks, and whether `official` or a `prior`. |
| `source_url`, `syllabus_year` | 4 | The official syllabus PDF and its year. |
| `overlaps` | 4 | Ids whose topics overlap (e.g. a subject shared across papers), so the engine does not double-count. |

## Adding a skill

Have the `curriculum-architect` agent design it, then:

    python3 engine/calamity.py tree add --id htmx --title "htmx" --track 10x --group frontend \
        --prereqs html-css,slot:backend-framework --slot frontend-framework --tags frontend \
        --weaves-into frontend --hours 15 --summary "Server-rendered interactivity without a JavaScript framework." \
        --scope "- attributes for requests and swaps
    - partial responses from the server"

The engine writes `learner/tree/htmx.md` and refuses the change if it would
break the tree (unknown prerequisite, a cycle). Then open the file and write
the `# Boss` section with checks that can be run, and `# Weave` if it
applies. Finish with `python3 engine/calamity.py tree check`.

Before adding, search: `python3 engine/calamity.py find <words>`. The skill
may already exist under another name or alias.

## Alternatives: slots

A slot holds interchangeable skills; a prerequisite written `slot:<name>` is
met by any one of them. Routes follow whichever member the learner is
already on.

| Slot | Shipped members |
|---|---|
| `language` | javascript, python, java, kotlin, dart |
| `frontend-framework` | react, vue, svelte |
| `state-management` | redux |
| `animation` | framer-motion, gsap |
| `e2e-testing` | playwright, cypress |
| `backend-framework` | express, fastify, nestjs, fastapi, spring-boot |
| `ci` | github-actions, jenkins |
| `android-app` | android-release (native Kotlin route), flutter-release (Flutter route) |
| `rag` | rag-qdrant, rag-vectorless |

To offer another alternative (Angular, Django, GitLab CI), add it with
`--slot <name>`. To make a learner's route use it, they enrol in it.

## Weaving

A skill offers its topics for embedding in exercises of other skills through
`weaves_into`. Each entry is matched against the skill being studied: its
id, its group, its track, and its tags. `any` matches everything.

- `docker` has `weaves_into: [runnable]`, and `java` is tagged `runnable`:
  a Java exercise can require a Dockerfile.
- `linux-shell` and `git-gh` weave into the whole `10x` and `ai` tracks.
- Competitive-programming skills weave into the `cp` track.
- GATE subjects do not weave: exam questions stay single-subject.

Shipped tags: `runnable` (produces a program or service worth
containerising and testing), `language`, `js-ecosystem`, `frontend`,
`backend`, `backend-framework`, `database`, `api`, `android`, `flutter`,
`ai`, `ml`, `llm`, `math`, `cp`, `gate`. Give a new skill the tags that
describe it, and `weaves_into` only where practitioners really combine the
two.

## Changing a skill

    python3 engine/calamity.py tree set <skill> --prereqs a,b --hours 30
    python3 engine/calamity.py tree set <skill> --slot ci
    python3 engine/calamity.py tree set <skill> --clear-slot --not-optional

For a shipped skill this writes a full copy into `learner/tree/` with the
change applied; edit that copy for anything `tree set` has no flag for
(scope, boss). Removing a prerequisite unlocks the skill; it does not teach
what the prerequisite covered, so say what will be missing.

## Dropping and restoring

    python3 engine/calamity.py tree drop <skill>

- If other skills depend on it, the engine refuses and lists them. Show the
  learner that list and what each will be missing. Only after they confirm:
  `tree drop <skill> --yes`.
- A dropped prerequisite counts as met for the skills that needed it.
  Progress on the dropped skill is kept.
- `python3 engine/calamity.py tree restore <skill>` brings it back.

Dropping is how a learner removes a skill from their path, for example
`vue` and `svelte` when React is their framework, or `terraform` when
infrastructure is not their goal. It is their decision; give the numbers
(`tree path <goal>` before and after) and record it.

## Skipping ahead and reordering

- Prerequisites are the only ordering. Skills in the same layer of
  `tree path <goal>` can be studied in parallel.
- To take a skill before its prerequisites:
  `python3 engine/calamity.py enroll <skill> --force`. The engine notes the
  unmet prerequisites; weave their basics into early exercises.
- To skip a skill the learner already has, use a placement test
  (`framework/rules/syllabus.md`).

## After any change

Run `tree check`, show the learner `tree path <their goal>`, and record why
the change was made: `python3 engine/calamity.py observe "dropped terraform: not doing infrastructure" --skill terraform`.
