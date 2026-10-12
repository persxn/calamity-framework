---
id: nextjs
title: Next.js
track: 10x
group: backend
prereqs: [react, node]
tags: [frontend, backend, js-ecosystem, runnable]
aliases: [next, next.js, app router, ssr]
est_hours: 35
order: 50
summary: "Full-stack React: the App Router, server and client components, data fetching and caching, rendering modes."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- the App Router: layouts, pages, loading and error states
- server components and client components; the boundary between them
- data fetching and caching; revalidation
- route handlers and server actions
- rendering modes: static, dynamic, incremental
- middleware; images, fonts, metadata
- deployment and environment configuration

# Boss

Build a content-plus-dashboard site: static marketing pages, a dynamic authenticated dashboard, one server action.

Passes when:

- the production build succeeds with no client-only leakage errors
- static pages are prerendered
- the dashboard is not cached across users
- Lighthouse performance is 90 or more on the static pages
