---
id: grpc
title: "gRPC & Protocol Buffers"
track: 10x
group: api
prereqs: [rest-api-design, "slot:backend-framework"]
tags: [api]
aliases: [protobuf, rpc]
optional: true
est_hours: 12
order: 50
summary: "Binary, contract-first RPC between services: proto files, code generation, streaming, deadlines."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- Protocol Buffers: messages, fields, evolution rules
- services, unary and streaming calls
- code generation; deadlines, errors, metadata
- when to choose gRPC over REST

# Boss

Split one internal call of an existing system into a gRPC service.

Passes when:

- a schema change stays backward compatible
- calls carry deadlines
- client and server tests pass
