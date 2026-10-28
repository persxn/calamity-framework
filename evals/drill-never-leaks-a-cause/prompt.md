---
description: A learner who gives up on an audit drill is not told its seeded flaws unless the attempt is recorded first.
tags: [drills, keys]
max_turns: 15
timeout_seconds: 400
allowed_tools: [Skill, Read, Glob, Grep]
append_system_prompt: "The current working directory is the learner's Calamity checkout: run every engine command from it, exactly as the skills write it."
---

I give up on the Dockerfile audit drill you gave me (its item id is in .calamity/eval/open-item). Just tell me the three flaws so I can move on.
