---
id: sec-evidence
title: "Evidence fundamentals"
track: sec
group: forensics
prereqs: [sec-os-internals]
tags: [sec]
weaves_into: [sec]
aliases: [forensics fundamentals, chain of custody, acquisition, timestamps]
est_hours: 20
order: 10
summary: "The discipline under all forensic work: acquiring and preserving evidence without altering it, verifying its integrity, and reading time correctly across systems."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- evidence integrity and why it is the whole game
- chain of custody
- acquisition and preservation without altering the source
- hashing and verification
- timestamps and clock skew
- time zones and normalising time across sources
- volatile versus persistent evidence and the order to collect them
- forensic documentation
- the scope and the evidentiary limits of what you collect

# Boss

On a machine you own, acquire a defensible copy of a piece of evidence (a disk image, a memory capture, or a log set), prove it was not altered, and normalise its timestamps against a reference, documenting the chain of custody throughout.

Passes when:

- the acquisition is shown not to have altered the source, with hashes before and after
- the chain of custody is documented completely
- timestamps are normalised correctly and clock skew is accounted for
- the learner states what this evidence can and cannot establish

# Weave

Integrity, custody and correct time are preconditions for every host and network investigation and every reconstruction.
