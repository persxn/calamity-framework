---
id: system-design
title: System design
track: 10x
group: engineering
prereqs: ["slot:backend-framework", postgresql, redis, docker]
aliases: [architecture, scalability, distributed systems]
est_hours: 40
order: 40
summary: "Designing systems that scale and survive: requirements, storage choices, caching, queues, consistency."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- requirements and back-of-envelope estimation
- data modelling and storage choices
- caching, queues, load balancing
- consistency, replication, partitioning
- service boundaries and API contracts
- reliability patterns: timeouts, retries, circuit breakers, idempotency
- observability and cost
- walking through classic designs

# Boss

Design a system the tutor names (a URL shortener at scale, a feed, a booking system) in a written document, then defend it in a review.

Passes when:

- estimates are stated with their assumptions
- every component's failure mode is addressed
- trade-offs name what was given up
- the design holds at ten times the stated load
