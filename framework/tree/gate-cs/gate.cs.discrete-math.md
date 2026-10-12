---
id: gate.cs.discrete-math
title: Discrete Mathematics
track: gate-cs
group: engineering-maths
tags: [gate]
aliases: [discrete mathematics, dm, logic, graph theory]
overlaps: [gate.da.ai]
paper: CS
marks: 5.5
marks_source: prior
source_url: "https://gate2027.iitm.ac.in/static/doc/GATE2027_Syllabus/CS_GATE2027_Syllabus.pdf"
est_hours: 60
syllabus_year: 2027
order: 10
summary: "Logic, sets, relations, functions, orders, groups, graphs and counting."
---

Topics follow section 1 (Engineering Mathematics) of the official GATE 2027 syllabus for Computer Science and Information Technology (read 2026-10-11). If the official document and this file ever differ, the official document wins: write the corrected list to `learner/syllabus/gate.cs.discrete-math.md` and it replaces this one. The marks figure is a planning prior, not an official number; replace it with `gate weight` or `gate weights --apply`.

# Topics

## propositional-logic | Propositional logic
level: 2
same_as: [gate.da.ai/propositional-logic]
- connectives, truth tables, logical equivalence, tautology, contradiction, satisfiability
- implication and its converse, inverse and contrapositive; normal forms; validity of an argument

## first-order-logic | First-order logic
level: 3
same_as: [gate.da.ai/predicate-logic]
- predicates and quantifiers; translate between English and logic; negate nested quantifiers
- valid versus satisfiable formulas

## sets-relations | Sets and relations
level: 2
- set operations, power sets, cardinality
- reflexive, symmetric, antisymmetric, transitive; equivalence relations and partitions; closures; counting relations of each kind

## functions | Functions
level: 2
- injective, surjective, bijective; composition and inverse; counting functions between finite sets

## partial-orders-lattices | Partial orders and lattices
level: 3
- posets and Hasse diagrams; minimal, maximal, least, greatest elements; lub and glb
- bounded, distributive and complemented lattices

## groups | Monoids and groups
level: 3
- semigroup, monoid and group axioms; abelian and cyclic groups; order of an element
- subgroups, cosets and Lagrange's theorem

## graph-connectivity | Graphs: connectivity
level: 2
- degree sequences and the handshaking lemma; paths, cycles, components
- cut vertices, bridges, vertex and edge connectivity; trees as minimally connected graphs

## graph-matching | Graphs: matching
level: 3
- matchings, maximum and perfect matchings; bipartite graphs and Hall's condition; covers

## graph-colouring | Graphs: colouring
level: 3
- chromatic number and its bounds; bipartite means 2-colourable; colouring planar graphs

## counting | Combinatorics: counting
level: 2
- sum and product rules; permutations and combinations with and without repetition
- pigeonhole principle; inclusion-exclusion; derangements; binomial identities

## recurrence-relations | Combinatorics: recurrence relations
level: 3
- set up a recurrence for a counting problem; solve linear recurrences with constant coefficients

## generating-functions | Combinatorics: generating functions
level: 4
- ordinary generating functions; closed forms; extract a coefficient to count
