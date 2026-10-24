---
id: mcp-servers
title: "MCP servers"
track: ai
group: agents
prereqs: [agent-loops]
tags: [ai, llm, runnable]
weaves_into: [llm]
aliases: [mcp, model context protocol, mcp server, tools, resources]
est_hours: 20
order: 20
summary: "Build a Model Context Protocol server so one tool integration works across every compatible host."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- what MCP is: a host's client discovers and calls a server's tools, reads its resources and uses its prompts
- tools with typed input schemas; resources as read-only data addressed by URI; prompts as reusable templates
- transports: a local process over stdio, a remote server over HTTP; choosing between them
- the access boundary: resolve paths and refuse escapes, deny-list sensitive files, expose no write you did not intend
- errors returned as tool results, so the host sees the reason and the server stays up
- testing a server: a normal call, an invalid input, a refused path; connecting a real client
- when MCP earns its keep over a plain library or HTTP API
- secrets from the environment, never from arguments or logs; server output is data to the host, not instructions

# Boss

Build and test a read-only MCP server that exposes a safe view of one resource, for example a repository, then connect it to a host.

Passes when:

- tests cover a normal call, an invalid input and a refused path, and all pass
- a path that escapes the allowed root is refused, not served
- a sensitive file, such as a key or an environment file, is never listed or returned
- the server's tools are visible and callable from a real client
