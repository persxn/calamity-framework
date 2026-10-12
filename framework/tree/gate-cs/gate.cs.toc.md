---
id: gate.cs.toc
title: Theory of Computation
track: gate-cs
group: core
tags: [gate]
aliases: [toc, automata, theory of computation]
paper: CS
marks: 8
marks_source: prior
source_url: "https://gate2027.iitm.ac.in/static/doc/GATE2027_Syllabus/CS_GATE2027_Syllabus.pdf"
est_hours: 55
syllabus_year: 2027
order: 50
summary: "Regular and context-free languages with their machines, Turing machines and undecidability."
---

Topics follow section 6 of the official GATE 2027 syllabus for Computer Science and Information Technology (read 2026-10-11). If the official document and this file ever differ, the official document wins: write the corrected list to `learner/syllabus/gate.cs.toc.md` and it replaces this one. The marks figure is a planning prior, not an official number; replace it with `gate weight` or `gate weights --apply`.

# Topics

## regular-expressions | Regular expressions
level: 2
- write an expression for a language; convert between expressions and automata

## finite-automata | Finite automata
level: 2
- DFA, NFA and epsilon-NFA; subset construction; minimisation; number of states needed

## regular-languages | Regular languages
level: 2
- closure properties and decision problems of regular languages

## context-free-grammars | Context-free grammars
level: 2
- derivations and parse trees; ambiguity; simplification and normal forms

## pushdown-automata | Push-down automata
level: 3
- design a PDA; acceptance by final state and by empty stack; deterministic versus non-deterministic

## context-free-languages | Context-free languages
level: 3
- closure properties; deterministic context-free languages; membership and emptiness

## pumping-lemma | Pumping lemma
level: 3
- use it to show a language is not regular or not context-free

## turing-machines | Turing machines
level: 3
- the model and its variants; recursive and recursively enumerable languages

## undecidability | Undecidability
level: 4
- the halting problem; reductions; Rice's theorem; which problems are decidable for which class
