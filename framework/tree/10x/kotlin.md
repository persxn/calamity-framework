---
id: kotlin
title: Kotlin
track: 10x
group: mobile
prereqs: [dev-environment]
slot: language
tags: [language, runnable]
weaves_into: [android]
aliases: [kt, coroutines]
est_hours: 35
order: 10
summary: "The language of native Android: null safety, data and sealed classes, lambdas, coroutines and flows."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- syntax, types, null safety
- classes, data classes, sealed classes, objects
- collections and lambdas; extension functions
- coroutines and flows in outline
- Gradle basics; testing

# Boss

Model a small domain in Kotlin with tests, as a command-line program.

Passes when:

- the Gradle build and tests pass
- no `!!` operator is used
- state changes are modelled with sealed types
