---
id: sec-os-internals
title: "Operating-system internals"
track: sec
group: foundations
prereqs: [sec-programming]
tags: [sec]
weaves_into: [sec]
aliases: [linux internals, os internals, privilege boundaries, process internals]
est_hours: 35
order: 20
summary: "How Linux (and, in outline, Windows) runs programs, isolates them and records what they do: processes, memory, privilege boundaries and the telemetry they leave."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- filesystem layout and permissions; users, groups, capabilities and the sudo boundary
- processes, threads, signals and the process tree; how a program is started
- system calls and the user/kernel transition; tracing them on a running program
- virtual memory: pages, mappings and address spaces, and why addresses are not physical
- ELF binaries, shared libraries, dynamic linking and loading
- services and daemons under a service manager; startup and persistence points
- namespaces and cgroups: the isolation that containers are built from
- temporary files, resource ownership and the races they invite
- logs, audit records and process telemetry: what the system remembers
- Linux security mechanisms (DAC, capabilities, seccomp, MAC in outline) and their limits

# Boss

On a machine or VM you own, instrument a single program end to end: trace its system calls, map its memory while it runs, follow it in the process tree, and collect every log and audit record it produces. Write up what the operating system knew about that program at each moment.

Passes when:

- the write-up shows the system-call trace, the memory map and the process-tree position, each read correctly
- the learner names which privilege boundary the program sits behind and what would have to happen to cross it
- the collected telemetry is matched to the actions that produced it, with any gaps noted
- the whole investigation is reproducible from the written steps on a fresh VM

# Weave

Privilege boundaries, process telemetry and memory layout recur in every branch: exploitation, infrastructure, enterprise, cloud and forensics all rest on them.
