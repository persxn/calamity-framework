---
id: langchain
title: "LangChain & LangGraph"
track: ai
group: llm
prereqs: [llm-basics]
tags: [ai, llm, runnable]
weaves_into: [llm]
aliases: [lcel, langgraph, llm framework, chains]
est_hours: 30
order: 30
summary: "Compose model calls, prompts, parsers, retrievers and tools into applications you can test."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- the runnable interface and composition (LCEL): invoke, batch, stream
- prompt templates, chat models, output parsers, structured output
- document loaders and text splitters
- retrievers and vector store integrations as interfaces
- tools and tool-calling models
- LangGraph: state, nodes, edges, conditional routing, persistence, human-in-the-loop
- tracing and debugging a chain; callbacks
- when not to use a framework: reading what a chain really sends to the model
- version awareness: the library moves fast, so check current documentation before relying on an API

# Boss

Rebuild the llm-basics assistant as a LangGraph application with a retry branch and a human-approval step, then write the same core flow without any framework and compare.

Passes when:

- the graph's state transitions are covered by tests with a fake model
- the trace of one run shows every prompt sent to the model
- the framework-free version produces the same outputs on the test inputs

# Weave

RAG and agent skills build on these interfaces; exercises should make the learner print the final prompt.
