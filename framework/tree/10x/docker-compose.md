---
id: docker-compose
title: Docker Compose
track: 10x
group: devops
prereqs: [docker, networking]
weaves_into: [runnable, database]
aliases: [compose, multi-container]
est_hours: 8
order: 20
summary: "Several containers as one application: services, networks, volumes, health checks, profiles, overrides."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- services, networks, volumes
- environment files and secrets
- health checks and start order
- profiles; development and production overrides

# Boss

Bring up an API, its database and a cache with one command.

Passes when:

- `docker compose up` from a fresh clone reaches a healthy state
- data survives a restart
- the API waits for the database's health check
