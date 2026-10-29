---
id: sec-cloud-capstone
title: "Milestone: cloud & Kubernetes assessment"
track: sec
group: cloud-container
kind: milestone
prereqs: [sec-kubernetes-security, sec-cloud-attack-paths]
tags: [sec]
aliases: [cloud capstone, kubernetes capstone]
est_hours: 35
order: 50
summary: "Build a local containerised or Kubernetes environment, introduce controlled misconfigurations, map and validate attack paths, apply least privilege, and prove the paths are blocked."
---

# Boss

Build a local containerised or Kubernetes environment, introduce controlled misconfigurations, map possible attack paths, validate them in the lab, implement least-privilege controls, and demonstrate that the original paths have been blocked.

Passes when:

- the environment and its controlled misconfigurations are documented and reproducible
- each attack path is validated with evidence inside the lab
- least-privilege controls are applied and the original paths are shown to fail
- the audit trail supports the report and the work stays within owned resources
