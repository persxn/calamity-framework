---
id: web-security
title: Web security
track: 10x
group: engineering
prereqs: ["slot:backend-framework", auth-basics]
weaves_into: [backend-framework]
aliases: [owasp, xss, csrf, sql injection, security]
est_hours: 20
order: 30
summary: "Build things that hold: the OWASP Top 10, injection, XSS, CSRF, SSRF, access-control flaws, secrets."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- the OWASP Top 10
- injection, cross-site scripting, CSRF, SSRF
- broken access control, including insecure direct object references
- secrets management; dependency scanning
- security headers and a content security policy
- threat modelling in outline

# Boss

Review one of your own services against the OWASP Top 10, write up what you find, and fix it. Work only on systems you own.

Passes when:

- each finding has a reproduction and a fix with a test
- a dependency scan is clean or its exceptions are justified
- a content security policy is in place
