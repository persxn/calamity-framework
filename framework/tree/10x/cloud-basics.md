---
id: cloud-basics
title: Cloud fundamentals
track: 10x
group: devops
prereqs: [networking, linux-shell]
aliases: [aws, gcp, azure, iam, vpc, cloud]
est_hours: 25
order: 50
summary: "One provider, properly: compute, storage, networking, IAM, managed databases, cost, the CLI."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- regions and zones; the shared responsibility model
- compute: virtual machines, containers, serverless
- storage: object and block
- networking: virtual networks, subnets, security groups, load balancers
- identity and access management with least privilege
- managed databases
- cost awareness and budgets; the provider's CLI

# Boss

Deploy a containerised service with a managed database on one cloud provider, by CLI.

Passes when:

- the service is reachable over HTTPS
- the database is not publicly reachable
- no credential has administrator rights
- a budget alert exists, and everything is torn down afterwards
