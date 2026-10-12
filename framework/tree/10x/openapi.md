---
id: openapi
title: OpenAPI
track: 10x
group: api
prereqs: [rest-api-design]
weaves_into: [backend-framework, api]
aliases: [swagger, api spec, api documentation]
est_hours: 8
order: 20
summary: "Describe an API precisely: paths, schemas, examples; generate docs, clients and mocks; lint the contract."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- OpenAPI 3.1 structure: paths, operations, schemas, components
- modelling parameters, request bodies, responses and examples
- generating documentation (Swagger UI, Redoc), clients and server stubs
- linting with Spectral; contract testing against a mock (Prism)

# Boss

Write the full OpenAPI description of the API designed in the REST boss, then generate docs and a typed client.

Passes when:

- the spec validates and passes lint
- the generated client compiles
- the client's calls succeed against a mock server
