---
id: cpp
title: "Modern C++"
track: 10x
group: foundations
prereqs: [dev-environment]
weaves_into: [10x, ai]
aliases: [c++, cpp, modern c++, systems programming]
est_hours: 45
order: 50
summary: "Modern C++ to the depth systems and GPU work need: the memory model, the build, and debugging under sanitisers."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- the build: translation units, compiling and linking, a build file (CMake), warnings as errors
- value semantics, references and pointers; ownership and RAII; smart pointers
- the object and memory model: stack versus heap, lifetimes, what undefined behaviour is and why it bites
- headers and namespaces; the standard-library containers and algorithms
- templates and generic code in outline; `const` correctness; move semantics in outline
- debugging with a debugger and with sanitisers (address, undefined behaviour)
- measuring: timing a hot path and reading a profiler

# Boss

Write a small C++ program with a build file and tests: a command-line tool or a non-trivial data structure of the tutor's choosing.

Passes when:

- it builds with `-Wall -Wextra` and no warnings
- its tests pass
- it runs clean under the address and undefined-behaviour sanitisers
- a profiler run identifies the hot path and the result is explained in one paragraph

# Weave

Later systems and GPU exercises assume this C++: a clean build, a debugger, and sanitiser discipline.
