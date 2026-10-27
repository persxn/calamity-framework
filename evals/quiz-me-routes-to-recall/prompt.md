---
description: A request for a quick quiz goes to the recall round, which serves only what is due.
tags: [routing, smoke]
max_turns: 15
timeout_seconds: 300
allowed_tools: [Skill, Read, Glob, Grep]
append_system_prompt: "The current working directory is the learner's Calamity checkout: run every engine command from it, exactly as the skills write it."
---

quiz me
