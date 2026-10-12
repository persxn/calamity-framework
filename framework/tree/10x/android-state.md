---
id: android-state
title: "Android state & architecture"
track: 10x
group: mobile
prereqs: [android-core]
tags: [android]
aliases: [viewmodel, mvvm, hilt, stateflow]
est_hours: 25
order: 30
summary: "Apps that stay maintainable: ViewModel, state hoisting, StateFlow, one-way data flow, DI, repositories."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- ViewModel and state hoisting
- StateFlow and one-way data flow
- the repository pattern; layering
- dependency injection with Hilt

# Boss

Restructure the three-screen app around ViewModels and repositories.

Passes when:

- no business logic lives in composables
- ViewModels are unit-tested
- dependencies are injected, not constructed in place
