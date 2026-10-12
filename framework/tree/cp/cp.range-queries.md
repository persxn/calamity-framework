---
id: cp.range-queries
title: Range queries and data structures
track: cp
group: advanced
prereqs: [cp.prefix-sums-two-pointers, cp.binary-search]
tags: [cp]
weaves_into: [cp]
aliases: [segment tree, fenwick, bit, sparse table, data structures, "mo's algorithm"]
cf_tags: [data structures]
band: 1600
est_hours: 40
order: 10
summary: "Monotonic stacks, sparse tables, Fenwick and segment trees, and when to answer offline."
---

`band` is the Codeforces rating from which this skill is expected; a topic's own `band` marks a part that belongs to a later rating. Practice problems come from `cf recommend --skill cp.range-queries`.

# Boss

A timed set under contest conditions: 5 Codeforces problems the learner has never opened, tagged `data structures`, rated 1700 to 2000, in one sitting of 120 minutes. No editorial, no tags shown, no help.

Passes when:

- after `cf sync`, at least 4 of the 5 show an accepted verdict submitted inside the sitting
- each accepted solution is explained in two sentences: the idea and its complexity
- every problem left unsolved is upsolved within three days (`cf upsolve`)

# Topics

## monotonic-stack | Monotonic stack
level: 3
band: 1400
- next greater or smaller element for every position in O(n); largest rectangle in a histogram

## monotonic-queue | Monotonic queue
needs: [monotonic-stack]
level: 3
- minimum or maximum of every window of length k in O(n)

## sparse-table | Sparse table
level: 3
- O(1) queries for min, max or gcd on an array that never changes; O(n log n) to build

## coordinate-compression | Coordinate compression
level: 2
- map large values to ranks with sort, unique and `lower_bound`

## fenwick | Fenwick tree
needs: [coordinate-compression]
level: 3
- point update and prefix sum in O(log n); count inversions; range update with a difference tree

## segment-tree | Segment tree
needs: [fenwick]
level: 3
- build, point update and range query for any associative operation; what the identity element is

## lazy-propagation | Lazy propagation
needs: [segment-tree]
level: 4
band: 1800
- range update with range query; how two pending updates compose, and in which order

## tree-descent | Searching inside a segment tree
needs: [segment-tree]
level: 4
band: 1900
- find the first position where a prefix condition holds by walking down the tree

## offline-sweep | Offline queries and sweeps
needs: [fenwick]
level: 4
band: 1800
- sort the queries, sweep one coordinate and keep the other in a Fenwick tree

## sqrt-decomposition | Sqrt decomposition and Mo's algorithm
needs: [offline-sweep]
level: 4
band: 1900
- blocks of size about sqrt n; order queries so the window moves O((n + q) sqrt n) in total
