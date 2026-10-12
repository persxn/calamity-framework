---
id: tanstack-query
title: TanStack Query (React Query)
track: 10x
group: frontend
prereqs: [react, rest-api-design]
tags: [frontend, js-ecosystem]
aliases: [react query, react queries, server state]
est_hours: 12
order: 60
summary: "Server state done right: query keys, caching and staleness, mutations, invalidation, optimistic updates."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- server state versus client state
- queries, query keys, caching, stale time and garbage collection
- mutations, invalidation, optimistic updates and rollback
- pagination and infinite queries; prefetching
- retries, error handling, devtools

# Boss

Replace hand-rolled data fetching in the React app with TanStack Query.

Passes when:

- remounting a screen does not repeat a fresh request
- an optimistic update rolls back on a forced server error (covered by a test)
- loading and error states are handled on every query
