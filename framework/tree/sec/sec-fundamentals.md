---
id: sec-fundamentals
title: "Security fundamentals"
track: sec
group: foundations
prereqs: [sec-os-internals, sec-networking]
tags: [sec]
weaves_into: [sec]
aliases: [threat modelling, security principles, cia, vulnerability classes]
est_hours: 25
order: 40
summary: "Reasoning about systems as an attacker and a defender: trust boundaries, vulnerability classes and their root causes, and the discipline of evidence and disclosure."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- threat modelling and attack surface: what an attacker wants and where they can touch the system
- trust boundaries and the assumptions a design depends on
- authentication, authorisation and accounting; confidentiality, integrity and availability
- least privilege, defence in depth, secure defaults and isolation
- the common vulnerability classes and their root causes, named and compared
- input validation, output encoding and the places data crosses a boundary
- security logging and monitoring: what to record so an incident can be reconstructed
- responsible and coordinated disclosure, and why premature publication causes harm
- reproducibility and evidence quality; what a finding must show to be believed
- reading a vulnerability advisory and a CVE record critically

# Boss

Take a small system you can run (one of your own foundation-boss programs, or a deliberately vulnerable application), draw its trust boundaries and attack surface, and write a threat model: the assets, the boundaries, the plausible vulnerability classes at each boundary, and the evidence that would confirm or rule each one out.

Passes when:

- every trust boundary in the running system is identified and justified
- each named vulnerability class is tied to a specific boundary and a root cause, not a buzzword
- the model states, for each hypothesis, what evidence would confirm it and what would refute it
- the learner explains how they would disclose a real finding responsibly and why

# Weave

Threat modelling, trust boundaries and evidence discipline frame every practical exercise in every later branch.
