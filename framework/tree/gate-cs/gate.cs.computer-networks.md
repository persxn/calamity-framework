---
id: gate.cs.computer-networks
title: Computer Networks
track: gate-cs
group: core
tags: [gate]
aliases: [cn, networks, computer networks, tcp]
paper: CS
marks: 8
marks_source: prior
source_url: "https://gate2027.iitm.ac.in/static/doc/GATE2027_Syllabus/CS_GATE2027_Syllabus.pdf"
est_hours: 55
syllabus_year: 2027
order: 90
summary: "Layering, switching and performance, the data link layer, routing, IPv4, TCP, DNS and HTTP."
---

Topics follow section 10 of the official GATE 2027 syllabus for Computer Science and Information Technology (read 2026-10-11). If the official document and this file ever differ, the official document wins: write the corrected list to `learner/syllabus/gate.cs.computer-networks.md` and it replaces this one. The marks figure is a planning prior, not an official number; replace it with `gate weight` or `gate weights --apply`.

# Topics

## layering | Principles of layering
level: 2
- why protocols are layered; services, interfaces and encapsulation; what each layer is responsible for

## switching | Switching basics: circuit, packet and virtual-circuit switching
level: 2
- compare the three; total delay for a message under each

## performance-metrics | Performance metrics
level: 2
- bandwidth, throughput, transmission and propagation delay, round-trip time, utilisation

## error-detection | Data link layer: error detection
level: 2
- parity, checksum and CRC by polynomial division; what each can detect

## medium-access-control | Data link layer: medium access control
level: 3
- ALOHA, CSMA/CD and CSMA/CA; efficiency; minimum frame size for collision detection

## ethernet | Data link layer: Ethernet
level: 2
- frame format and addressing; how switched Ethernet forwards

## distance-vector | Routing: distance vector
level: 3
- the table update rule; count-to-infinity and split horizon

## link-state | Routing: link state
level: 3
- link-state advertisements and Dijkstra's computation; contrast with distance vector

## ipv4-fragmentation | IPv4: fragmentation
level: 3
- identification, flags and offset; split a datagram for a given MTU

## cidr | IPv4: CIDR notation
level: 2
- prefixes and masks; subnetting and route aggregation; longest-prefix match

## nat | IPv4: NAT
level: 2
- private addresses and the translation table; port mapping

## tcp-flow-control | TCP: flow control
level: 3
- sequence and acknowledgement numbers; the sliding window and the advertised window

## tcp-congestion-control | TCP: congestion control
level: 3
- slow start, congestion avoidance, fast retransmit and recovery; trace the congestion window

## socket-api | TCP: socket API
level: 2
- socket, bind, listen, accept, connect, send and receive; the order on the client and on the server

## dns | DNS
level: 2
- name hierarchy; iterative and recursive resolution; record types; caching

## http | HTTP
level: 2
- requests and responses; methods and status codes; persistent connections
