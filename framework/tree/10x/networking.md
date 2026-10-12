---
id: networking
title: Networking for developers
track: 10x
group: foundations
prereqs: [linux-shell]
weaves_into: [backend, backend-framework, devops, api]
aliases: [network, tcp/ip, dns, http, tls]
est_hours: 25
order: 40
summary: "How machines talk: IP and subnets, DNS, TCP and UDP, HTTP, TLS, proxies, and the tools to debug them."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- layering: link, internet, transport, application, and what each layer adds
- IP addressing: IPv4 and IPv6, subnets and CIDR, private ranges, NAT, routing in outline
- DNS: record types, resolution, TTL, debugging with dig
- TCP and UDP: handshake, ports, sockets, reliability, timeouts
- HTTP/1.1, HTTP/2 and HTTP/3 in outline: methods, status codes, headers, caching, cookies, CORS
- TLS and HTTPS: certificates, chains of trust, the handshake at a high level
- proxies, reverse proxies, load balancers, CDNs, firewalls
- tools: curl, dig, ping, traceroute, ss, tcpdump or Wireshark basics

# Boss

Diagnose a broken multi-service setup. The tutor supplies a compose file with four planted faults (a wrong DNS name, a closed port, a certificate mismatch, a CORS error). Find each with command-line tools and write a short diagnosis report.

Passes when:

- every fault is identified with the command and output that proved it
- after the fixes, `curl` returns 200 over HTTPS for each service
- the report explains each fault in terms of the layer it lives in

# Weave

Backend, API and DevOps exercises should make the learner reason about ports, DNS names, headers and TLS.
