---
id: sec-attack-paths
title: "Infrastructure attack paths"
track: sec
group: network-infra
prereqs: [sec-service-security, sec-os-internals]
tags: [sec]
weaves_into: [sec]
aliases: [privilege escalation, lateral movement, pivoting, attack chains]
est_hours: 30
order: 30
summary: "Reading a multi-host environment as a chain of failed assumptions: how initial access, trust between services, and privilege escalation connect into a path, all in an isolated lab."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill. All work is in an
isolated lab the learner owns.

- initial access in an authorised lab environment, as one step in a chain
- service-to-service trust relationships and what they grant
- privilege-escalation analysis on a host: how a boundary is crossed
- credential and secret exposure as a link between hosts
- pivoting and lateral-movement concepts inside the isolated lab
- documenting an attack path as connected failures in assumptions and controls
- validating network segmentation: what it does and does not stop
- the detection and containment that would break the path

# Boss

Build an isolated multi-host lab with a deliberate chain of misconfigurations, then document a complete attack path through it: each link, the assumption it breaks, and the evidence. Improve the configuration and verify the original path no longer works.

Passes when:

- the attack path is traced end to end, each link justified by evidence from the lab
- the path is explained as failed assumptions and controls, not a list of commands
- the remediation closes at least one essential link, and the original path is shown to fail afterwards
- segmentation claims are validated against what the lab actually permits

# Weave

Thinking in attack paths rather than isolated findings is the core of adversary emulation and cloud attack-path research.
