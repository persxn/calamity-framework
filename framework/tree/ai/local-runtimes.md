---
id: local-runtimes
title: "Local runtimes and quantization"
track: ai
group: inference
prereqs: [ollama, inference-internals]
tags: [ai, llm, runnable]
aliases: [llama.cpp, gguf, quantization formats, local inference, runtime]
est_hours: 25
order: 30
summary: "Run and benchmark open models at the runtime level: a readable inference engine, model formats, quantization, and the quality-speed trade-off."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- what a runtime does versus a model manager; a readable open inference engine as the example
- the on-disk model format: loading a model, what the file holds
- quantization formats and bit-widths (FP16 and BF16, INT8, INT4) and how they trade quality for memory and speed
- running the same model at two bit-widths and on two runtimes
- measuring: tokens per second, time to first token, peak memory, at a short and a long prompt
- scoring quality loss on a small fixed set, not by eye
- CPU versus GPU; offloading layers; locating the bottleneck

# Boss

Serve one open model at two quantization levels across two runtimes and report speed, memory and quality.

Passes when:

- tokens per second, time to first token and peak memory are reported for each variant at two prompt lengths
- the numbers reproduce within the margin the tutor sets across three runs
- the quality loss of the lower bit-width is scored on a fixed set, not described
- the variant to use is chosen in one paragraph from the numbers, not by preference
