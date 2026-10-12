# Changing the skill tree

The tree is the shipped skills in `framework/tree/` plus whatever this
learner has added, changed or dropped in `learner/tree/`. A learner's file
with the same id wins over the shipped one. Never edit `framework/tree/` for
one learner: framework updates would then overwrite, or be blocked by, their
changes.

## A skill file

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

| Field | Meaning |
|---|---|
| `id` | Lower-case letters, digits, `-`, `.`. Permanent: progress is stored under it. |
| `track`, `group` | Where it appears on the roadmap. Any name works; `framework/tree/tracks.md` orders the shipped ones. |
| `prereqs` | Skill ids, or `slot:<name>` to accept any one skill of a slot. A skill is unlocked when each prerequisite is ready, known or mastered. |
| `slot` | Membership of a group of alternatives. |
| `tags`, `weaves_into` | See "Weaving" below. |
| `kind: milestone` | A capstone with no topics: it is passed by its boss. |
| `optional: true` | Shown with `?` on the roadmap and suggested last. |
| `est_hours` | A planning estimate, used for routes and GATE triage. |

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
