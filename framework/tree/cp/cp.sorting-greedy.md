---
id: cp.sorting-greedy
title: Sorting and greedy
track: cp
group: foundations
prereqs: [cp.stl, cp.complexity]
tags: [cp]
weaves_into: [cp]
aliases: [greedy, sorting, sortings]
cf_tags: [greedy, sortings]
band: 900
est_hours: 25
order: 40
summary: "Sort first, then take the locally best choice, and know how to prove or break it."
---

`band` is the Codeforces rating from which this skill is expected; a topic's own `band` marks a part that belongs to a later rating. Practice problems come from `cf recommend --skill cp.sorting-greedy`.

# Boss

A timed set under contest conditions: 5 Codeforces problems the learner has never opened, tagged `greedy` or `sortings`, rated 1000 to 1300, in one sitting of 120 minutes. No editorial, no tags shown, no help.

Passes when:

- after `cf sync`, at least 4 of the 5 show an accepted verdict submitted inside the sitting
- each accepted solution is explained in two sentences: the idea and its complexity
- every problem left unsolved is upsolved within three days (`cf upsolve`)

# Topics

## sort-then-scan | Sort, then scan
level: 1
- sorting as the first move: neighbours, extremes, pairing smallest with largest, grouping equals

## custom-order | Sorting by the right key
needs: [sort-then-scan]
level: 2
- sort by end time, by a pair, or by a ratio compared with cross-multiplication instead of doubles

## exchange-argument | Why a greedy choice is safe
needs: [custom-order]
level: 3
- prove a greedy order by swapping two adjacent elements and showing the result is no worse
- the stays-ahead argument for step-by-step choices

## intervals | Interval problems
needs: [custom-order]
level: 2
- pick the most non-overlapping intervals by right end; merge intervals; count overlaps with a sweep

## counterexamples | Breaking a wrong greedy
needs: [exchange-argument]
level: 3
- hunt a counterexample by hand on tiny inputs, then by brute force on random ones

## greedy-with-heap | Greedy with a priority queue
needs: [exchange-argument]
level: 4
band: 1600
- keep the best available option in a heap; take back an earlier choice when a better one appears
