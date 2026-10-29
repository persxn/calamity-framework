---
id: sec-applied-crypto
title: "Applied cryptography"
track: sec
group: cross-cutting
prereqs: [sec-fundamentals]
optional: true
tags: [sec]
weaves_into: [sec]
aliases: [applied cryptography, crypto failures, key management, certificate validation]
est_hours: 25
order: 40
summary: "Cryptography as it is actually deployed and actually broken: the primitives, where implementations go wrong, and the failure modes around randomness, keys and certificates."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- cryptographic primitives and what each one provides
- secure protocol design in outline
- common implementation mistakes
- randomness and why weak randomness breaks a scheme
- key management
- certificate validation and how it is skipped or fooled
- the recurring cryptographic failure modes, by their cause

# Boss

Take a small system that uses cryptography incorrectly (build one, or a known teaching example), demonstrate the failure, explain its root cause among the standard failure modes, and show the corrected use.

Passes when:

- the failure is demonstrated concretely, not only described
- the root cause is named among the standard failure modes and explained
- the corrected version is shown to remove the weakness
- the learner explains why rolling one's own primitive is rarely the real problem
