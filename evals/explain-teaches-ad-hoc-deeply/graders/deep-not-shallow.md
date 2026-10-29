---
type: llm
---

The learner asked, casually, to understand hash tables. Judge the explanation the assistant gives.

It teaches in short chunks and may pause to check with the learner before continuing, so judge the portion delivered in this turn. A mid-lesson pause, or a chunk that ends with a check question, is expected and is not a failure — do not require a full end-of-topic summary here.

PASS if the delivered explanation:
- leads with why hash tables exist / the problem they solve (fast lookup by key) before any formal definition;
- builds up in a natural order — each new idea rests on the one before it — rather than dumping terminology;
- explains the mechanism in plain language (turning a key into a slot or bucket with a hash function; that collisions happen) with a concrete example, analogy or small trace, not a one-line definition;
- defines each new term the first time it is used.

FAIL if the reply is mostly a short textbook definition, jumps to jargon before motivating it, skips why hash tables exist, or gives no concrete example or mechanism.
