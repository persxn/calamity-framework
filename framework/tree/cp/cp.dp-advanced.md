---
id: cp.dp-advanced
title: "Dynamic programming: advanced"
track: cp
group: advanced
prereqs: [cp.dp-basics, cp.bit-manipulation, cp.trees]
tags: [cp]
weaves_into: [cp]
aliases: [bitmask dp, digit dp, tree dp, interval dp, sos dp]
cf_tags: [dp, bitmasks]
band: 1700
est_hours: 45
order: 20
summary: "DP over subsets, digits, trees and intervals, and the standard ways to speed a transition up."
---

`band` is the Codeforces rating from which this skill is expected; a topic's own `band` marks a part that belongs to a later rating. Practice problems come from `cf recommend --skill cp.dp-advanced`.

# Boss

A timed set under contest conditions: 5 Codeforces problems the learner has never opened, tagged `dp` or `bitmasks`, rated 1800 to 2100, in one sitting of 120 minutes. No editorial, no tags shown, no help.

Passes when:

- after `cf sync`, at least 4 of the 5 show an accepted verdict submitted inside the sitting
- each accepted solution is explained in two sentences: the idea and its complexity
- every problem left unsolved is upsolved within three days (`cf upsolve`)

# Topics

## bitmask-dp | Bitmask DP
level: 3
- a state per subset for n up to about 20; visiting-order problems in O(2^n * n^2)

## digit-dp | Digit DP
level: 3
- count numbers up to N with a digit property: position, tight flag, started flag, extra state

## tree-dp | DP on trees
level: 3
- states per vertex combined over children; why merging child tables by size is O(n^2) in total

## interval-dp | Interval DP
level: 4
- dp[l][r] built by increasing length in O(n^3); choosing the last operation instead of the first

## monotonic-optimisation | Window transitions with a monotonic queue
level: 4
- a transition that takes the best of the last k states in O(1) amortised

## dp-with-structures | Transitions through a data structure
level: 4
band: 1900
- best earlier state over a range of keys with a Fenwick or segment tree

## probability-dp | DP over probabilities and expectations
level: 4
band: 1900
- set up the equation for an expected value; solve it when the state refers to itself

## sos-dp | Sum over subsets
needs: [bitmask-dp]
level: 5
band: 2000
- for every mask, the sum over its submasks in O(2^n * n)

## convex-hull-trick | Convex hull trick and divide-and-conquer optimisation
needs: [monotonic-optimisation]
level: 5
band: 2100
- transitions of the form min over j of (m_j * x_i + c_j); when the optimal split point is monotone
