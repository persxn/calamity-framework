---
id: graphql
title: GraphQL
track: 10x
group: api
prereqs: [rest-api-design, "slot:backend-framework"]
tags: [api]
aliases: [apollo, schema, resolvers]
est_hours: 20
order: 30
summary: "A typed query language for APIs: schemas, resolvers, the N+1 problem, pagination, auth, trade-offs with REST."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- schema, types, queries, mutations, subscriptions
- resolvers; the N+1 problem and dataloaders
- pagination with connections; error handling
- authentication and authorisation in resolvers
- when GraphQL is the better fit and when it is not

# Boss

Expose an existing REST domain through a GraphQL API.

Passes when:

- a nested query triggers a bounded number of database queries
- schema and resolvers are covered by tests
- unauthorised fields are refused
