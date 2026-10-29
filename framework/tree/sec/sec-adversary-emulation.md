---
id: sec-adversary-emulation
title: "Authorised adversary emulation"
track: sec
group: enterprise-redteam
prereqs: [sec-enterprise, sec-attack-paths]
tags: [sec]
weaves_into: [sec]
aliases: [red team, adversary simulation, att&ck, c2 concepts]
est_hours: 35
order: 20
summary: "Running a scoped, authorised adversary simulation in an owned enterprise lab as a sequence of hypotheses, mapped to ATT&CK, with cleanup and evidence throughout."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill. Every exercise is in
an owned lab or an explicitly authorised environment, under written scope.

- engagement scoping and rules of engagement as the first step
- threat modelling and attack hypotheses for the target
- attack-surface discovery and initial-access simulation
- privilege-boundary assessment inside the domain
- identity and credential-security testing
- lateral-movement simulation between owned hosts
- persistence mechanisms studied as controlled exercises
- command-and-control architecture concepts, with contained test payloads
- egress restrictions and network monitoring
- cleanup, restoration and evidence collection as part of the work
- mapping each action to the ATT&CK technique it represents

# Boss

In your owned enterprise lab, run a short scoped emulation against a stated objective: form hypotheses, carry out the chain with contained test tooling, map each step to ATT&CK, collect the telemetry you generate, and restore the environment afterwards.

Passes when:

- a written scope and objective precede any action, and the work stays inside them
- the chain is executed with contained, non-destructive tooling and each step mapped to a technique
- the telemetry generated at each step is collected and tied to the action
- the environment is cleaned up and restored, and the evidence supports the write-up

# Weave

Emulation generates the telemetry that detection-aware operations and forensics learn to read.
