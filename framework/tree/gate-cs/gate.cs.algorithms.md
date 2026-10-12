---
id: gate.cs.algorithms
title: Algorithms
track: gate-cs
group: core
tags: [gate]
aliases: [algorithms, algo, daa]
overlaps: [gate.da.programming-dsa]
paper: CS
marks: 8
marks_source: prior
source_url: "https://gate2027.iitm.ac.in/static/doc/GATE2027_Syllabus/CS_GATE2027_Syllabus.pdf"
est_hours: 60
syllabus_year: 2027
order: 40
summary: "Searching, sorting, hashing, asymptotic analysis, design techniques and graph algorithms."
---

Topics follow section 5 of the official GATE 2027 syllabus for Computer Science and Information Technology (read 2026-10-11). If the official document and this file ever differ, the official document wins: write the corrected list to `learner/syllabus/gate.cs.algorithms.md` and it replaces this one. The marks figure is a planning prior, not an official number; replace it with `gate weight` or `gate weights --apply`.

# Topics

## searching | Searching
level: 2
same_as: [gate.da.programming-dsa/searching]
- linear and binary search; number of comparisons

## sorting | Sorting
level: 2
- the standard sorts with best, average and worst cases; stability; in-place or not
- the comparison lower bound

## hashing | Hashing
level: 2
same_as: [gate.da.programming-dsa/hash-tables]
- chaining and open addressing; linear and quadratic probing; load factor and expected probes

## asymptotic-analysis | Asymptotic worst-case time and space complexity
level: 2
- O, Omega and Theta; order functions by growth; analyse loops; solve recurrences (Master theorem)

## greedy | Algorithm design: greedy
level: 2
- activity selection, Huffman codes, fractional knapsack; when a greedy choice is optimal

## dynamic-programming | Algorithm design: dynamic programming
level: 3
- optimal substructure and overlapping subproblems; LCS, matrix-chain multiplication, 0/1 knapsack

## divide-and-conquer | Algorithm design: divide and conquer
level: 2
same_as: [gate.da.programming-dsa/divide-and-conquer]
- merge sort, quick sort, binary search and their recurrences

## graph-traversals | Graph traversals
level: 2
same_as: [gate.da.programming-dsa/graph-traversals]
- BFS and DFS; edge types; topological order; connected and strongly connected components

## minimum-spanning-trees | Minimum spanning trees
level: 2
- Kruskal and Prim; cut and cycle properties; when the tree is unique

## shortest-paths | Shortest paths
level: 2
same_as: [gate.da.programming-dsa/shortest-path]
- Dijkstra, Bellman-Ford and Floyd-Warshall; negative edges and cycles
