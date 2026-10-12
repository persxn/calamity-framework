---
id: rest-api-design
title: REST API design
track: 10x
group: api
prereqs: [networking]
weaves_into: [backend-framework, api]
aliases: [rest, api design, http api, restful]
est_hours: 15
order: 10
summary: "Designing HTTP APIs people can live with: resources, methods, status codes, errors, pagination, versioning, idempotency, rate limits."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- resources and URIs; HTTP methods and their safe and idempotent semantics
- status codes and a consistent error format (problem details)
- request and response design: filtering, sorting, pagination (offset and cursor)
- versioning and backwards compatibility
- idempotency keys, rate limiting, caching headers, ETags
- where authentication goes; CORS
- designing the contract before the code

# Boss

Design an API for a domain the tutor names (bookings, orders, a library): resources, endpoints, errors, pagination and idempotency, as a written design plus an OpenAPI stub.

Passes when:

- every endpoint lists method, success status and error cases
- pagination and idempotency are specified where they apply
- the stub passes a Spectral lint ruleset
- a reviewer can answer 'what happens if I retry this?' for every write

# Weave

Every backend-framework exercise is judged against these rules, not only on whether it runs.
