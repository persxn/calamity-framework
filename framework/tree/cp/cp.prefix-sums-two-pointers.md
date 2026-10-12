---
id: cp.prefix-sums-two-pointers
title: Prefix sums and two pointers
track: cp
group: foundations
prereqs: [cp.stl, cp.complexity]
tags: [cp]
weaves_into: [cp]
aliases: [prefix sums, two pointers, sliding window, difference array]
cf_tags: [two pointers]
band: 1000
est_hours: 18
order: 60
summary: Answer range questions in O(1) and scan with two indices instead of two loops.
---

`band` is the Codeforces rating from which this skill is expected; a topic's own `band` marks a part that belongs to a later rating. Practice problems come from `cf recommend --skill cp.prefix-sums-two-pointers`.

# Boss

A timed set under contest conditions: 5 Codeforces problems the learner has never opened, rated 1100 to 1400, each solvable with prefix sums, difference arrays or two pointers (the coach picks them from `two pointers` and prefix-sum problems), in one sitting of 120 minutes.

Passes when:

- after `cf sync`, at least 4 of the 5 show an accepted verdict submitted inside the sitting
- each accepted solution is explained in two sentences: the idea and its complexity
- every problem left unsolved is upsolved within three days (`cf upsolve`)

# Topics

## prefix-sums | Prefix sums
level: 1
- range sum as a difference of two prefix values; keep the array 1-indexed to avoid special cases
- count subarrays with a given sum using a map of earlier prefix values

## difference-arrays | Difference arrays
needs: [prefix-sums]
level: 2
- add a value to a whole range in O(1), then rebuild the array with one prefix pass

## prefix-2d | Two-dimensional prefix sums
needs: [prefix-sums]
level: 3
- rectangle sums by inclusion-exclusion of four corners

## prefix-other | Prefix and suffix aggregates
needs: [prefix-sums]
level: 2
- prefix minimum, maximum, xor and gcd; combine a prefix with a suffix to remove one element

## two-pointers | Two pointers
needs: [prefix-sums]
level: 2
- from both ends of a sorted array; or two indices moving the same way while a condition stays monotone

## sliding-window | Sliding window
needs: [two-pointers]
level: 3
- a window that grows and shrinks while keeping counts; what must be monotone for it to be valid
