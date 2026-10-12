---
id: trpc
title: tRPC
track: 10x
group: api
prereqs: [rest-api-design, typescript, node]
tags: [api, js-ecosystem]
aliases: [typesafe api, end-to-end types]
est_hours: 10
order: 60
summary: "End-to-end type safety without a schema file: routers, procedures, zod validation, React Query client."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- the idea: the server's types are the contract
- routers and procedures; input validation with zod
- context and middleware; auth
- the client and its React Query integration
- where tRPC fits and where a public REST API is still needed

# Boss

Build a small full-stack TypeScript feature on tRPC.

Passes when:

- changing a procedure's output breaks the client at compile time
- inputs are validated
- protected procedures refuse anonymous calls
