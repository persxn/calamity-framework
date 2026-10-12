---
id: gate.da.ai
title: AI
track: gate-da
group: subjects
tags: [gate]
aliases: [ai, artificial intelligence]
overlaps: [gate.cs.discrete-math]
paper: DA
marks: 12
marks_source: prior
source_url: "https://gate2027.iitm.ac.in/static/doc/GATE2027_Syllabus/DA_GATE2027_Syllabus.pdf"
est_hours: 40
syllabus_year: 2027
order: 70
summary: "Search, logic, and reasoning under uncertainty."
---

Topics follow section 7 of the official GATE 2027 syllabus for Data Science and Artificial Intelligence (read 2026-10-11). If the official document and this file ever differ, the official document wins: write the corrected list to `learner/syllabus/gate.da.ai.md` and it replaces this one. The marks figure is a planning prior, not an official number; replace it with `gate weight` or `gate weights --apply`.

# Topics

## uninformed-search | Search: uninformed
level: 2
- BFS, DFS, uniform-cost and iterative deepening; completeness and cost

## informed-search | Search: informed
level: 3
- greedy best-first and A*; admissible and consistent heuristics

## adversarial-search | Search: adversarial
level: 3
- minimax and alpha-beta pruning on a game tree

## propositional-logic | Logic: propositional
level: 2
same_as: [gate.cs.discrete-math/propositional-logic]
- equivalences, satisfiability, inference

## predicate-logic | Logic: predicate
level: 3
same_as: [gate.cs.discrete-math/first-order-logic]
- quantifiers, translation, inference

## conditional-independence | Reasoning under uncertainty: conditional independence representation
level: 3
- read independences off a Bayesian network; factorise the joint distribution

## variable-elimination | Exact inference through variable elimination
level: 4
- eliminate variables in an order; the factors each step creates

## approximate-inference | Approximate inference through sampling
level: 4
- prior, rejection and likelihood-weighted sampling; Gibbs sampling in outline
