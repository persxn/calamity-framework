---
id: fastify
title: Fastify
track: 10x
group: backend
prereqs: [node, rest-api-design]
slot: backend-framework
tags: [backend, backend-framework, runnable, js-ecosystem]
aliases: [fastify]
est_hours: 15
order: 30
summary: "A fast, schema-first Node framework: plugins and encapsulation, JSON-schema validation, hooks."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- routes, plugins and encapsulation
- schema-based validation and serialisation
- hooks and the request lifecycle; decorators
- logging with pino; testing with inject
- why it is faster, and when that matters

# Boss

Build the same CRUD REST API as the Express boss, on Fastify.

Passes when:

- every route declares a schema
- the test suite passes with `inject`
- errors follow the problem-details format
