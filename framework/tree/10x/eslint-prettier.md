---
id: eslint-prettier
title: "ESLint & Prettier"
track: 10x
group: web-core
prereqs: [npm-bundlers]
tags: [js-ecosystem]
weaves_into: [js-ecosystem]
aliases: [eslint, prettier, lint, formatter]
est_hours: 5
order: 50
summary: "Linting and formatting that run by themselves: flat config, plugins, pre-commit hooks, CI."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- what a linter does and what a formatter does, and why to keep them apart
- ESLint flat config: rules, plugins (typescript-eslint, framework plugins), overrides
- Prettier options and editor format-on-save
- pre-commit hooks with husky and lint-staged
- enforcing both in CI

# Boss

Add ESLint, Prettier and a pre-commit hook to an existing repository.

Passes when:

- `npm run lint` exits 0
- a commit containing a lint error is rejected by the hook
- the CI workflow runs lint and format checks
