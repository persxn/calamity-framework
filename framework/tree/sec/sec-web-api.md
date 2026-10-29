---
id: sec-web-api
title: "Application & API security"
track: sec
group: cross-cutting
prereqs: [sec-networking]
optional: true
tags: [sec]
weaves_into: [sec]
aliases: [web security, api security, injection, ssrf, request smuggling]
est_hours: 30
order: 10
summary: "Where web and API applications break: HTTP internals, broken authentication and access control, injection and SSRF, and how small flaws chain into a larger one."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill. Targets are
deliberately vulnerable applications the learner runs, or explicitly authorised.

- HTTP internals, deep enough to reproduce a request by hand
- authentication and session handling, and how they fail
- authorisation and access-control flaws
- injection in its major forms, by the boundary the data crosses
- server-side request forgery
- request smuggling in outline
- deserialisation and file-handling vulnerabilities
- API-specific security concerns
- chaining several small flaws into one meaningful result

# Boss

On a deliberately vulnerable application you run, find a chain of at least two flaws, reproduce each by reconstructing the HTTP requests yourself, explain the root cause of each, and describe the fix and the defensive signal.

Passes when:

- each flaw is reproduced from hand-built requests, not only through a tool
- the chain is explained as connected root causes, each tied to a boundary
- the fix for each flaw is stated, with the observable evidence a defender would see
- the work stays on the owned or authorised target
