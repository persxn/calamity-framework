---
id: react
title: React
track: 10x
group: frontend
prereqs: [html-css, javascript, npm-bundlers]
slot: frontend-framework
tags: [frontend, js-ecosystem, runnable]
aliases: [reactjs, react.js, hooks, jsx]
est_hours: 50
order: 10
summary: "Components, state and effects, hooks, routing, data fetching and performance in React."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- components, JSX, props, state; how rendering and re-rendering work
- hooks: useState, useEffect, useRef, useMemo, useCallback, useContext, custom hooks
- lists and keys; forms (controlled and uncontrolled); lifting state
- data fetching patterns, Suspense in outline, error boundaries
- routing with React Router; code splitting
- performance: memoisation, the profiler; stale closures and effect dependencies
- component design: composition, accessibility

# Boss

Build a multi-route React app that consumes a public API (for example a film browser): search, pagination, a detail route, and one optimistic update.

Passes when:

- component tests pass
- the browser console shows no warnings
- Lighthouse performance is 85 or more on the production build
- the app is usable with the keyboard alone
