---
id: gate.cs.operating-systems
title: Operating System
track: gate-cs
group: core
tags: [gate]
aliases: [os, operating systems]
paper: CS
marks: 8
marks_source: prior
source_url: "https://gate2027.iitm.ac.in/static/doc/GATE2027_Syllabus/CS_GATE2027_Syllabus.pdf"
est_hours: 60
syllabus_year: 2027
order: 70
summary: "Processes and threads, synchronization and deadlock, scheduling, memory and file systems."
---

Topics follow section 8 of the official GATE 2027 syllabus for Computer Science and Information Technology (read 2026-10-11). If the official document and this file ever differ, the official document wins: write the corrected list to `learner/syllabus/gate.cs.operating-systems.md` and it replaces this one. The marks figure is a planning prior, not an official number; replace it with `gate weight` or `gate weights --apply`.

# Topics

## system-calls | System calls
level: 2
- user and kernel mode; what a system call does; count processes created by fork code

## processes | Processes
level: 2
- process states and the process control block; context switches

## threads | Threads
level: 2
- what threads of a process share; user-level versus kernel-level threads

## ipc | Inter-process communication
level: 2
- pipes, shared memory and message passing

## concurrency-synchronization | Concurrency and synchronization
level: 3
- critical sections; mutual exclusion, progress, bounded waiting; semaphores and monitors
- the classic problems: producer-consumer, readers-writers, dining philosophers

## deadlock | Deadlock
level: 3
- the four necessary conditions; resource-allocation graphs; prevention, avoidance (Banker's algorithm), detection

## cpu-scheduling | CPU scheduling
level: 2
- FCFS, SJF and SRTF, priority, round robin; waiting, turnaround and response times from a Gantt chart

## io-scheduling | I/O scheduling
level: 2
- disk scheduling policies and total head movement

## memory-management | Memory management
level: 3
- paging and segmentation; address translation; page-table size; multi-level paging; TLB access time

## virtual-memory | Virtual memory
level: 3
- demand paging; page-replacement policies and fault counts; Belady's anomaly; thrashing

## file-systems | File systems
level: 2
- allocation methods; inodes and maximum file size; directories; free-space management
