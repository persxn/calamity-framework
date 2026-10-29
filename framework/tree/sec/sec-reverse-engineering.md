---
id: sec-reverse-engineering
title: "Reverse engineering"
track: sec
group: cross-cutting
prereqs: [sec-arch-asm]
optional: true
tags: [sec]
weaves_into: [sec]
aliases: [reverse engineering, static analysis, dynamic analysis, disassembly]
est_hours: 30
order: 20
summary: "Understanding unfamiliar software from the binary: formats and assembly, static and dynamic analysis, and comparing versions to find what changed."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill. Targets are the
learner's own software or software they are licensed to analyse.

- executable formats and the assembly they contain
- disassembly and navigating an unfamiliar binary
- debugging to observe behaviour dynamically
- static analysis of control and data flow
- combining static and dynamic views
- reconstructing a program's behaviour and intent
- binary comparison across versions
- investigating a software component's provenance

# Boss

Take a binary whose source you do not consult, and recover a specific piece of its behaviour: what one function does, what input drives it, and how it decides an outcome, confirming your reconstruction by running it under a debugger.

Passes when:

- the recovered behaviour is confirmed dynamically, not only asserted from the disassembly
- static and dynamic evidence agree, or the discrepancy is explained
- the learner explains how they located the relevant function in the binary
- the analysis stays within owned or licensed software
