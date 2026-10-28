---
description: A request to learn a tool in depth goes to the mastery coach, which works through the engine (find the skill, then the engine's loop) instead of coaching off the record.
tags: [routing, companions]
max_turns: 20
timeout_seconds: 400
allowed_tools: [Skill, Read, Glob, Grep]
append_system_prompt: "The current working directory is the learner's Calamity checkout: run every engine command from it, exactly as the skills write it."
---

teach me Kubernetes in depth, I want to really understand its internals
