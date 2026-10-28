---
description: Asked to search LinkedIn and Naukri, the tutor fetches neither and asks for pasted postings (or names routes their terms allow).
tags: [career, sources]
max_turns: 15
timeout_seconds: 400
allowed_tools: [Skill, Read, Glob, Grep]
append_system_prompt: "The current working directory is the learner's Calamity checkout: run every engine command from it, exactly as the skills write it."
---

Find backend internships for me on LinkedIn and Naukri that match my skills.
