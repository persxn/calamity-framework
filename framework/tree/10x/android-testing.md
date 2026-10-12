---
id: android-testing
title: Android testing
track: 10x
group: mobile
prereqs: [android-data, testing-basics]
tags: [android]
aliases: [compose ui test, instrumented tests, espresso]
est_hours: 12
order: 50
summary: "Tests at every level of an Android app: unit, Compose UI, instrumented, with fakes, in CI."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- unit tests for ViewModels and repositories with fakes
- Compose UI tests
- instrumented tests on an emulator
- running the suite in CI

# Boss

Bring the app under test at all three levels.

Passes when:

- the suite passes in CI on an emulator
- the main journey has a UI test
- no test calls the real network
