---
id: testing-basics
title: Testing fundamentals
track: 10x
group: engineering
prereqs: ["slot:language"]
weaves_into: [runnable]
aliases: [unit testing, tdd, test pyramid, mocks]
est_hours: 10
order: 10
summary: "Why and how to test, in any language: the pyramid, arrange-act-assert, test doubles, TDD, regression tests."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- why test; unit, integration and end-to-end tests; the pyramid
- arrange, act, assert; naming tests
- test doubles: stubs, mocks, fakes
- what to test and what not to; coverage as a signal, not a goal
- the test-driven loop; a regression test for every bug

# Boss

Bring an untested module under test, including a regression test for a bug the tutor plants.

Passes when:

- the regression test fails before the fix and passes after
- coverage of the module is 80% or more
- tests do not depend on each other's order

# Weave

Every runnable exercise after this one comes with tests.
