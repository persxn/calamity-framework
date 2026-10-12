---
id: gate.cs.databases
title: Databases
track: gate-cs
group: core
tags: [gate]
aliases: [dbms, databases, sql]
overlaps: [gate.da.dbms-warehousing]
paper: CS
marks: 8
marks_source: prior
source_url: "https://gate2027.iitm.ac.in/static/doc/GATE2027_Syllabus/CS_GATE2027_Syllabus.pdf"
est_hours: 50
syllabus_year: 2027
order: 80
summary: "ER and relational models, queries, normal forms, storage and indexing, transactions and concurrency."
---

Topics follow section 9 of the official GATE 2027 syllabus for Computer Science and Information Technology (read 2026-10-11). If the official document and this file ever differ, the official document wins: write the corrected list to `learner/syllabus/gate.cs.databases.md` and it replaces this one. The marks figure is a planning prior, not an official number; replace it with `gate weight` or `gate weights --apply`.

# Topics

## er-model | ER model
level: 2
same_as: [gate.da.dbms-warehousing/er-model]
- entities, relationships, cardinality and participation; minimum number of tables for a diagram

## relational-model | Relational model
level: 2
same_as: [gate.da.dbms-warehousing/relational-model]
- schemas; super, candidate, primary and foreign keys

## relational-algebra | Relational algebra
level: 2
same_as: [gate.da.dbms-warehousing/relational-algebra]
- select, project, joins, division and set operations; size of a result

## tuple-calculus | Tuple calculus
level: 3
same_as: [gate.da.dbms-warehousing/tuple-calculus]
- read and write tuple relational calculus queries; safe expressions

## sql | SQL
level: 2
same_as: [gate.da.dbms-warehousing/sql]
- joins, grouping and HAVING, nested and correlated subqueries, set operations, NULL behaviour

## integrity-constraints | Integrity constraints
level: 2
same_as: [gate.da.dbms-warehousing/integrity-constraints]
- domain, key, entity and referential integrity; actions on delete and update

## normal-forms | Normal forms
level: 3
same_as: [gate.da.dbms-warehousing/normal-forms]
- functional dependencies, closures, candidate keys, minimal cover; 1NF to BCNF
- lossless join and dependency preservation

## file-organization | File organization
level: 2
same_as: [gate.da.dbms-warehousing/file-organization]
- records per block; ordered, unordered and hashed files

## indexing | Indexing (B and B+ trees)
level: 3
same_as: [gate.da.dbms-warehousing/indexing]
- primary, clustering and secondary indexes; dense and sparse; order, height and capacity of B/B+ trees

## transactions | Transactions
level: 3
- ACID; conflict and view serializability; recoverable, cascadeless and strict schedules

## concurrency-control | Concurrency control
level: 3
- two-phase locking and its variants; timestamp ordering; deadlocks between transactions
