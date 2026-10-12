---
id: mongodb
title: MongoDB
track: 10x
group: data
prereqs: ["slot:language"]
tags: [database]
weaves_into: [backend-framework]
aliases: [mongo, mongoose, nosql, document database]
est_hours: 20
order: 30
summary: "The document model: CRUD and queries, schema design (embed or reference), indexes, aggregation."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- documents, collections, CRUD, query operators
- schema design: embedding versus referencing, by access pattern
- indexes and `explain`
- the aggregation pipeline
- transactions; replica sets in outline
- using a driver or Mongoose from application code

# Boss

Model a domain with nested and referenced data and build three aggregation reports on it.

Passes when:

- every frequent query is covered by an index (`explain` shows it)
- the reports return correct figures on seed data
- the embed-or-reference choice is justified for each relation
