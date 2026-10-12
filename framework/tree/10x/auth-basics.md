---
id: auth-basics
title: "Authentication & authorisation fundamentals"
track: 10x
group: backend
prereqs: [rest-api-design]
weaves_into: [backend-framework]
aliases: [auth, authn, authz, sessions, rbac]
est_hours: 10
order: 100
summary: "Who you are and what you may do: sessions and tokens, password storage, cookies, CSRF, access control."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- authentication versus authorisation
- sessions versus tokens; where each fits
- password hashing (argon2, bcrypt); never storing secrets in plain text
- cookies: HttpOnly, Secure, SameSite; CSRF
- access control models: roles and attributes
- multi-factor authentication in outline

# Boss

Add sign-up, sign-in and role-based access to an existing API, with session cookies.

Passes when:

- passwords are stored with a slow hash
- a CSRF attempt is refused
- a user cannot read another user's resource (tested)
