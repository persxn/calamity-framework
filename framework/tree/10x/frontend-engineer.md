---
id: frontend-engineer
title: Frontend capstone
track: 10x
group: milestones
kind: milestone
prereqs: [typescript, eslint-prettier, "slot:frontend-framework", tailwind, "slot:animation", "slot:state-management", tanstack-query, jest, "slot:e2e-testing", a11y-performance]
aliases: [frontend, front end, spa capstone]
est_hours: 50
order: 14
summary: "Milestone: a typed, tested, accessible single-page application with real state and motion."
---

# Boss

Build a production-grade single-page application against an API: TypeScript throughout, a client store and a server-state cache with clear roles, styled with utility classes, animated transitions, and tests at unit and end-to-end level.

Passes when:

- type check, lint and format checks are clean in the pipeline
- unit and end-to-end suites pass against a mocked and a real API
- Lighthouse performance and accessibility are 90 or more on the main route
- server data is never copied into the client store, and the learner can say why
- animations respect the reduced-motion setting
