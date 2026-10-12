---
id: node
title: Node.js
track: 10x
group: backend
prereqs: [javascript, linux-shell]
tags: [backend, js-ecosystem, runnable]
aliases: [nodejs, node.js, event loop]
est_hours: 30
order: 10
summary: "JavaScript on the server: the event loop, streams, core modules, error handling, graceful shutdown."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- the runtime model: event loop, non-blocking I/O, the thread pool
- streams and buffers; back-pressure
- modules, npm scripts, configuration from the environment
- core modules: fs, path, http, events, child_process; worker threads in outline
- error handling in async code; graceful shutdown on signals
- debugging and profiling; security basics

# Boss

Build a command-line tool and a small HTTP service with no framework, for example a file-processing service that streams.

Passes when:

- a 1 GB input is processed with flat memory use
- exit codes are correct for success and failure
- SIGTERM finishes in-flight work before exiting
- tests pass
