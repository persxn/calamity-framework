---
id: ai-pair-engineering
title: AI pair engineering
track: 10x
group: engineering
prereqs: [git-gh, testing-basics]
tags: [engineering, ai-tools]
weaves_into: [10x]
aliases: [ai pairing, ai coding, claude code, coding agents, prompting for code]
est_hours: 25
order: 35
summary: "Working with AI coding agents as an engineer: specifications, decomposition, reviewing AI output, agent workflows."
---

# Scope

What the mastery standard covers: using AI coding tools without handing
over judgement. The learner writes the specification, decomposes the work,
reviews every change, and knows the ways AI output goes wrong in their
stack. Claude Code itself is one of the tools studied.

- specifications an agent can act on: constraints, acceptance tests, edge cases, non-goals
- decomposition into steps that can each be checked
- reviewing AI output: invented APIs and flags, outdated patterns, insecure defaults, confident wrong comments
- agent workflows: tools and permissions, context, plans, hooks, sub-agents; Claude Code as the worked example
- verification: tests first, running the code, reading the diff
- when not to use an agent, and what stays the engineer's job

# Boss

An agent-assisted feature in a real project: the specification written first, the agent's work in
reviewed steps, and a written review of every AI-produced change (what was kept, changed or rejected,
and why), with the tests that prove it.

# Topics

## spec | Specifications an agent can act on
level: 1
- [P] write a task specification with constraints, acceptance tests, edge cases and non-goals
- [T] explain why an underspecified prompt produces plausible but wrong code
- [I] turn a vague request into a specification and its acceptance tests

## decompose | Decomposing the work
level: 2
needs: [spec]
- [P] split a feature into steps that can each be run and checked
- [T] explain why small verified steps beat one large generation
- [P] choose which steps to hand to an agent and which to write by hand

## review | Reviewing AI output
level: 2
needs: [spec]
- [P] find an invented flag or API by checking the official documentation
- [P] spot an insecure default, an outdated pattern and a confident wrong comment in generated code
- [T] explain the failure modes of AI code in a named stack, and why each happens
- [I] review a generated change line by line and write what to keep, change or reject

## workflows | Agent workflows
level: 3
needs: [decompose, review]
- [T] explain how a coding agent's tools, permissions and context shape what it does
- [P] set up a Claude Code project: CLAUDE.md, permissions, a hook, a sub-agent
- [P] run a plan, implement and review loop on a real task, with tests at each step
- [I] build a small custom agent workflow (a hook or a sub-agent) and show it working

## judgement | What stays the engineer's
level: 3
needs: [workflows]
- [T] explain which decisions an engineer must not delegate (architecture, security, data handling)
- [P] decide when an agent slows a task down, and say why
- [T] explain how to keep learning a skill while using AI on it
