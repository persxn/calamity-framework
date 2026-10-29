---
id: sec-enterprise
title: "Enterprise & Active Directory fundamentals"
track: sec
group: enterprise-redteam
prereqs: [sec-fundamentals, sec-networking]
tags: [sec]
weaves_into: [sec]
aliases: [windows internals, active directory, kerberos, ntlm, identity]
est_hours: 30
order: 10
summary: "How a Windows enterprise is built and authenticated: processes, tokens and logging on the host, and identity, directory and authentication protocols across the domain."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- Windows architecture and administration, enough to reason about it
- processes, services, permissions and access tokens
- PowerShell for administration, and Windows event logging
- identity and access management in the enterprise
- domain environments and Active Directory structure
- Kerberos and NTLM fundamentals: what each proves and how
- Group Policy and directory services
- authentication protocols and where trust is placed
- enterprise network segmentation and endpoint security concepts

# Boss

Build a small Windows lab with a domain you own, join a client, and document how an identity authenticates and what each action records: trace a logon through the relevant protocol, read the tokens a process carries, and collect the event-log evidence.

Passes when:

- the logon is traced through Kerberos or NTLM with the learner explaining each step
- the access token on a chosen process is read and explained
- the event-log records for the actions are collected and matched to what produced them
- the lab is reproducible and stays entirely within the owned domain

# Weave

Windows internals, identity protocols and event logging underlie adversary emulation and detection-aware operations.
