---
id: ai-capstone
title: "Milestone: LLM application engineer"
track: ai
group: milestones
kind: milestone
prereqs: [rag-qdrant, rag-vectorless, llm-evals, llm-agents, ollama]
aliases: [llm engineer, rag capstone]
order: 20
summary: "A documented LLM system that runs locally, retrieves two ways, and is measured."
---

# Boss

Ship a question-answering system over a real corpus with both retrieval routes (Qdrant and vectorless), a router that picks between them, a local-model mode through Ollama, and one evaluation harness for all of it.

Passes when:

- one command brings the whole system up in containers
- the harness reports each route and the router on the same question set
- the local-model mode passes the same harness, with the quality gap stated
- the README lets another developer reproduce every number
