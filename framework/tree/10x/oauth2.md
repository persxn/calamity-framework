---
id: oauth2
title: "OAuth 2.0 & OpenID Connect"
track: 10x
group: backend
prereqs: [jwt]
aliases: [oauth, oidc, openid connect, social login, sso, pkce]
est_hours: 15
order: 120
summary: "Delegated access and federated sign-in: roles, flows (authorisation code with PKCE), scopes, ID tokens."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- the roles: resource owner, client, authorisation server, resource server
- grant types: authorisation code with PKCE, client credentials; why the implicit flow is gone
- scopes and consent
- OpenID Connect: ID tokens, user info, discovery
- integrating a provider (social login); validating tokens properly

# Boss

Add 'sign in with' one identity provider to an app, using the authorisation-code flow with PKCE.

Passes when:

- state and PKCE are verified
- the ID token's signature, issuer and audience are checked
- a replayed authorisation code is refused
