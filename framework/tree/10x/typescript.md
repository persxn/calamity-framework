---
id: typescript
title: TypeScript
track: 10x
group: web-core
prereqs: [javascript]
tags: [language, runnable, js-ecosystem]
weaves_into: [js-ecosystem]
aliases: [ts, types]
est_hours: 25
order: 30
summary: "Static types for JavaScript: inference, unions, generics, strict mode, typed boundaries."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- annotations and inference; unions, intersections, literal types, narrowing
- interfaces and type aliases; generics; utility types
- discriminated unions and exhaustive checks
- typing functions, classes and async code
- modules, declaration files, tsconfig and strict mode
- typing third-party APIs; validating data at runtime boundaries (zod or similar)

# Boss

Convert the JavaScript boss app to strict TypeScript.

Passes when:

- `tsc --noEmit` passes with `strict: true`
- a lint rule forbids `any`, and the lint run is clean
- the existing tests still pass
- data from storage and from the network is validated before use

# Weave

Once learnt, every JavaScript-ecosystem exercise is written in TypeScript.
