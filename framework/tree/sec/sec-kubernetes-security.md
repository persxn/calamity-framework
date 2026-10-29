---
id: sec-kubernetes-security
title: "Kubernetes security"
track: sec
group: cloud-container
prereqs: [sec-container-security, kubernetes]
tags: [sec]
weaves_into: [sec]
aliases: [kubernetes security, k8s, rbac, admission control, cluster audit]
est_hours: 30
order: 30
summary: "The security model of a Kubernetes cluster: the API server and RBAC, service accounts and secrets, network policy and admission control, and the boundaries between workloads and nodes."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill. Work is on a local
cluster the learner owns.

- control-plane architecture
- API-server authentication and authorisation
- RBAC: roles, bindings and what they grant
- service accounts and their tokens
- pods, deployments and workloads
- network policies between workloads
- admission control
- secrets and configuration handling
- node and workload isolation
- runtime monitoring and cluster audit logs
- container-escape concepts and workload-boundary analysis
- multi-tenant isolation

# Boss

On a local cluster you own, introduce a controlled RBAC or workload misconfiguration, show what it lets a workload reach, then apply least-privilege RBAC, a network policy and admission control to close it, and read the audit log that recorded the whole thing.

Passes when:

- the misconfiguration's reach is demonstrated from inside a workload in the lab
- the RBAC, network policy and admission changes are shown to close it
- the cluster audit log is read and matched to the actions taken
- the learner explains the boundary between a workload, its node and the control plane

# Weave

The cluster's identity and isolation model is where cloud and container attack paths converge.
