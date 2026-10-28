---
id: eng-vocab
title: Engineering vocabulary
track: 10x
group: engineering
tags: [vocabulary]
weaves_into: [10x]
aliases: [vocabulary, vocab, engineering terms, jargon]
est_hours: 30
order: 5
optional: true
summary: "The working language of production engineering, about five terms a day: each with its mental model, a real example and a check."
---

# Scope

What the mastery standard covers: the terms senior engineers use without
explaining, grouped by the problem they name. Each term is learnt with its
mental model, where it shows up in a real system, and what goes wrong
without it. Terms are added as sessions bring them up (`practice session
vocab`); the topics below are the families they belong to.

# Boss

A forty-minute design conversation the tutor runs (a real system the learner
has not studied): every term used precisely, each one asked about defined in
the learner's own words with an example, and five terms from the families
below brought in unprompted where they fit.

# Topics

## reliability | Reliability and failure
level: 1
- [T] explain blast radius, single point of failure, graceful degradation and failover, each with a real example
- [T] explain why a retry without backoff and jitter can turn a blip into an outage (retry storm, thundering herd)
- [P] choose between a timeout, a retry, a circuit breaker and a fallback for a named failure, and say why

## distributed | Distributed systems
level: 2
needs: [reliability]
- [T] explain idempotency, exactly-once versus at-least-once delivery, and why idempotency keys exist
- [T] explain eventual consistency, read-your-writes and split-brain, each with the failure that shows it
- [T] explain consensus, leader election and quorum in plain words, and what a partition does to them
- [I] build a tiny at-least-once queue consumer that stays correct under duplicate delivery

## data | Data and storage
level: 2
- [T] explain hot partition (hot key), write amplification, tombstones and compaction
- [T] explain replication lag and a stale read, and how a read replica produces one
- [P] pick the term that names a symptom from a short incident description (for example, a skewed shard)

## performance | Performance and capacity
level: 2
- [T] explain tail latency (p99), head-of-line blocking, backpressure and load shedding
- [N] estimate throughput, latency and capacity on the back of an envelope (Little's law, fan-out)
- [P] read a latency histogram and name what it shows (a bimodal tail, queueing)

## architecture | Architecture and coupling
level: 2
- [T] explain coupling and cohesion, bounded context, and east-west versus north-south traffic
- [T] explain a sidecar, a service mesh and an API gateway, and what each one costs
- [P] name the coupling in a design sketch and propose the change that reduces it

## operations | Operations and delivery
level: 1
- [T] explain SLI, SLO, SLA and error budget, and how an error budget decides a release
- [T] explain canary, blue-green, feature flag and rollback, and the risk each one removes
- [P] write a one-line postmortem summary that names trigger, root cause and contributing factor

## security | Security language
level: 2
- [T] explain least privilege, defence in depth, attack surface and the confused-deputy problem
- [T] explain authentication versus authorisation, and what a token's audience and scope are for
- [P] spot the term an incident describes (privilege escalation, SSRF, replay) from a short account
