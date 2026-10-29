---
id: sec-infra-capstone
title: "Milestone: infrastructure assessment"
track: sec
group: network-infra
kind: milestone
prereqs: [sec-attack-paths]
tags: [sec]
aliases: [infrastructure capstone, network assessment capstone]
est_hours: 35
order: 40
summary: "Map an isolated multi-host lab, identify and validate a chain of weaknesses, remediate, and prove the attack path is closed."
---

# Boss

Build an isolated multi-host environment, map its attack surface, identify a chain of misconfigurations or vulnerabilities, validate the impact in the lab, improve the configuration, and verify that the original attack path no longer works.

Passes when:

- the attack surface and the full chain are documented with reproducible evidence
- the impact of the chain is validated inside the isolated lab
- the remediation is applied and the original path is demonstrated to fail
- the report is reproducible by another person from the written steps and stays within the owned lab
