---
id: sec-memory-bugs
title: "Memory-safety bug classes"
track: sec
group: binary-exploitation
prereqs: [sec-arch-asm]
tags: [sec]
weaves_into: [sec]
aliases: [memory safety, buffer overflow, use after free, vulnerability classes]
est_hours: 30
order: 20
summary: "The memory-safety vulnerability classes by their root cause: what the bug is, under what conditions it occurs, and how to reduce it to a minimal reproduction."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- out-of-bounds reads and writes, and the boundary that was crossed
- stack and heap buffer overflows, by their cause rather than a single recipe
- use-after-free and double-free, and the allocator state that makes them possible
- integer overflow and truncation as the root of a later memory error
- type confusion and the assumptions it breaks
- format-string flaws: how an attacker-controlled format reaches a dangerous call
- races and concurrency errors that corrupt memory
- how a heap allocator lays out and reuses memory, in outline
- root-cause analysis: separating the crash from the defect that caused it
- building a minimal reproduction for each class under a sanitiser

# Boss

Write (or take) a set of small programs, one per memory-safety class in scope, each with the bug seeded deliberately. For each, produce a minimal reproduction, show the sanitiser's diagnosis, and write the root cause: what state, what input and what assumption combined to produce it.

Passes when:

- each program's bug is reproduced on demand and confirmed by a sanitiser or a debugger
- each write-up names the class correctly and distinguishes the symptom from the root cause
- at least one case shows an integer or truncation error leading to a later memory error
- the learner explains, for one case, why a memory-safe language would have prevented it

# Weave

These classes are the raw material for exploitation concepts and for the fuzzing work that finds them at scale.
