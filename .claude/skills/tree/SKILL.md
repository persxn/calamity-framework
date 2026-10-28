---
name: tree
description: "The skill tree: roadmap, prerequisites, routes to a goal, what next; add, swap, drop or restore a skill, skip what is known."
when_to_use: "When the learner asks what to learn next or what a skill needs, or wants their path or goals changed."
argument-hint: "[show <skill> | path <goal> | next | add <skill> | drop <skill> | goal <skill>]"
effort: high
---

# The skill tree

## Looking

| They ask | Run |
|---|---|
| what is there | `python3 engine/calamity.py dash roadmap --all-tracks` |
| about one skill | `python3 engine/calamity.py tree show <skill>` |
| how to get to X | `python3 engine/calamity.py tree path <skill>` |
| what next | `python3 engine/calamity.py tree suggest` |
| what their work leads to (the frontier, with reasons) | `python3 engine/calamity.py tree frontier` |
| a project that uses two skills together | `python3 engine/calamity.py project suggest`, then the examiner writes it as one `task` item listing the topics it prints |
| is there a skill for Y | `python3 engine/calamity.py find <words>` |

Print the output unchanged in a code block, then answer the question in a
line or two. A route is read layer by layer: skills in one layer can be
learnt in parallel, each layer needs the one before it. Where a route shows
a choice (language, framework, CI system), say which was assumed and that
enrolling in another member of the slot switches the route.

## Setting a goal

    python3 engine/calamity.py profile set goals mern-stack,kubernetes

Suggestions and routes then aim at it. Show `tree path <goal>` and the hour
estimate, and say it is an estimate.

## Changing

Read `framework/rules/tree-editing.md` first. In short:

- **A skill the tree lacks** ("teach me Rust", "add Angular as my
  frontend"): search with `find`; if it is truly absent, delegate the
  design to the `curriculum-architect` agent ("design a tree node for
  `<skill>`: id, track, group, prerequisites, slot, tags, weaves_into,
  scope, boss with runnable checks"), then create it with
  `python3 engine/calamity.py tree add ...`, write its `# Boss` in
  `learner/tree/<id>.md`, and run `tree check`.
- **An alternative** ("Fastify instead of Express", "Flutter instead of
  native Android"): enrol in the alternative; it shares a slot, so
  everything downstream accepts it. Offer to drop the one they will not use.
- **Already known** ("I know Git"): a placement test
  (`framework/rules/syllabus.md`), then
  `python3 engine/calamity.py placement <skill> ...`. Not taken on trust,
  not refused either.
- **Not wanted** ("skip Terraform"): `python3 engine/calamity.py tree drop <skill>`.
  If the engine lists skills that depend on it, show that list and what
  they will miss; run `tree drop <skill> --yes` only after the learner
  confirms.
- **Out of order** ("Docker now, Linux later"):
  `python3 engine/calamity.py enroll <skill> --force`, and say which
  prerequisites are unmet.
- **Different prerequisites or details**:
  `python3 engine/calamity.py tree set <skill> ...`.

After any change: `python3 engine/calamity.py tree check`, show the new
`tree path <goal>`, and record the reason with
`python3 engine/calamity.py observe "..." --skill <skill>`.

The learner decides what is on their path. Your part is to show what a
change costs or saves (hours on the route, skills that lose a prerequisite)
before it is made. Never edit files under `framework/tree/`.
