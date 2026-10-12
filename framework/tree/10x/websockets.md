---
id: websockets
title: WebSockets
track: 10x
group: api
prereqs: [rest-api-design, "slot:backend-framework"]
tags: [api]
aliases: [realtime, real-time, socket.io, sse]
est_hours: 12
order: 40
summary: "Real-time communication: the upgrade handshake, rooms and broadcast, reconnection, auth, scaling."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- the upgrade handshake, frames, ping and pong
- when Server-Sent Events are enough
- rooms and broadcast patterns
- reconnection with backoff; message ordering
- authenticating sockets
- scaling out: sticky sessions and pub/sub

# Boss

Build a live feature (chat or a live dashboard) with reconnect and auth.

Passes when:

- a dropped connection recovers without losing messages
- an unauthenticated socket is refused
- two server instances deliver to the same room through pub/sub
