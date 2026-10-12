---
id: jwt
title: JWT
track: 10x
group: backend
prereqs: [auth-basics, "slot:backend-framework"]
weaves_into: [backend-framework]
aliases: [json web token, access token, refresh token]
est_hours: 8
order: 110
summary: "Signed tokens: structure, algorithms, claims, expiry and refresh, storage, revocation, classic mistakes."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- structure: header, payload, signature
- signing algorithms; symmetric and asymmetric keys; key rotation
- claims, expiry, refresh tokens
- where to store tokens in a browser, and why
- revocation strategies
- classic mistakes: `alg: none`, key confusion, trusting unverified payloads

# Boss

Replace session auth in an API with short-lived access tokens and rotating refresh tokens.

Passes when:

- an expired token is refused
- a reused refresh token revokes the session (tested)
- a token signed with the wrong key is refused
