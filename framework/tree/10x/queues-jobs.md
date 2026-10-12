---
id: queues-jobs
title: "Queues & background jobs"
track: 10x
group: backend
prereqs: [redis, "slot:backend-framework"]
tags: [backend]
aliases: [message queue, bullmq, rabbitmq, kafka, workers, async jobs]
est_hours: 12
order: 130
summary: "Work that happens later: brokers, retries, dead-letter queues, idempotent consumers, scheduling."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- why move work out of the request
- brokers in outline: Redis streams and BullMQ, RabbitMQ, Kafka
- delivery guarantees; retries with backoff; dead-letter queues
- idempotent consumers
- scheduled and recurring jobs; monitoring a queue

# Boss

Move a slow operation of an API (sending email, generating a report) into a background job.

Passes when:

- the request returns before the job finishes
- a failing job retries, then lands in a dead-letter queue
- running the same job twice has no extra effect
