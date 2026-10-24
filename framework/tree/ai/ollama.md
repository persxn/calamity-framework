---
id: ollama
title: Local models with Ollama
track: ai
group: inference
prereqs: [llm-basics, linux-shell]
tags: [ai, llm, runnable]
weaves_into: [llm]
aliases: [local llm, gguf, quantization, modelfile]
est_hours: 12
order: 10
summary: "Run open models on your own machine: pulling, configuring, serving and measuring them."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- installing Ollama; pulling, listing, running and removing models
- model sizes, quantisation levels, memory needs; CPU versus GPU
- the Modelfile: base model, system prompt, parameters, templates
- the local HTTP API: generate, chat, embeddings; the OpenAI-compatible endpoint
- context length and keep-alive settings; concurrency limits
- local embedding models
- measuring tokens per second and quality against a hosted model
- running it as a service or in a container

# Boss

Stand up a local model service with a custom Modelfile and benchmark two quantisation levels of the same model on speed and on a small quality set.

Passes when:

- a script reports tokens per second for both variants on the same prompts
- the quality set is scored the same way for both, and the trade-off is stated in one paragraph
- the service restarts cleanly and the custom model is reproducible from the Modelfile

# Weave

RAG and agent exercises should have a mode that runs entirely on the local model.
