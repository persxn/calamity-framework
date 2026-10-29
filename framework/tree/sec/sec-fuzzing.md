---
id: sec-fuzzing
title: "Fuzzing & variant research"
track: sec
group: binary-exploitation
prereqs: [sec-memory-bugs, sec-research-method]
tags: [sec]
weaves_into: [sec]
aliases: [fuzzing, afl, libfuzzer, crash triage, variant analysis]
est_hours: 30
order: 40
summary: "Finding memory-safety bugs at scale and turning a pile of crashes into understood, deduplicated, minimised, root-caused findings with regression tests."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- coverage-guided and mutation-based fuzzing: how each explores inputs
- writing a fuzzing harness around a target function
- sanitisers as the oracle that turns silent corruption into a detected crash
- corpus construction and management
- crash deduplication and triage across many crashes
- input minimisation down to the smallest triggering case
- root-cause identification from a minimised crash
- variant analysis: finding siblings of a known bug
- patch-diff reading and regression testing
- reproducibility across versions and environments; responsible disclosure of what is found

# Boss

Fuzz a purpose-built or explicitly authorised target: build a harness, run it under sanitisers, and process the results into a small set of distinct, minimised, root-caused findings, each with a regression test. Write a report that separates demonstrated impact from speculation.

Passes when:

- the harness drives the target under a sanitiser and produces reproducible crashes
- crashes are deduplicated to distinct root causes, and each is minimised and explained
- each finding has a regression test that fails on the bug and passes on a fix
- the report follows a responsible-disclosure posture and marks every claim as tested or unverified

# Weave

Harness building, triage and minimisation are the daily work of the research capstone and of contributing fixes to real projects.
