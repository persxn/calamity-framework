---
id: flutter-release
title: Flutter release
track: 10x
group: mobile
prereqs: [flutter-data, testing-basics]
slot: android-app
tags: [flutter]
aliases: [play store, app bundle, signing]
est_hours: 10
order: 110
summary: "Shipping a Flutter app to Android: flavours, signing, app bundles, the Play Console, CI."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- flavours and build modes
- signing; app bundles; versioning
- Play Console tracks
- integration tests; a release pipeline in CI

# Boss

Produce a signed release build and publish it to an internal testing track.

Passes when:

- the release bundle is signed
- integration tests pass in CI
- a CI job builds the release from a tag
