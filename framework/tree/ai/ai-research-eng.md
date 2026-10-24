---
id: ai-research-eng
title: "AI research engineer"
track: ai
group: milestones
kind: milestone
prereqs: [post-training-rl, transformers-internals]
aliases: [research engineer, reproduction, research milestone]
order: 50
summary: "Reproduce a published result and report it honestly: the method, the numbers, and where they differ."
---

# Boss

Reproduce one published result on your own hardware and write it up so a maintainer would trust it.

Passes when:

- the reproduced metric matches the paper within its reported variance, or the discrepancy is documented with a cause
- the experiment is pinned: data, seeds and configuration are recorded and reproduce a second time
- inference-time compute is held equal to the baseline, so the comparison is fair
- the write-up states plainly what was not reproduced, and why
