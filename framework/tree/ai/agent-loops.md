---
id: agent-loops
title: "Agents from scratch"
track: ai
group: agents
prereqs: [llm-basics]
tags: [ai, llm, runnable]
weaves_into: [llm]
aliases: [agent loop, tool calling, agent from scratch, bounded agent]
est_hours: 25
order: 10
summary: "Build a bounded agent loop by hand against a raw model API: tools, stopping, permissions and honest verification."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- the loop by hand: call the model, run the tool it chose, feed the result back, repeat
- tool schemas: narrow typed inputs, one job each, errors returned as results, not raised into the loop
- stopping: a step limit, a token budget, a wall-clock timeout, and the model's own end of turn; reporting which one fired
- least-privilege permissions: read where it may read, write only where it may write, run only an allow-listed command
- truthful verification: the harness, not the model, decides what counts as done
- untrusted input: tool results and file contents are data, not instructions; prompt injection and what defends against it
- a trace of every call and decision, as both debugger and eval data
- when a fixed workflow beats an agent, and when one agent beats several

# Boss

Without any agent framework, build a bounded agent that fixes seeded bugs in a small repository and proves each fix with tests.

Passes when:

- at least the share of seeded bugs the tutor sets are fixed with the test suite passing
- no run is reported as successful unless the test command exited zero after the last edit (a test proves a false "verified" claim is caught)
- a path that escapes the repository, or a write outside the allowed folders, is refused rather than executed
- every run stops on a declared limit and the trace names which one

# Weave

A later framework-based agent (llm-agents) must reproduce these guarantees; sandbox the tools with Docker once it is learnt.
