---
id: backend-engineer
title: Backend capstone
track: 10x
group: milestones
kind: milestone
prereqs: [express, fastify, nestjs, nextjs, trpc, fastapi, postgresql, mongodb, prisma, redis, jwt, oauth2, graphql, websockets, openapi, queues-jobs]
aliases: [backend, back end, api capstone]
est_hours: 70
order: 17
summary: "Milestone: one product backend built from the services, stores and protocols of the whole backend path."
---

# Boss

A product backend made of services you would really split: a main API in a Node framework with an OpenAPI contract, a second service in FastAPI, a typed edge (tRPC or GraphQL) consumed by a Next.js app, live updates over WebSockets, PostgreSQL through Prisma, MongoDB for one document-shaped feature, Redis for caching and background jobs, and OAuth2 login issuing short-lived JWT access tokens.

Passes when:

- each service passes contract tests against its own schema (OpenAPI or GraphQL)
- integration tests run against real databases started in containers
- a load test meets the latency budget the tutor sets with the cache on, and shows the gap with it off
- access tokens expire and refresh correctly, and one user provably cannot read another user's data
- a failed background job is retried and, after the limit, parked where it can be inspected
