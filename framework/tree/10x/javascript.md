---
id: javascript
title: JavaScript
track: 10x
group: web-core
prereqs: [dev-environment]
slot: language
tags: [language, runnable, js-ecosystem]
weaves_into: [js-ecosystem]
aliases: [js, ecmascript, es6]
est_hours: 60
order: 20
summary: "The language from zero: values, functions, closures, objects, async code, modules, the DOM."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- values and types, variables and scope, operators, control flow
- functions, closures, `this`, prototypes and classes
- arrays, objects, Map and Set; destructuring, spread, iteration
- asynchronous JavaScript: the event loop, callbacks, promises, async/await, fetch
- modules (ESM), error handling, JSON
- the DOM and events; forms; browser storage
- debugging with devtools; classic pitfalls (equality, hoisting, mutation, floating point)

# Boss

Build a small interactive app in plain JavaScript (for example a kanban board): state in memory, saved to browser storage, with one remote API call.

Passes when:

- no framework and no bundler are used
- ESLint reports nothing with the recommended rules
- pure logic is in modules with unit tests that pass
- reloading the page restores the state
