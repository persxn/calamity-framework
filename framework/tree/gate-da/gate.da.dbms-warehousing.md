---
id: gate.da.dbms-warehousing
title: Database Management and Warehousing
track: gate-da
group: subjects
tags: [gate]
aliases: [dbms, data warehouse, warehousing]
overlaps: [gate.cs.databases]
paper: DA
marks: 12
marks_source: prior
source_url: "https://gate2027.iitm.ac.in/static/doc/GATE2027_Syllabus/DA_GATE2027_Syllabus.pdf"
est_hours: 45
syllabus_year: 2027
order: 50
summary: "The relational side of databases, then data transformation and warehouse modelling."
---

Topics follow section 5 of the official GATE 2027 syllabus for Data Science and Artificial Intelligence (read 2026-10-11). If the official document and this file ever differ, the official document wins: write the corrected list to `learner/syllabus/gate.da.dbms-warehousing.md` and it replaces this one. The marks figure is a planning prior, not an official number; replace it with `gate weight` or `gate weights --apply`.

# Topics

## er-model | ER model
level: 2
same_as: [gate.cs.databases/er-model]
- entities, relationships, cardinality

## relational-model | Relational model
level: 2
same_as: [gate.cs.databases/relational-model]
- schemas and keys

## relational-algebra | Relational algebra
level: 2
same_as: [gate.cs.databases/relational-algebra]
- operators and result sizes

## tuple-calculus | Tuple calculus
level: 3
same_as: [gate.cs.databases/tuple-calculus]
- read and write tuple calculus queries

## sql | SQL
level: 2
same_as: [gate.cs.databases/sql]
- joins, grouping, subqueries, NULL behaviour

## integrity-constraints | Integrity constraints
level: 2
same_as: [gate.cs.databases/integrity-constraints]
- key, entity and referential integrity

## normal-forms | Normal forms
level: 3
same_as: [gate.cs.databases/normal-forms]
- functional dependencies and 1NF to BCNF

## file-organization | File organization
level: 2
same_as: [gate.cs.databases/file-organization]
- records per block; kinds of files

## indexing | Indexing
level: 3
same_as: [gate.cs.databases/indexing]
- kinds of index; B and B+ trees

## data-types | Data types
level: 2
- kinds of attributes and data: nominal, ordinal, interval, ratio

## data-transformation | Data transformation: normalization, discretization, sampling, compression
level: 2
- min-max and z-score normalisation; binning; sampling schemes; lossless and lossy reduction

## warehouse-modelling | Data warehouse modelling: schema for multidimensional data models
level: 3
- facts and dimensions; star, snowflake and fact-constellation schemas; cube operations

## concept-hierarchies | Concept hierarchies
level: 2
- levels of a dimension; roll-up and drill-down along them

## measures | Measures: categorization and computations
level: 3
- distributive, algebraic and holistic measures; which can be computed from sub-aggregates
