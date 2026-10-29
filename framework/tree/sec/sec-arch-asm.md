---
id: sec-arch-asm
title: "Architecture & assembly"
track: sec
group: binary-exploitation
prereqs: [sec-programming, sec-os-internals]
tags: [sec]
weaves_into: [sec]
aliases: [assembly, reversing foundations, calling conventions, stack frames]
est_hours: 30
order: 10
summary: "Read machine code and reason from source to instructions: registers, calling conventions, stack frames and process memory under a debugger and a disassembler."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- instruction execution: how a CPU fetches, decodes and runs an instruction
- registers, memory addressing and the calling convention for the target platform
- reading assembly fluently, and writing small amounts by hand
- stack frames, function prologues and epilogues, arguments and return addresses
- process memory layout: code, data, heap, stack and mapped regions
- executable formats and linking, enough to find a function in a binary
- relating compiler-generated code back to the source that produced it
- driving a debugger: breakpoints, stepping, reading registers and memory
- driving a disassembler to navigate an unfamiliar binary

# Boss

Take a small C program you wrote, compile it, and reconstruct its behaviour purely from the binary: identify each function, its stack frame, how arguments arrive and how the return address is stored, using a debugger and a disassembler. Then predict a register and memory state at a chosen instruction and confirm it by running to that point.

Passes when:

- the function boundaries and stack-frame layout recovered from the binary match the source
- the prediction of register and memory state at the chosen instruction is confirmed by the debugger
- the learner explains the calling convention the binary uses, with evidence from the disassembly
- the write-up maps at least one source-level construct to the exact instructions it compiled to

# Weave

Reading machine code and process memory underlies every memory-safety bug, every exploitation concept and all reverse-engineering work.
