---
id: gate.cs.compiler-design
title: Compiler Design
track: gate-cs
group: core
tags: [gate]
aliases: [compilers, cd, compiler]
paper: CS
marks: 8
marks_source: prior
source_url: "https://gate2027.iitm.ac.in/static/doc/GATE2027_Syllabus/CS_GATE2027_Syllabus.pdf"
est_hours: 40
syllabus_year: 2027
order: 60
summary: "Lexing, parsing, syntax-directed translation, runtime environments, intermediate code and optimisation."
---

Topics follow section 7 of the official GATE 2027 syllabus for Computer Science and Information Technology (read 2026-10-11). If the official document and this file ever differ, the official document wins: write the corrected list to `learner/syllabus/gate.cs.compiler-design.md` and it replaces this one. The marks figure is a planning prior, not an official number; replace it with `gate weight` or `gate weights --apply`.

# Topics

## lexical-analysis | Lexical analysis
level: 2
- tokens, lexemes and patterns; count the tokens in a fragment

## parsing | Parsing
level: 3
- FIRST and FOLLOW; LL(1); the LR family (LR(0), SLR, LALR, CLR) and their conflicts

## syntax-directed-translation | Syntax-directed translation
level: 3
- synthesized and inherited attributes; S-attributed and L-attributed definitions; evaluate a parse tree

## runtime-environments | Runtime environments
level: 2
- activation records; stack and heap allocation; parameter passing; static and dynamic scope

## intermediate-code | Intermediate code generation
level: 2
- three-address code, quadruples and triples; DAGs; static single assignment form

## local-optimisation | Local optimisation
level: 2
- basic blocks; constant folding, copy propagation, dead-code elimination, strength reduction

## data-flow-analysis | Data flow analyses: constant propagation, liveness, common subexpression elimination
level: 4
- control-flow graphs; live variables as a backward analysis; available expressions as a forward analysis
