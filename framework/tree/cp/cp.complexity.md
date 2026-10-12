---
id: cp.complexity
title: Complexity and reading constraints
track: cp
group: foundations
prereqs: [cp.cpp]
tags: [cp]
weaves_into: [cp]
aliases: [big o, time complexity, constraints]
band: 800
est_hours: 8
order: 10
summary: "Decide whether an idea is fast enough before writing it, straight from the constraints."
---

`band` is the Codeforces rating from which this skill is expected; a topic's own `band` marks a part that belongs to a later rating. Practice problems come from `cf recommend --skill cp.complexity`.

# Boss

For 12 statements the coach picks, shown with constraints only, name the complexity that fits and an algorithm family, before seeing any solution.

Passes when:

- at least 10 of 12 match the intended complexity
- each answer gives an operation count, not only a big-O label

# Weave

Every later solution states its complexity against the constraints before any code is written.

# Topics

## big-o | Counting operations
level: 1
- count the work of simple and nested loops; logarithms from halving; `sort` is n log n
- amortised costs: a pointer that only moves forward does O(n) work in total

## constraints-to-algorithm | From constraints to an algorithm class
needs: [big-o]
level: 1
- budget about 1e8 simple operations a second
- n up to 20 allows 2^n; 500 allows n^3; 5000 allows n^2; 2e5 needs n log n; 1e18 needs log n or a formula
- check the line about the sum of n over all test cases

## memory | Memory limits
needs: [big-o]
level: 2
- an `int` is 4 bytes and a `long long` 8: 1e6 ints is 4 MB, a 5000 x 5000 int table is 100 MB
- deep recursion uses stack memory

## harmonic-amortised | Sums that look slow and are not
needs: [constraints-to-algorithm]
level: 3
band: 1300
- looping over all multiples of every i up to n is n/1 + n/2 + ... = O(n log n)
- merging the smaller set into the larger moves each element O(log n) times
