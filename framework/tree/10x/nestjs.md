---
id: nestjs
title: NestJS
track: 10x
group: backend
prereqs: [typescript, express]
slot: backend-framework
tags: [backend, backend-framework, runnable, js-ecosystem]
aliases: [nest, nest.js]
est_hours: 35
order: 40
summary: "A structured TypeScript backend framework: modules, dependency injection, pipes, guards, interceptors."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- modules, controllers, providers; dependency injection
- pipes, guards, interceptors, exception filters
- configuration; database integration
- OpenAPI generation; validation with class-validator or zod
- testing with the testing module; e2e tests

# Boss

Build a modular service (two bounded modules, a database, auth guard) in NestJS.

Passes when:

- unit and e2e tests pass
- the OpenAPI document is generated from the code
- a guard protects the write routes
