---
id: prisma
title: Prisma
track: 10x
group: data
prereqs: [postgresql, typescript, node]
tags: [js-ecosystem]
aliases: [orm, prisma client, migrations]
est_hours: 12
order: 40
summary: "A typed ORM for TypeScript: schema, migrations, client queries, relations, transactions, pitfalls."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- the schema file and data model
- migrations in development and in deployment
- client queries, relations, filtering, pagination
- transactions
- seeding; performance pitfalls (N+1, over-fetching); raw SQL when needed

# Boss

Put Prisma under an existing TypeScript API in place of hand-written SQL.

Passes when:

- migrations apply cleanly on an empty database
- list endpoints issue a bounded number of queries
- a multi-step write is atomic (tested)
