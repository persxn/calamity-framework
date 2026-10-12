---
id: android-data
title: "Android data & networking"
track: 10x
group: mobile
prereqs: [android-state, rest-api-design]
tags: [android]
aliases: [room, retrofit, ktor, datastore, workmanager, offline first]
est_hours: 25
order: 40
summary: "Local and remote data: Room, DataStore, an HTTP client, offline-first sync, background work."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- Room: entities, DAOs, migrations
- DataStore for preferences
- an HTTP client (Retrofit or Ktor) with serialisation
- offline-first: the database as the source of truth, sync
- background work with WorkManager

# Boss

Connect the app to a REST API you built, with an offline cache.

Passes when:

- the app shows cached data with no network
- a write made offline syncs when the network returns
- a database migration is tested
