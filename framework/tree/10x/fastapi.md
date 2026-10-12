---
id: fastapi
title: FastAPI
track: 10x
group: backend
prereqs: [python, rest-api-design]
slot: backend-framework
tags: [backend, backend-framework, runnable]
aliases: [pydantic, async python api]
est_hours: 25
order: 70
summary: "Typed, async Python APIs: path operations, pydantic models, dependency injection, auth, testing."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- path operations, parameters, pydantic models
- dependency injection; settings
- async endpoints and when to use them
- authentication dependencies; background tasks
- database access with an async driver or SQLAlchemy
- testing with the test client; the generated OpenAPI

# Boss

Build a CRUD REST API with validation, auth on write routes and tests.

Passes when:

- `pytest` passes
- the generated OpenAPI passes lint
- invalid input returns a 422 with field errors
- write routes refuse anonymous calls
