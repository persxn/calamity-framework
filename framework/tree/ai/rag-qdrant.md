---
id: rag-qdrant
title: RAG with a vector database (Qdrant)
track: ai
group: llm
prereqs: [langchain, docker]
slot: rag
tags: [ai, llm, runnable]
weaves_into: [llm]
aliases: [rag, retrieval augmented generation, vector database, qdrant, embeddings search, hybrid search]
est_hours: 35
order: 40
summary: "Retrieval-augmented generation on embeddings: chunking, indexing in Qdrant, hybrid search, reranking, citations."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- the RAG loop: ingest, chunk, embed, index, retrieve, assemble context, generate, cite
- chunking strategies and their effect on retrieval
- choosing an embedding model; dimensions, distance metrics, normalisation
- Qdrant: collections, points, payloads, payload indexes, filters
- approximate nearest-neighbour search (HNSW) and its parameters; quantisation
- hybrid search: dense plus sparse vectors, fusion
- reranking; query rewriting; multi-query retrieval
- context assembly: ordering, deduplication, token budget, citations to sources
- keeping the index fresh: updates, deletes, re-embedding
- retrieval metrics: recall@k, MRR, nDCG

# Boss

Build a question-answering service over a document set of at least a few hundred pages, with Qdrant in a container, hybrid search, reranking, and answers that cite their sources.

Passes when:

- recall@5 on a labelled question set meets the bar the tutor sets, and beats a dense-only baseline
- every answer cites chunks that were actually retrieved
- a question with no answer in the corpus gets a refusal, not an invention
- re-ingesting a changed document updates its points without duplicating them

# Weave

Reuse Docker for Qdrant, and the evaluation habits from classical ML when measuring retrieval.
