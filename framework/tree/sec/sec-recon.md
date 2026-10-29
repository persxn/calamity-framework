---
id: sec-recon
title: "Reconnaissance & service analysis"
track: sec
group: network-infra
prereqs: [sec-networking]
tags: [sec]
weaves_into: [sec]
aliases: [recon, enumeration, scanning, service fingerprinting]
est_hours: 25
order: 10
summary: "Discovering hosts and services and understanding what they are, with professional tools and a scanner you write yourself so you know what the tools do."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill. All scanning is on
hosts the learner owns or is explicitly authorised to test.

- host discovery and service enumeration on an isolated network
- port states and what each one implies about the host's response
- service fingerprinting and version identification
- protocol-specific probing of a listening service
- capturing and interpreting the traffic a scan produces
- building a network map from the results
- how a firewall changes what a scan sees
- reading segmentation and trust boundaries from scan results
- writing a simplified scanner and a small protocol client, and comparing their output with a professional tool

# Boss

On an isolated lab network of your own, map every host and service two ways: with a professional scanner and with a scanner you write yourself. Explain every difference between the two sets of results.

Passes when:

- both tools run against the lab and their results are reconciled host by host, service by service
- each discrepancy is explained by a property of the protocol, the host or the tool, not hand-waved
- the learner reads the port states correctly and relates them to the hosts' actual configuration
- the exercise stays entirely within the owned lab, with scope stated up front

# Weave

Recon and the habit of verifying a tool against your own implementation open every infrastructure and cloud assessment.
