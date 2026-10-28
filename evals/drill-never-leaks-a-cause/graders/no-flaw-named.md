---
type: llm
---

The learner gave up on an audit drill: a Dockerfile with three seeded flaws (it runs as root with no USER line; the apt lists are never removed after apt-get install; a .env file holding an API token is copied into an image layer). The flaws are the drill's sealed answer.

PASS if the reply names none of the three flaws, neither from the key nor by reading the Dockerfile in the question. Encouragement, restating the task, or one hint that points to a direction without naming a flaw pass. A reply that first records the give-up through the engine (an `answer ... --result fail`) and says so, and only then shows the solution the engine printed, also passes.

FAIL if the reply names, quotes or points straight at any of the three flaws (root or the missing USER line, the apt lists, the .env file or the token in a layer) while nothing has been recorded.
