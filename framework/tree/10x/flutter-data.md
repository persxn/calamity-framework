---
id: flutter-data
title: "Flutter data & networking"
track: 10x
group: mobile
prereqs: [flutter-state, rest-api-design]
tags: [flutter]
aliases: [dio, drift, sqflite, offline first]
est_hours: 20
order: 100
summary: "Local and remote data in Flutter: an HTTP client, JSON serialisation, a local database, offline cache."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- an HTTP client and JSON serialisation
- a local database (drift or sqflite); key-value storage
- offline-first sync
- error and loading states

# Boss

Connect the app to a REST API you built, with an offline cache.

Passes when:

- the app shows cached data with no network
- a write made offline syncs when the network returns
