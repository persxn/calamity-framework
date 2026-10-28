---
type: llm
---

The learner answered C to an open multiple-choice question and the tutor tried to record it with the engine. (The right option is B. The eval sandbox may refuse the engine's write; if it did, nothing was recorded.)

PASS if the reply responds to this answer before anything else: either the result the engine gave (C is wrong, with the key and solution the engine printed and a word on why), or, if the engine could not record it, a plain statement that the answer was not recorded, without saying which option is right.

FAIL if the reply moves on to another question or topic without telling the result of this answer, or says which option is right while also saying the answer was not recorded.
