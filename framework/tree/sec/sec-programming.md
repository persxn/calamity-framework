---
id: sec-programming
title: "Programming & debugging for security"
track: sec
group: foundations
prereqs: [dev-environment]
tags: [sec]
weaves_into: [sec]
aliases: [security programming, c for security, shell scripting, debugging foundations]
est_hours: 35
order: 10
summary: "Read, write and debug C/C++, shell and PowerShell well enough to see how a program's runtime and machine code become security properties."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- C/C++ for systems work: pointers, references, ownership and object lifetimes
- the stack, the heap, and what the compiler is allowed to assume (undefined behaviour)
- integer representation, signedness, overflow and truncation, and where they bite
- file descriptors, streams, buffers and the system-call boundary
- processes, threads and the basics of synchronisation
- the build: translation units, linking, and reading what the compiler emits
- debugging and tracing: a debugger, address and undefined-behaviour sanitisers
- Bash scripting for automation; PowerShell fundamentals for Windows work
- when Go or Rust is the better tool, and why memory-safe languages change the threat model
- Git, tests and reproducible builds as the baseline for any tool you write

# Boss

Write a small C program with a deliberate memory-safety mistake and a Bash harness around it: the harness builds it twice (once plain, once under the address and undefined-behaviour sanitisers), runs it on a set of inputs, and reports which build caught the fault and where.

Passes when:

- the plain build runs without an obvious crash on the benign input, and the sanitiser build reports the exact fault and source line
- the learner explains, in their own words, what the compiler assumed and why the bug is undefined behaviour rather than merely a wrong answer
- the harness is idempotent and exits non-zero when the sanitiser build reports a fault
- `shellcheck` reports nothing on the harness

# Weave

Every later security exercise assumes this: a clean build, a debugger, sanitiser discipline, and a scripted, reproducible way to run things.
