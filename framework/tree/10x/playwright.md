---
id: playwright
title: Playwright
track: 10x
group: frontend
prereqs: [jest, "slot:frontend-framework"]
slot: e2e-testing
tags: [js-ecosystem]
aliases: [e2e, end-to-end, browser tests]
est_hours: 12
order: 110
summary: "End-to-end tests across browsers: locators, auto-waiting, fixtures, network mocking, traces, CI."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- locators and auto-waiting; assertions
- fixtures and the page object pattern
- network interception and API mocking
- authentication state reuse
- parallelism, retries, the trace viewer
- running across browsers in CI

# Boss

Cover the main user journeys of an app with end-to-end tests.

Passes when:

- the suite passes in three browsers in CI
- no fixed sleeps are used
- a failing run uploads a trace
