---
id: sec-detection
title: "Detection-aware operations"
track: sec
group: enterprise-redteam
prereqs: [sec-enterprise]
tags: [sec]
weaves_into: [sec]
aliases: [detection engineering, blue team, sysmon, siem, att&ck mapping]
est_hours: 25
order: 30
summary: "How security controls see an attacker: the telemetry each action produces, how it is correlated in a SIEM, and where detection has gaps and false positives."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- Windows event logs and Sysmon where appropriate
- authentication events and what they reveal
- process creation and parent-child relationships
- network connection telemetry
- PowerShell logging and its coverage
- endpoint detection concepts
- SIEM queries and correlation across sources
- building an attack timeline from telemetry
- detection coverage, gaps and false positives
- mapping observed behaviour to ATT&CK techniques

# Boss

Take the telemetry from an emulation you ran (or a provided data set), and build detections for the chain: write the queries that would catch each step, assemble the timeline, and produce a detection-gap assessment with honest false-positive costs.

Passes when:

- each step of the chain is matched to the telemetry it produced, or shown to produce none
- the queries detect the intended behaviour and the learner states their false-positive cost
- the timeline is correct and the gaps are identified with what would close them
- each detection is mapped to the ATT&CK technique it covers

# Weave

Reading telemetry and reasoning about detection coverage connects emulation to forensics and to defensive value.
