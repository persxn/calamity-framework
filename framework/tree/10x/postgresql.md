---
id: postgresql
title: PostgreSQL
track: 10x
group: data
prereqs: [sql-modelling, linux-shell]
tags: [database]
weaves_into: [backend-framework]
aliases: [postgres, psql, explain analyze]
est_hours: 25
order: 20
summary: "Running and tuning Postgres: roles, types, indexes, EXPLAIN, migrations, backups, pooling."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- psql; roles and privileges
- data types including JSONB and arrays
- indexes: B-tree, GIN, partial, composite; reading EXPLAIN ANALYZE
- migrations; zero-downtime changes in outline
- backup and restore; replication in outline
- connection pooling; common performance traps

# Boss

Take a slow, unindexed database the tutor provides and make its five worst queries fast.

Passes when:

- each query's plan and timing are shown before and after
- no query needs a sequential scan on a large table
- a backup is taken and restored into a fresh instance

# Weave

Backend exercises after this one persist to Postgres rather than to memory.
