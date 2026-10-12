---
id: jest
title: Jest
track: 10x
group: frontend
prereqs: [testing-basics, npm-bundlers]
tags: [js-ecosystem]
weaves_into: [js-ecosystem]
aliases: [unit tests, vitest, testing library]
est_hours: 12
order: 100
summary: "Unit and integration tests in JavaScript and TypeScript: matchers, mocks, async tests, component tests."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- test structure, matchers, setup and teardown
- mocking modules, timers and the network
- asynchronous tests
- snapshot tests and their limits
- testing components with Testing Library
- coverage, watch mode, running in CI; Vitest as the Vite-native sibling

# Boss

Bring an untested JavaScript module and two components under test.

Passes when:

- the suite passes in CI
- coverage of the module is 80% or more
- no test depends on real time or the network

# Weave

JavaScript-ecosystem exercises after this one ship with tests.
