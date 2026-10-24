---
id: ai-agent-engineer
title: "AI agent engineer"
track: ai
group: milestones
kind: milestone
prereqs: [mcp-servers, llm-agents, llm-evals]
aliases: [agent engineer, agent systems, agent milestone]
order: 40
summary: "Ship a bounded agent system that does real work and never lies about it, with evaluations and a safety boundary."
---

# Boss

Build an agent system that completes a real task suite, proven by an evaluation harness and run inside a sandbox.

Passes when:

- the agent passes the share of seeded tasks the tutor sets, with zero false "verified" claims across every trace
- each destructive capability runs only behind a confirmation or an allow-list, shown in the traces
- an injected instruction in tool output or a fetched page is never obeyed
- the whole run is reproducible from its trace, and the evaluation runs on every change
