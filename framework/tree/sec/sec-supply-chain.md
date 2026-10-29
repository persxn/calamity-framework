---
id: sec-supply-chain
title: "Software supply-chain security"
track: sec
group: cross-cutting
prereqs: [sec-fundamentals]
optional: true
tags: [sec]
weaves_into: [sec]
aliases: [supply chain security, dependency confusion, build provenance, signing]
est_hours: 20
order: 50
summary: "The integrity of what you build and ship: dependencies, build provenance, CI/CD permissions, signing and verification, studied in controlled repositories you own."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill. All work is in
repositories and pipelines the learner owns.

- dependency analysis and package integrity
- build provenance
- CI/CD permissions and what a pipeline can reach
- signing of artefacts
- artefact verification
- dependency-confusion concepts in a controlled environment

# Boss

In repositories and a pipeline you own, demonstrate one supply-chain weakness (for example an over-privileged pipeline step or an unverified artefact), show its reach, then add provenance, least-privilege and verification and show the weakness is closed.

Passes when:

- the weakness and its reach are demonstrated inside the owned pipeline
- provenance, least-privilege permissions and verification are added and shown to close it
- the learner explains the dependency-confusion risk and how verification defeats it
- the exercise stays within owned repositories and pipelines
