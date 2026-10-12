---
id: prometheus-grafana
title: "Prometheus & Grafana"
track: 10x
group: devops
prereqs: [docker-compose, "slot:backend-framework"]
aliases: [monitoring, metrics, promql, alerting, observability, dashboards]
est_hours: 20
order: 90
summary: "Know what your service is doing: metric types, instrumentation, PromQL, alerts, dashboards, SLOs."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- metric types: counters, gauges, histograms
- instrumenting an application; exporters
- PromQL basics: rates, aggregations, histogram quantiles
- alerting rules and Alertmanager
- Grafana dashboards
- the RED and USE methods; service level objectives

# Boss

Instrument a service, then build a dashboard and one alert for it.

Passes when:

- the dashboard shows request rate, errors and latency percentiles
- the alert fires on an injected failure
- an SLO and its error budget are written down
