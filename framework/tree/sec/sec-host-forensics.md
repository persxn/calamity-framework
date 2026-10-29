---
id: sec-host-forensics
title: "Host investigation"
track: sec
group: forensics
prereqs: [sec-evidence]
tags: [sec]
weaves_into: [sec]
aliases: [host forensics, log analysis, persistence, memory analysis]
est_hours: 30
order: 20
summary: "Reconstructing what happened on a single machine from its artefacts: authentication and system logs, execution and persistence traces, and the line between normal administration and suspicious activity."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- Linux authentication and system logs
- process-execution artefacts
- service and startup changes
- filesystem timelines
- user and permission changes
- Windows event logs
- PowerShell and process telemetry
- scheduled tasks and service artefacts
- memory acquisition and analysis concepts
- persistence indicators
- distinguishing legitimate administration from suspicious activity

# Boss

From the artefacts of a host where a scripted set of actions took place (generate them on a machine you own), reconstruct what was done and when, building a host timeline and separating the benign administration from the actions of interest, with the evidence for each call.

Passes when:

- the host timeline is built from the artefacts and is correct against the known actions
- each conclusion is tied to a specific artefact, and benign activity is not mistaken for malicious
- a persistence mechanism, if present, is found and explained
- the write-up states what the artefacts could not establish

# Weave

Host timelines combine with network evidence into a full incident reconstruction.
