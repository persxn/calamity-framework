---
description: An answer given to an open question gets that answer recorded and its result told at once, without leaking the key when nothing was recorded.
tags: [loop, keys]
max_turns: 15
timeout_seconds: 400
allowed_tools: [Skill, Read, Glob, Grep]
append_system_prompt: "The current working directory is the learner's Calamity checkout: run every engine command from it, exactly as the skills write it."
---

My answer to the question you just asked me (its item id is in .calamity/eval/open-item) is C.
