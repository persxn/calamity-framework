---
id: express
title: Express.js
track: 10x
group: backend
prereqs: [node, rest-api-design]
slot: backend-framework
tags: [backend, backend-framework, runnable, js-ecosystem]
aliases: [express, expressjs, middleware]
est_hours: 20
order: 20
summary: "The minimal Node web framework: routing, middleware, validation, error handling, structure, tests."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- routing; the middleware chain; request and response
- input validation; error-handling middleware
- structuring an app in layers; configuration
- cookies and sessions in outline; CORS; security headers
- testing with supertest

# Boss

Build a CRUD REST API with validation, a consistent error format and tests.

Passes when:

- the supertest suite passes
- errors follow the problem-details format
- its OpenAPI description passes lint
- invalid input never reaches a handler
