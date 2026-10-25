---
id: agent-skills
title: "Agent skills"
track: ai
group: agents
prereqs: [agent-loops]
tags: [ai, llm, runnable]
aliases: [skills, skill engineering, agent capabilities, tool extensions]
est_hours: 15
order: 40
summary: "Package a repeatable agent capability as a skill: when it fires, what it does, and evaluations that prove both."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- what a skill is: a described, on-demand capability a host loads when it is relevant
- the description as the trigger: firing on the prompts it should, staying quiet on the rest
- scripts that compute facts the model then reasons over, instead of asking the model to guess
- short instructions, with detail deferred to reference files the skill loads only when needed
- evaluations: prompts that should and should not trigger, and measuring the trigger rate
- least privilege: the tools a skill may use, and why that matters in an untrusted repository

# Boss

Build a skill with an evaluation set and show it triggers on the right prompts, not the wrong ones, and does its job.

Passes when:

- the skill triggers on a set of prompts that should invoke it and stays quiet on a set that should not, at the rate the tutor sets
- at least one script produces facts the output relies on, rather than the model inventing them
- the output follows its stated format on every case in the eval set
- a with-skill versus without-skill comparison shows what the skill adds
