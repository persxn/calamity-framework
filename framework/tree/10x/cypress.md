---
id: cypress
title: Cypress
track: 10x
group: frontend
prereqs: [jest, "slot:frontend-framework"]
slot: e2e-testing
tags: [js-ecosystem]
aliases: [e2e, end-to-end, browser tests]
est_hours: 12
order: 120
summary: "End-to-end tests in the browser: commands and retry-ability, intercepts, custom commands, CI."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- commands, chaining and retry-ability
- selecting elements robustly
- cy.intercept and fixtures
- custom commands; component testing
- running in CI with recorded artefacts

# Boss

Cover the main user journeys of an app with end-to-end tests.

Passes when:

- the suite passes in CI
- no fixed waits are used
- a failing run saves screenshots and video
