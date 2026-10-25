---
id: inference-internals
title: "Inference internals"
track: ai
group: inference
prereqs: [transformers-internals]
tags: [ai, llm, runnable]
aliases: [kv cache, continuous batching, paged attention, prefill, decode, speculative decoding, roofline]
est_hours: 30
order: 20
summary: "Why LLM inference costs what it does: the KV cache, batching, attention memory, and the decode ceiling you can compute."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- prefill versus decode, and why decode is bound by memory bandwidth, not compute
- the KV cache: what it stores, how it grows with context, what it costs in memory
- sampling revisited: greedy, temperature, top-k, top-p, and their effect on latency
- batching: static versus continuous, and how a scheduler keeps the device busy
- attention memory: paged attention and why fragmentation matters
- prefix caching: sharing one long system prompt across many requests
- speculative decoding in outline: a small draft model proposing tokens a larger one checks
- the roofline: computing the single-stream decode ceiling (memory bandwidth divided by bytes read per token) and reporting the fraction reached

# Boss

Add a KV cache to a small transformer you wrote, measure the decode speed-up, and state the roofline ceiling for your setup.

Passes when:

- generation with and without the cache yields identical tokens under a fixed seed
- decode tokens per second with the cache is reported against without, on the same prompts
- the computed decode ceiling is shown together with the memory bandwidth it assumes
- the measured tokens per second is given as a fraction of that ceiling

# Weave

The measurements here are the baseline for local-runtimes and serving-engines.
