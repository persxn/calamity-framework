---
id: ai-inference-engineer
title: "AI inference engineer"
track: ai
group: milestones
kind: milestone
prereqs: [serving-engines, gpu-kernels, local-runtimes]
aliases: [inference engineer, serving engineer, inference milestone]
order: 30
summary: "Serve a model for many users efficiently: a measured serving service with a cost and latency story you can defend."
---

# Boss

Stand up a serving service for one model and defend its throughput, latency and cost under load.

Passes when:

- a load test drives real concurrency, and p95 latency, error rate and cost per million tokens are reported
- the serving engine and the quantization chosen are justified from your own benchmarks, not from defaults
- one kernel-level or cache-level change you made is shown to move one of the numbers
- someone else can reproduce the benchmark from the README alone
