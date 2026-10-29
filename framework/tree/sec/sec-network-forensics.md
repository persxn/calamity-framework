---
id: sec-network-forensics
title: "Network investigation"
track: sec
group: forensics
prereqs: [sec-evidence, sec-networking]
tags: [sec]
weaves_into: [sec]
aliases: [network forensics, pcap analysis, dns investigation, beaconing]
est_hours: 25
order: 30
summary: "Reconstructing activity from network evidence: reading packet captures and metadata, spotting unusual patterns, and correlating the network view with the hosts."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- packet-capture analysis
- DNS investigation
- HTTP and TLS metadata
- connection timelines
- unusual traffic patterns
- beaconing concepts
- lateral-movement indicators on the network
- exfiltration indicators
- correlating network artefacts with host artefacts

# Boss

From a packet capture of activity on a network you own, reconstruct the connections and their timeline, identify any unusual pattern, and correlate the network view with the host evidence for the same events.

Passes when:

- the connection timeline is reconstructed correctly from the capture
- any unusual pattern is identified and explained, or its absence justified
- at least one network observation is correlated with a matching host artefact
- the write-up distinguishes what the capture shows from what it only suggests

# Weave

The network view and the host view are the two halves a reconstruction joins.
