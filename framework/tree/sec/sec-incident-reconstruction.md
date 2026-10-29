---
id: sec-incident-reconstruction
title: "Incident reconstruction"
track: sec
group: forensics
prereqs: [sec-host-forensics, sec-network-forensics]
tags: [sec]
weaves_into: [sec]
aliases: [incident reconstruction, timeline, intrusion analysis, confidence levels]
est_hours: 25
order: 40
summary: "Joining host and network evidence into one defensible account of an intrusion: a unified timeline, confirmed facts separated from hypotheses, confidence stated, and the limits named."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- building a unified timeline across host and network evidence
- identifying initial access where the evidence supports it
- reconstructing execution and privilege changes
- tracing communications and lateral movement
- identifying impacted systems
- distinguishing confirmed facts from hypotheses
- recording alternative explanations
- establishing confidence levels
- determining what cannot be concluded
- recommending containment and remediation
- preserving evidence for further analysis

# Boss

From a combined set of host and network evidence for one intrusion, build a single reconstruction: the unified timeline, the initial access if the evidence supports it, the path through the systems, with each claim marked as confirmed or hypothesised and a confidence level, and the limits stated.

Passes when:

- the unified timeline is consistent across host and network evidence
- every major conclusion is substantiated by a specific artefact
- facts and hypotheses are kept separate, with alternatives and confidence recorded
- the reconstruction states plainly what the evidence cannot establish

# Weave

This is the synthesis the whole forensics branch builds toward, and it reads the telemetry that emulation produces.
