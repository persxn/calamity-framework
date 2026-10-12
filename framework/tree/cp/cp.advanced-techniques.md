---
id: cp.advanced-techniques
title: Advanced techniques
track: cp
group: advanced
prereqs: [cp.range-queries, cp.trees, cp.dp-advanced]
tags: [cp]
weaves_into: [cp]
aliases: [meet in the middle, small to large, centroid, hld]
cf_tags: [divide and conquer, meet-in-the-middle]
band: 2000
est_hours: 40
order: 70
summary: "The techniques that separate 1900 from 2200: meet in the middle, small-to-large, decompositions, bitsets."
---

`band` is the Codeforces rating from which this skill is expected; a topic's own `band` marks a part that belongs to a later rating. Practice problems come from `cf recommend --skill cp.advanced-techniques`.

# Boss

A timed set under contest conditions: 5 Codeforces problems the learner has never opened, tagged `divide and conquer` or `meet-in-the-middle`, rated 1900 to 2200, in one sitting of 120 minutes. No editorial, no tags shown, no help.

Passes when:

- after `cf sync`, at least 4 of the 5 show an accepted verdict submitted inside the sitting
- each accepted solution is explained in two sentences: the idea and its complexity
- every problem left unsolved is upsolved within three days (`cf upsolve`)

# Topics

## meet-in-the-middle | Meet in the middle
level: 4
band: 1800
- split n up to about 40 into two halves, enumerate each, combine with sorting or a map

## jump-pointers | Binary lifting beyond LCA
level: 4
band: 1800
- the 2^k-th successor in a functional graph; binary search over jumps

## divide-and-conquer | Divide and conquer on arrays
level: 4
- count pairs across the midpoint; merge-sort style counting

## bitset-optimisation | Bitset speed-ups
level: 4
- subset-sum reachability and transitive closure 64 times faster

## small-to-large | Small-to-large merging
level: 4
- merge children's containers into the largest one: O(n log n) insertions in total

## randomisation | Randomised techniques
level: 4
- give each value a random 64-bit number and compare sets by xor or sum of the numbers

## centroid-decomposition | Centroid decomposition
needs: [small-to-large]
level: 5
band: 2100
- count or optimise over all paths by splitting at centroids: O(log n) levels, O(n log n) work in total

## heavy-light | Heavy-light decomposition
needs: [small-to-large]
level: 5
band: 2100
- any path crosses O(log n) heavy chains; path updates and queries with one segment tree
