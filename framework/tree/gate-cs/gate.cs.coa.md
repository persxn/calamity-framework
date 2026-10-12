---
id: gate.cs.coa
title: Computer Organization and Architecture
track: gate-cs
group: core
tags: [gate]
aliases: [coa, computer organisation, computer architecture, cache, pipelining]
paper: CS
marks: 8
marks_source: prior
source_url: "https://gate2027.iitm.ac.in/static/doc/GATE2027_Syllabus/CS_GATE2027_Syllabus.pdf"
est_hours: 60
syllabus_year: 2027
order: 20
summary: "Instructions and addressing, ALU and control unit, memory and caches, I/O, pipelining."
---

Topics follow section 3 of the official GATE 2027 syllabus for Computer Science and Information Technology (read 2026-10-11). If the official document and this file ever differ, the official document wins: write the corrected list to `learner/syllabus/gate.cs.coa.md` and it replaces this one. The marks figure is a planning prior, not an official number; replace it with `gate weight` or `gate weights --apply`.

# Topics

## instruction-set | Instruction set
level: 2
- instruction formats and fields; counting instructions with expanding opcodes

## addressing-modes | Addressing modes
level: 2
- immediate, direct, indirect, register, indexed, relative, auto-increment; compute the effective address

## alu | ALU design
level: 2
- arithmetic and logic operations in the datapath; adders, shifters, status flags

## control-unit | Control unit design: hardwired and microprogrammed
level: 3
- control signals for a micro-operation sequence; horizontal versus vertical microprograms; control word size

## memory-interfacing | Memory interfacing
level: 2
- build a memory from smaller chips; address lines, decoding and chip-select logic

## memory-hierarchy | Memory hierarchy performance
level: 2
- locality; hit ratio; average access time across levels

## cache-mapping | Cache mapping
level: 3
- direct, associative and set-associative mapping; tag, index and offset bits; replacement

## io-interface | I/O interface: interrupt and DMA modes
level: 2
- programmed, interrupt-driven and DMA transfer; interrupt priority; cycle stealing and burst mode

## pipelining | Instruction pipelining
level: 3
- stages, cycle time with register delay, speed-up and throughput

## pipeline-hazards | Pipeline hazards
level: 3
- structural, data and control hazards; forwarding, stalls and branch penalty; effective time per instruction
