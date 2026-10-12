---
id: tracing-logging
title: "Logging & distributed tracing"
track: 10x
group: devops
prereqs: [prometheus-grafana]
aliases: [opentelemetry, otel, tracing, structured logging]
est_hours: 12
order: 100
summary: "Follow one request across services: structured logs, OpenTelemetry traces, correlation."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- structured logging; log levels; what not to log
- collecting and searching logs
- OpenTelemetry: traces, spans, context propagation
- correlating logs, metrics and traces

# Boss

Trace one request through two services and a database.

Passes when:

- one trace shows every hop with timings
- log lines carry the trace id
- no secret or personal data appears in logs
