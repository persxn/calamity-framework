---
id: llm-agents
title: Agent frameworks and orchestration
track: ai
group: agents
prereqs: [langchain, agent-loops]
tags: [ai, llm, runnable]
weaves_into: [llm]
aliases: [ai agents, agentic, orchestration, multi-agent, langgraph]
est_hours: 30
order: 30
summary: "Build agents with a framework and coordinate several: orchestration, state, multi-agent and evaluation, on the loop you already wrote by hand."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- the loop and tool design are built by hand first in agent-loops; here a framework carries them
- choosing a framework: what it gives you (orchestration, state, retries) and what it hides
- reading one framework's source until its loop holds no surprises
- planning patterns: single loop, plan-then-execute, a graph of steps
- multi-agent: separate contexts, when it genuinely helps and when one agent is better
- state and memory: scratchpads, summaries, external stores, resumable runs
- guardrails and injection defences carried from agent-loops into framework code
- evaluating agents: task success, steps, cost; replaying traces; a regression suite

# Boss

Rebuild your agent-loops agent on a framework, add one piece of coordination (a second agent or a planning graph), and keep every guarantee you had by hand.

Passes when:

- the framework agent passes the same task suite as the hand-written one, within the step budget
- an injected instruction inside a tool result is still not obeyed
- the destructive tool still never runs without confirmation in any trace
- the added coordination is justified by a metric it improves over the single loop

# Weave

Use the evaluation harness from llm-evals when it is learnt; containerise the tool sandbox with Docker.
