---
id: gpu-kernels
title: "GPU kernels"
track: ai
group: inference
prereqs: [cpp, transformers-internals]
tags: [ai, runnable]
aliases: [cuda, triton, kernels, matmul, roofline, nsight]
est_hours: 45
order: 40
summary: "Write and profile GPU kernels: the execution and memory model, a tiled matrix multiply, and reading a profiler against a vendor library."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- the GPU execution model: threads, warps, blocks, and streaming multiprocessors
- the memory hierarchy: global, shared and registers; coalesced access; occupancy
- a naive matrix multiply, then a tiled one that uses shared memory
- memory-bound versus compute-bound, and what each means for what to optimise next
- the roofline, and measuring a kernel against a vendor library
- a profiler: finding the limiting resource in a real kernel
- the same kernel in a higher-level kernel language, for comparison

# Boss

On a GPU, write a tiled matrix-multiply kernel, profile it, and report its performance as a fraction of a vendor library.

Passes when:

- the kernel's output matches a reference within floating-point tolerance
- the tiled version is faster than the naive one, both timed the same way
- a profiler run is shown and the limiting resource is named
- throughput is reported as a percentage of the vendor library on the same hardware
