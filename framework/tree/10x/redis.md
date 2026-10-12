---
id: redis
title: Redis
track: 10x
group: data
prereqs: [networking, "slot:language"]
tags: [database]
weaves_into: [backend-framework]
aliases: [cache, caching, pub/sub, rate limiting]
est_hours: 15
order: 50
summary: "An in-memory data store: data types, caching patterns and expiry, pub/sub and streams, rate limiting."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- data types: strings, hashes, lists, sets, sorted sets, streams
- caching patterns: cache-aside, write-through; TTLs; eviction
- cache invalidation and stampede protection
- pub/sub and streams
- rate limiting; distributed locks and their limits
- persistence and replication in outline

# Boss

Add caching and rate limiting to an API with Redis.

Passes when:

- a cached endpoint's latency drops and stays correct after a write
- the rate limiter holds under concurrent load
- a cold cache does not stampede the database
