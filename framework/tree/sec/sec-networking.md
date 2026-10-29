---
id: sec-networking
title: "Networking & protocols"
track: sec
group: foundations
prereqs: [sec-programming]
tags: [sec]
weaves_into: [sec]
aliases: [network fundamentals, protocols, tcp ip, packet analysis]
est_hours: 35
order: 30
summary: "The protocol stack from the wire up, read by capturing real traffic and comparing it with how the protocol is supposed to behave."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- binary and hexadecimal; reading a protocol field from raw bytes
- Ethernet, ARP, IP, ICMP, TCP and UDP, and the state a connection carries
- routing, NAT, subnetting and segmentation; why a packet reaches one host and not another
- DNS, DHCP, HTTP, TLS and certificates: what each exchange establishes
- ports, sockets, listeners and connection states
- capturing packets and dissecting a protocol; comparing captured traffic with the specification
- client/server architecture; writing a small client and a small server
- authentication and session establishment over the network
- firewalls, network policy, proxies, VPNs and tunnels, and what each one hides or exposes
- network namespaces and virtual networks for building isolated test topologies

# Boss

Write a minimal client and server that speak a small protocol of your design over TCP, run them inside network namespaces you create, capture the exchange, and annotate the capture packet by packet against your own specification.

Passes when:

- the client and server complete an exchange that the capture shows in full, from handshake to close
- the annotation names every field that matters and flags any packet that diverges from the specification
- the learner explains the TCP connection states the capture passes through
- the whole setup is brought up and torn down by a script, leaving no stray interfaces

# Weave

Packet capture, protocol state and trust boundaries on the network underlie recon, service security, cloud networking and network forensics.
