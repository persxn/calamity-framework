# Field reading

Lessons teach the tool. Field reading shows the learner how the tool behaves in the real world, at scale, and when it fails. Assign one piece roughly every unit or two, matched to what was just taught.

**Verify everything with a search before handing it over.** Links rot, accounts go quiet, and memory mixes up incident details. Never give a link, handle, date or figure you haven't just checked.

## 1. Official documentation

Training the learner to read primary docs is part of mastery. People who can read docs don't depend on tutorials.

- Assign a *specific* section, not "read the docs": "Read the `RUN`, `CMD` and `ENTRYPOINT` sections of the Dockerfile reference, including the shell form vs exec form notes."
- Give the learner 2–4 questions to look for while reading. Afterwards, ask questions that only a careful read could answer: a default value, an edge case, a warning box.
- Teach how docs are laid out: tutorial vs how-to vs reference vs explanation; man page sections (1 for commands, 2 for syscalls, 3 for library functions, 5 for file formats, 8 for admin); the changelog; the RFC or spec behind a protocol.
- From time to time, ask them to find something in the docs *you haven't taught yet* and teach it back to you.

## 2. Systems they can't build yet

Show what the tool looks like at a scale the learner can't reach yet, and the layers underneath it. This builds the designer's intuition.

- **Underneath**: the kernel behind the shell (fork/exec, file descriptors, signals), the syscalls behind `ls` (`getdents64`, `statx`, viewable with `strace`), the runtime behind Docker (containerd, runc, namespaces), the engine behind the browser, the planner behind SQL.
- **At scale**: engineering write-ups from companies running this kind of system in production. Good sources to search: the Cloudflare blog, the Netflix TechBlog, Google's free SRE books, the AWS Builders' Library, the engineering blogs of Discord, Uber, Meta, Stripe, Figma, Shopify, Dropbox and Slack, LWN.net for Linux internals, and *The Architecture of Open Source Applications*.
- After they read, ask: "Which decisions here do you recognise from our units? Which one would you have made differently, and what would it have cost?"

## 3. Outage post-mortems

Every outage traces back to a decision someone made: a config pushed, a check skipped, a limit nobody knew about, a retry with no backoff. Reading post-mortems teaches judgement faster than anything else.

**Finding them.** Search the company's own post-mortem or status page first. Aggregated lists such as Dan Luu's `post-mortems` repository on GitHub are useful starting points. Match the incident to the unit just taught.

Seeds to check and fetch (verify every detail before use):
- Cloudflare, July 2019: one WAF regex with catastrophic backtracking exhausted CPU worldwide (regex, deploys, CPU limits)
- AWS S3 us-east-1, February 2017: a mistyped input to an operational command removed far more servers than intended (CLI safety, blast radius)
- GitLab, January 2017: production database directory deleted; several backup methods turned out not to be working (shell, backups, fatigue)
- Facebook, October 2021: a backbone maintenance command disconnected data centres and BGP withdrawals made DNS unreachable (networking, out-of-band access)
- CrowdStrike, July 2024: a content update triggered an out-of-bounds read in a kernel-level sensor (memory safety, staged rollout)
- Knight Capital, August 2012: an incomplete deploy reactivated dead code through a reused flag (deployments, dead code)
- GitHub, October 2018: a brief network partition led to a cross-region database failover and a long recovery (distributed databases, failover)
- npm left-pad, March 2016: an unpublished tiny package broke builds across the ecosystem (dependencies, supply chain)
- Fastly, June 2021: a valid customer config change triggered a latent bug (config validation, testing)
- Atlassian, April 2022: a maintenance script deleted customer sites instead of an app (scripting, IDs, blast radius)
- Cloudflare, November 2025: a generated configuration file grew past a hard limit after an upstream change (limits, generated config)
- Also search for recent incidents. New ones teach current practice.

**How to analyse one with the learner.** Work through these together, and let the learner do most of the reasoning:

1. **Before**: what was the system, and what normal operation looked like.
2. **The decision**: the exact action or assumption that started it. Why did it seem reasonable at the time?
3. **The chain**: how one failure led to the next. Draw it.
4. **Blast radius**: why it spread as far as it did.
5. **Detection**: how they noticed, how long it took, and which signal they missed.
6. **Mitigation and fix**: what stopped the bleeding, and what fixed the cause.
7. **The lesson, mapped to the curriculum**: which unit's knowledge would have prevented or limited it.
8. **"You're the engineer"**: what would *you* have checked before pressing enter?

## 4. Engineers to follow on X

Recommend five people who post real insight about this tool: maintainers, core contributors, people who write post-mortems or deep dives, and practitioners running it at scale. Prefer substance over follower counts and engagement posting.

- Find them with a web search (the tool's maintainers, conference speakers, authors of well-known blog posts on it).
- **Verify** each one before recommending: the account exists, the handle is right, and they have posted about this topic recently. X is often hard to fetch. If you can't confirm an account directly, say so and link their blog, GitHub or talk instead.
- For each, give one line on *why* to follow them and what kind of thing they post.
- Revisit the list when a topic is finished or months later, since people move on.

## 5. What's new and what's next

Mastery includes knowing where the field is heading.

- After the core of a topic, search for: the latest stable version and its headline changes, deprecations in progress, and newer tools built on or competing with this one (React → Next.js, Remix and newer meta-frameworks; Express → NestJS, Fastify, Hono; Docker → Podman, BuildKit, Wasm containers).
- Teach *what problem the newer tool solves that the old one didn't*. That makes it an extension of the origin-story thinking, not a list of buzzwords.
- If something newer is clearly better for the learner's goals, say so and offer it as a follow-up topic.
