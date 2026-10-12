---
id: android-release
title: Android release
track: 10x
group: mobile
prereqs: [android-testing]
slot: android-app
tags: [android]
aliases: [play store, app bundle, signing, r8]
est_hours: 10
order: 60
summary: "Shipping: build variants, signing, shrinking, app bundles, the Play Console, crash reporting."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- build variants and flavours
- signing; R8 shrinking and obfuscation
- app bundles; versioning
- Play Console tracks; store listing requirements
- crash reporting; a release pipeline in CI

# Boss

Produce a signed release build and publish it to an internal testing track.

Passes when:

- the release bundle is signed and shrunk
- a CI job builds the release from a tag
- a crash appears in the reporting tool
