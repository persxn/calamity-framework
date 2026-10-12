---
id: kubernetes
title: Kubernetes
track: 10x
group: devops
prereqs: [docker-compose, cloud-basics]
aliases: [k8s, kubectl, helm, pods, ingress]
est_hours: 50
order: 70
summary: "Run containers at scale: pods, deployments, services, ingress, config, probes, rollouts, RBAC, Helm."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- architecture: control plane and nodes
- pods, deployments, services, ingress
- config maps and secrets; volumes
- probes; resource requests and limits
- rollouts and rollbacks; autoscaling
- namespaces and role-based access
- Helm in outline; debugging with kubectl

# Boss

Deploy a multi-service application to a cluster with zero-downtime rollouts.

Passes when:

- a rollout under load loses no request
- a bad image rolls back
- every container has probes and limits
- configuration and secrets are not baked into images
