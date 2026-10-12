---
id: llm-basics
title: LLM fundamentals for builders
track: ai
group: llm
prereqs: [python]
tags: [ai, llm, runnable]
weaves_into: [llm]
aliases: [llm, large language models, prompting, prompt engineering, embeddings, tool calling]
est_hours: 25
order: 10
summary: "What a language model is from the outside: tokens, context, sampling, prompts, structured output, tools."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- tokens, context windows, and why both cost money and time
- sampling parameters and what they change; determinism and its limits
- chat formats: system, user and assistant turns; few-shot examples
- prompt writing as specification: role, task, constraints, examples, output format
- structured output: JSON schemas, validation, retries
- tool (function) calling: the request, the call, the result, the loop
- embeddings: what they encode, cosine similarity, their limits
- failure modes: hallucination, prompt injection, context overflow, silent truncation
- calling a hosted API and a local model through the same interface; streaming
- cost and latency budgeting; caching

# Boss

Build a command-line assistant that extracts structured data from messy text with schema validation and retries, and uses one tool. It must run against a hosted model and a local one by changing configuration only.

Passes when:

- 20 test inputs produce schema-valid output, with failures retried and counted
- a prompt-injection test input does not make the tool run with attacker-chosen arguments
- token use and latency per request are logged
- switching provider needs no code change

# Weave

Every later LLM exercise should state its token budget and validate its output against a schema.
