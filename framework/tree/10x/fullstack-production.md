---
id: fullstack-production
title: Production full-stack capstone
track: 10x
group: milestones
kind: milestone
prereqs: ["slot:backend-framework", "slot:frontend-framework", postgresql, jwt, docker-compose, "slot:ci", "slot:e2e-testing", openapi]
aliases: [full stack, production app, capstone]
est_hours: 60
order: 20
summary: "Milestone: a tested, documented, containerised application that deploys through a pipeline."
---

# Boss

Build an application to production standard: typed API with an OpenAPI contract, relational database with migrations, token auth, a frontend, end-to-end tests, containers, and a pipeline that deploys it.

Passes when:

- the pipeline is green: lint, unit, integration and end-to-end tests
- `docker compose up` from a fresh clone reaches a healthy state
- the deployed endpoint answers over HTTPS
- the OpenAPI contract matches the running API (contract test)
