---
id: dev-environment
title: "Developer environment & tooling"
track: 10x
group: foundations
aliases: [setup, tooling, editor, vs code]
est_hours: 8
order: 10
summary: "The ground floor for a novice: how programs run, an editor, a terminal, runtimes, reading errors."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- how a program runs: source code, interpreter or compiler, process, files, PATH
- editor fluency (VS Code or similar): multi-cursor, search, integrated terminal, extensions, settings
- installing runtimes with a version manager (Node, Python, a JDK) and your OS package manager
- reading error messages and stack traces from the bottom up
- a debugging routine: reproduce, isolate, form a hypothesis, fix, confirm
- browser devtools at a glance: elements, console, network
- finding answers: official documentation first, then issue trackers; asking a precise question

# Boss

Set up a working machine profile from nothing: install a runtime through a version manager, create a tiny project, run it, break it on purpose and fix it by reading the stack trace. Write a README another person can follow.

Passes when:

- the runtime's `--version` prints from a new terminal
- the project runs from a fresh clone by following only its README
- the planted bug is explained in one sentence that names the file and line
