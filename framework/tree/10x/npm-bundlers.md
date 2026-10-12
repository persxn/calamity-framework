---
id: npm-bundlers
title: "npm & bundlers (Vite and others)"
track: 10x
group: web-core
prereqs: [javascript]
tags: [js-ecosystem]
weaves_into: [js-ecosystem]
aliases: [npm, pnpm, yarn, vite, webpack, bundler, esbuild, rollup]
est_hours: 12
order: 40
summary: "Packages, lockfiles and scripts; what a bundler does; Vite in depth, the others in outline."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- package.json, semver ranges, lockfiles, scripts; npm, pnpm and yarn
- ESM and CommonJS; dependency kinds; npx
- Vite: dev server, hot module replacement, build, environment variables, plugins
- what bundlers do: tree shaking, code splitting, minification, source maps
- the landscape in outline: webpack, esbuild, Rollup, Turbopack
- workspaces and monorepo basics; publishing a package

# Boss

Set up a Vite project by hand (no template): environment-based config, one lazily loaded route, and a bundle analysis.

Passes when:

- `npm ci && npm run build` works from a fresh clone
- the bundle report shows a separate chunk for the lazy route
- the lockfile is committed and no dependency is unpinned to `latest`
