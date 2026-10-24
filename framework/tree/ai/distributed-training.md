---
id: distributed-training
title: "Distributed training"
track: ai
group: training
prereqs: [fine-tuning]
tags: [ai, ml, runnable]
aliases: [data parallel, tensor parallel, pipeline parallel, fsdp, nccl, distributed training]
optional: true
est_hours: 40
order: 30
summary: "Train a model too big for one GPU: data, tensor and pipeline parallelism, sharding, and the collectives underneath."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- why one GPU runs out: parameters, gradients, optimiser state and activations
- data parallelism, and the all-reduce that synchronises gradients across devices
- sharding optimiser state and parameters (FSDP) to fit memory
- tensor and pipeline parallelism in outline, and when each is reached for
- the collective operations (all-reduce and its family) and the bandwidth they need
- measuring scaling efficiency: throughput on two devices against one

# Boss

Measure a collective, then train one small model across two devices and report the scaling efficiency.

Passes when:

- an all-reduce is benchmarked on two devices and its bandwidth reported against the hardware's limit
- the same model is trained on one device and on two, with throughput recorded for each
- scaling efficiency (two-device throughput over twice the one-device throughput) is computed and explained
- the memory saved by sharding is shown, if sharding is used
