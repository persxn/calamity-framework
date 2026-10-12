---
id: gate.cs.digital-logic
title: Digital Logic
track: gate-cs
group: core
tags: [gate]
aliases: [digital logic, dl, k-map, boolean algebra]
paper: CS
marks: 8
marks_source: prior
source_url: "https://gate2027.iitm.ac.in/static/doc/GATE2027_Syllabus/CS_GATE2027_Syllabus.pdf"
est_hours: 40
syllabus_year: 2027
order: 10
summary: "Boolean algebra and minimization, combinational and sequential design, number representation and arithmetic."
---

Topics follow section 2 of the official GATE 2027 syllabus for Computer Science and Information Technology (read 2026-10-11). If the official document and this file ever differ, the official document wins: write the corrected list to `learner/syllabus/gate.cs.digital-logic.md` and it replaces this one. The marks figure is a planning prior, not an official number; replace it with `gate weight` or `gate weights --apply`.

# Topics

## boolean-algebra | Boolean algebra
level: 2
- laws, De Morgan, duality; canonical SOP and POS forms; functionally complete sets of gates

## minimization-kmap | Minimization: algebraic technique and Karnaugh map
level: 2
- simplify algebraically; K-maps with don't-cares; prime and essential prime implicants

## minimization-tabular | Minimization: tabular method
level: 3
- group minterms by number of ones, combine, and choose a cover from the prime implicant chart

## combinational-circuits | Combinational circuit design
level: 2
- adders, multiplexers, decoders, encoders, comparators; build a function from a MUX or a decoder

## sequential-circuits | Sequential circuit design
level: 3
- latches and flip-flops with their excitation tables; counters and shift registers
- design from a state diagram; Mealy and Moore machines

## number-representation | Number representation
level: 2
- bases and conversion; signed magnitude, 1's and 2's complement; ranges and overflow

## fixed-point-arithmetic | Fixed-point arithmetic
level: 2
- addition and subtraction in 2's complement; overflow rules; multiplication in outline

## floating-point | Floating-point representation and arithmetic
level: 3
- sign, biased exponent and mantissa; normalised and special values; rounding
