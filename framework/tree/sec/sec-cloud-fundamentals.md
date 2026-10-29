---
id: sec-cloud-fundamentals
title: "Cloud fundamentals & IAM"
track: sec
group: cloud-container
prereqs: [sec-networking, sec-fundamentals]
tags: [sec]
weaves_into: [sec]
aliases: [cloud security, iam, identity federation, metadata service]
est_hours: 25
order: 10
summary: "How a cloud account is structured and secured: networking and isolation, identity and policy, secrets, storage, and the metadata and audit surfaces that attackers and defenders both read."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill. Work uses the
learner's own account or free-tier resources, within the provider's terms.

- cloud networking and the isolation between tenants and resources
- virtual machines and their isolation
- IAM and identity federation
- roles, policies and trust relationships, read from the policy document
- secrets management
- object storage security and its common exposures
- network security groups and firewalls in the cloud
- metadata services and why they are a security-sensitive surface
- audit logs and cloud telemetry
- evaluating a configuration or policy against least privilege

# Boss

In your own cloud account (or a local emulator), model the identity and trust relationships of a small deployment: read the policies, draw who can assume what and reach which resource, and identify the least-privilege gap.

Passes when:

- the identity and trust graph is drawn from the actual policy documents and is correct
- at least one over-broad permission or trust relationship is identified and explained
- the learner explains why the metadata service matters to that deployment
- the corrected policy is shown to remove the excess access without breaking the deployment

# Weave

Cloud identity, policy and metadata surfaces are the ground every cloud attack-path exercise stands on.
