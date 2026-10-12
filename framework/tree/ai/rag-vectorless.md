---
id: rag-vectorless
title: Vectorless RAG
track: ai
group: llm
prereqs: [langchain]
slot: rag
tags: [ai, llm, runnable]
weaves_into: [llm]
aliases: [vectorless rag, reasoning-based retrieval, bm25, full-text search, document tree index, agentic search]
est_hours: 30
order: 50
summary: "Retrieval without embeddings: structure-aware indexes, lexical search and model-driven navigation."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- why skip vectors: exact terms, long structured documents, auditability, no embedding pipeline to maintain
- lexical retrieval: tokenisation, BM25, full-text search in PostgreSQL or SQLite FTS5
- structure-aware indexes: tables of contents, heading trees, summaries per node
- model-driven navigation: the model reads an index, picks a branch, descends, then reads the leaf
- tool-driven retrieval: search and read tools (grep-like search, SQL, an API) inside an agent loop
- metadata and filters as the first retrieval step
- cost and latency: more model calls per question, and how to cap them
- where it loses: paraphrase-heavy queries, unstructured corpora
- combining it with vector retrieval, and deciding per query

# Boss

Answer questions over the same corpus used for vector RAG with no embeddings at all: build a heading-tree index with node summaries, let the model navigate it, and add a full-text search tool as a second route.

Passes when:

- every answer lists the path through the index that led to its source
- accuracy on the labelled question set meets the bar the tutor sets
- model calls per question stay under a fixed cap, enforced in code
- a short report says which question types each route wins, with examples

# Weave

This framework's own lookup (index, then tree node, then topic, then notes) is a worked example to study.
