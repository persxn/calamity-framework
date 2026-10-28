---
description: Between two blocks of the day, /day names the next block and asks at most one question.
tags: [day]
max_turns: 20
timeout_seconds: 400
allowed_tools: [Skill, Read, Glob, Grep]
append_system_prompt: "The current working directory is the learner's Calamity checkout: run every engine command from it, exactly as the skills write it."
---

/day
