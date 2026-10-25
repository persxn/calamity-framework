---
id: serving-engines
title: "Serving engines"
track: ai
group: inference
prereqs: [inference-internals, docker]
tags: [ai, llm, runnable]
aliases: [vllm, sglang, serving, continuous batching, throughput]
est_hours: 30
order: 50
summary: "Serve a model to many concurrent users: a production serving engine, its scheduler, and a throughput-latency benchmark."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- what a serving engine adds over a single-process runtime: a scheduler for many requests at once
- continuous batching and paged attention in practice, not just in theory
- prefix caching for shared system prompts and agent traffic
- a concurrency sweep: how throughput and latency move as load rises
- the numbers under load: tokens per second, time to first token, p50 and p95 latency
- memory and the maximum batch; what falls over first as load grows
- reading the engine's scheduler so a number has an explanation

# Boss

Serve one model on a production serving engine and chart throughput against latency across a concurrency sweep.

Passes when:

- the same model is driven at rising concurrency (for example 1 to 32) with tokens per second and p50 and p95 latency recorded at each
- a prefix-cache test, many requests sharing one long prompt, shows the effect, measured
- the knee of the throughput-latency curve is identified from the data
- cost per million tokens is derived from the measured throughput and stated
