---
id: llm-agents
title: Agents and tool use
track: ai
group: llm
prereqs: [langchain]
tags: [ai, llm, runnable]
weaves_into: [llm]
aliases: [ai agents, agentic, mcp, tool use, multi-agent]
est_hours: 30
order: 70
summary: "Model-driven loops that plan, call tools and recover from errors, with limits you can defend."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- the agent loop: observe, decide, act, check; stop conditions
- designing tools: narrow inputs, clear errors, idempotence
- state and memory: scratchpads, summaries, external stores
- planning patterns: single loop, plan-then-execute, sub-agents with separate context
- the Model Context Protocol in outline: servers, tools, resources
- guardrails: allow-lists, budgets, confirmation for irreversible actions, sandboxing
- prompt injection through tool results, and defences
- evaluating agents: task success, steps, cost; replaying traces

# Boss

Build an agent that completes a multi-step task over a local workspace using at least three tools, under a step budget, with a confirmation gate on the one destructive tool.

Passes when:

- the task suite passes at the rate the tutor sets within the step budget
- an injected instruction inside a tool result is not obeyed
- the destructive tool never runs without confirmation in any trace
- every run can be replayed from its trace

# Weave

Use the evaluation harness from llm-evals when it is learnt; containerise the tool sandbox with Docker.
