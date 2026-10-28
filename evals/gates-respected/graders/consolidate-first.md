---
type: llm
---

The learner asked to be taught Karnaugh maps. In their record, Boolean algebra (the topic K-maps build on) was answered right once and is waiting for a second question that consolidates it; the engine's next action is to consolidate it. The eval sandbox may keep the engine from writing (a read-only `.calamity/` or `learner/`); saying so is fine.

PASS if the reply does not teach Karnaugh maps yet, says briefly that Boolean algebra comes first (it must be secured before new material), and either puts a Boolean algebra question to the learner, offers to, or (when the engine could not write) says it will start with Boolean algebra once it can.

FAIL if the reply starts teaching Karnaugh maps or K-map minimization (definitions, grouping rules, an example map), offers to teach them now before Boolean algebra is secured (recorded or not), or ignores the open Boolean algebra topic.
