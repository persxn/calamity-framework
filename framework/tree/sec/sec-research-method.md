---
id: sec-research-method
title: "Security research methodology"
track: sec
group: foundations
prereqs: [sec-fundamentals]
tags: [sec]
weaves_into: [sec]
aliases: [research method, reproduction, root cause analysis, minimisation]
est_hours: 20
order: 50
summary: "Investigating unknown behaviour like a researcher: a baseline, a falsifiable hypothesis, a controlled experiment, a reliable reproduction and an honest write-up."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- forming a testable, falsifiable hypothesis about a system's behaviour
- designing a controlled experiment and establishing a baseline
- telling correlation from causation in a system's response
- reproducing a bug reliably, and collecting the artefacts that prove it
- reducing a complex failure to a minimal reproduction
- comparing versions and configurations to isolate what changed
- reading source, documentation, papers and advisories as primary sources
- documenting uncertainty, limitations and what could not be concluded
- judging whether a finding is genuinely novel against existing work
- distinguishing a symptom from a root cause, and a crash from a vulnerability

# Boss

Take an unexpected behaviour in a program you control (seed one if needed), and run the full loop on it: baseline, hypothesis, experiment, reliable reproduction, minimisation, root cause. Produce a minimal reproducible case and a short report that separates what you demonstrated from what you only suspect.

Passes when:

- the reproduction is reliable: it triggers the behaviour on demand on a clean machine
- the minimised case is as small as the behaviour allows, and the report explains each reduction step
- the root cause is stated with the evidence for it, distinct from the symptom
- the report marks every claim as tested, expected or unverified, and names its limitations

# Weave

This loop is the backbone of the research-grade work in every specialisation: a finding that cannot be reproduced and reduced is not yet a finding.
