---
id: cp.binary-search
title: Binary search
track: cp
group: foundations
prereqs: [cp.stl, cp.complexity]
tags: [cp]
weaves_into: [cp]
aliases: [binary search, bsearch, binary search on answer]
cf_tags: [binary search, ternary search]
band: 1100
est_hours: 18
order: 70
summary: "Search a sorted array without bugs, then search the answer itself."
---

`band` is the Codeforces rating from which this skill is expected; a topic's own `band` marks a part that belongs to a later rating. Practice problems come from `cf recommend --skill cp.binary-search`.

# Boss

A timed set under contest conditions: 5 Codeforces problems the learner has never opened, tagged `binary search` or `ternary search`, rated 1200 to 1500, in one sitting of 120 minutes. No editorial, no tags shown, no help.

Passes when:

- after `cf sync`, at least 4 of the 5 show an accepted verdict submitted inside the sitting
- each accepted solution is explained in two sentences: the idea and its complexity
- every problem left unsolved is upsolved within three days (`cf upsolve`)

# Topics

## on-sorted-array | Binary search on a sorted array
level: 1
- keep an invariant: `lo` always fails the test and `hi` always passes; stop when they are adjacent
- find the first position `>= x` by hand and with `lower_bound`

## on-answer | Binary search on the answer
needs: [on-sorted-array]
level: 2
- when "can we do it with x?" flips from no to yes exactly once, search for the flip
- minimise the maximum, maximise the minimum; choose bounds that certainly fail and certainly pass

## predicate-design | Writing the check
needs: [on-answer, cp.sorting-greedy/sort-then-scan]
level: 3
- a greedy feasibility check in O(n); total cost O(n log range)

## real-valued | Binary search on real numbers
needs: [on-answer]
level: 3
- run a fixed number of iterations instead of looping until an epsilon

## ternary-search | Ternary search
needs: [real-valued]
level: 3
band: 1600
- find the extremum of a unimodal function; the integer version; when it silently fails on plateaus
