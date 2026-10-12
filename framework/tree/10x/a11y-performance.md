---
id: a11y-performance
title: "Web accessibility & performance"
track: 10x
group: frontend
prereqs: ["slot:frontend-framework"]
tags: [frontend]
weaves_into: [frontend]
aliases: [accessibility, a11y, wcag, core web vitals, lighthouse]
est_hours: 15
order: 90
summary: "Make it usable by everyone and fast for everyone: WCAG essentials, Core Web Vitals, measuring and fixing."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- WCAG essentials: semantics, contrast, focus management, ARIA only where HTML cannot do it
- testing with a screen reader and with axe
- Core Web Vitals: LCP, CLS, INP, and how to measure them
- images, fonts, code splitting, caching strategies
- performance budgets in CI

# Boss

Audit an existing app, then fix what the audit finds.

Passes when:

- axe reports no serious or critical issue
- LCP is under 2.5 s on a throttled mobile profile
- a keyboard-only and a screen-reader walkthrough both complete the main task
