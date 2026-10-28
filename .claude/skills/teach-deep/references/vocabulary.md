# Building technical vocabulary

Precise vocabulary does two jobs. It lets the learner *think* in the field's concepts, and it signals seniority in interviews. "We kept the blast radius small by putting it behind a feature flag" carries a whole design discussion in one sentence.

## Starting set (stage 2)

Before the curriculum, brainstorm 20–40 terms that practitioners of this topic use. Draw from these families and keep the ones that apply:

- **Architecture and coupling**: tight vs loose coupling, cohesion, separation of concerns, leaky abstraction, single point of failure, control plane vs data plane, sidecar, shared-nothing
- **Traffic and networking**: north-south vs east-west traffic, ingress and egress, hop, fan-out and fan-in, head-of-line blocking, backpressure
- **Reliability**: blast radius, failure domain, graceful degradation, circuit breaker, retry storm, thundering herd, cascading failure, SLI/SLO/SLA, error budget, MTTR, toil, runbook
- **Data and state**: idempotency, eventual consistency, read-your-writes, hot partition or hot key, write amplification, tombstone, compaction, stale read, split-brain
- **Performance**: tail latency (p99, p999), throughput vs latency, cold start, cache stampede, working set, cache locality
- **Change and delivery**: canary, blue-green, feature flag, rollback vs roll-forward, immutable infrastructure, drift, config as code, golden path
- **Security**: least privilege, attack surface, defence in depth, supply chain, secret sprawl
- **Engineering culture**: blameless post-mortem, bikeshedding, yak shaving, footgun, paved road, the boring-technology principle
- **Topic-specific terms**: the tool's own vocabulary and community slang (for Docker: layer, image vs container, entrypoint vs cmd, build context, multi-stage, distroless; for C: undefined behaviour, sequence point, lvalue, decay, strict aliasing)

Also search for words practitioners currently use around this topic. Vocabulary moves, so check with a search.

## How to teach a term

For each term:

1. **Plain meaning**, in one sentence.
2. **Precise meaning**: the definition an expert would accept.
3. **Used in a sentence**, the way an interviewer or senior engineer would say it.
4. **Its contrast**: the opposite or neighbouring term (tight ↔ loose coupling; north-south ↔ east-west).
5. **Where it will show up** in this curriculum ("you'll meet this in U12, when containers talk to each other").

Introduce 5–8 terms at a time, not the whole list at once. Check with quick "use it in a sentence" or "which term describes this situation?" questions.

## Ongoing

- Every unit adds its own terms to `learner/coach/<topic>/glossary.md`.
- Recall includes vocabulary items: describe a situation and ask for the term, or give a term and ask for a real example.
- In the learner's own explanations, nudge vague phrasing towards the precise term: "you described a cascading failure — say it that way in an interview."
