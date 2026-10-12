---
id: devops-platform
title: DevOps capstone
track: 10x
group: milestones
kind: milestone
prereqs: [kubernetes, terraform, prometheus-grafana, "slot:ci", nginx-tls]
aliases: [devops, platform, sre]
est_hours: 50
order: 30
summary: "Milestone: infrastructure as code, a cluster deployment, monitoring and alerts for a real application."
---

# Boss

Take an application you built and run it properly: infrastructure in Terraform, deployment to Kubernetes, TLS at the edge, dashboards and one alert, all from a pipeline.

Passes when:

- `terraform plan` is clean after apply
- a rollout under load loses no request
- the dashboard shows rate, errors and latency, and the alert fires on an injected failure
- everything can be torn down and recreated from the repository
