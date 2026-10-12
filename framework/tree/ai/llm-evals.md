---
id: llm-evals
title: Evaluating LLM systems
track: ai
group: llm
prereqs: ["slot:rag"]
tags: [ai, llm, runnable]
weaves_into: [llm]
aliases: [evals, llm evaluation, llm as judge, faithfulness, regression tests for prompts]
est_hours: 25
order: 60
summary: "Measure an LLM application so that changes are decisions, not guesses."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- building a test set: sources of questions, labelling, keeping a held-out part
- retrieval metrics against labelled evidence
- answer quality: exact match, rubric scoring, faithfulness to retrieved context
- model-graded evaluation: writing the grader prompt, checking the grader against human labels
- statistical care: sample size, intervals, paired comparisons
- regression suites in CI; snapshotting prompts and model versions
- tracing and reading failures one by one
- cost, latency and safety checks as first-class metrics

# Boss

Write an evaluation harness for a RAG system and use it to decide between two concrete changes.

Passes when:

- the grader agrees with human labels on a checked sample at the rate the tutor sets
- the comparison reports a paired difference with an interval
- the harness runs in CI and fails on a planted regression
- ten failures are read and categorised by hand

# Weave

Bring in hypothesis tests and intervals from the probability skill for every comparison.
