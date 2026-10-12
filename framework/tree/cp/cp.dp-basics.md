---
id: cp.dp-basics
title: "Dynamic programming: foundations"
track: cp
group: core
prereqs: [cp.complexity, cp.implementation]
tags: [cp]
weaves_into: [cp]
aliases: [dp, dynamic programming, knapsack, lis]
cf_tags: [dp]
band: 1200
est_hours: 35
order: 40
summary: "State, transition, base case, order: the classic one- and two-dimensional DPs done by method, not memory."
---

`band` is the Codeforces rating from which this skill is expected; a topic's own `band` marks a part that belongs to a later rating. Practice problems come from `cf recommend --skill cp.dp-basics`.

# Boss

A timed set under contest conditions: 5 Codeforces problems the learner has never opened, tagged `dp`, rated 1300 to 1600, in one sitting of 120 minutes. No editorial, no tags shown, no help.

Passes when:

- after `cf sync`, at least 4 of the 5 show an accepted verdict submitted inside the sitting
- each accepted solution is explained in two sentences: the idea and its complexity
- every problem left unsolved is upsolved within three days (`cf upsolve`)

# Topics

## states-transitions | The method
level: 2
- name the state in words, write the transition, the base cases, the order of evaluation and the answer
- memoised recursion and the bottom-up table are the same DP

## linear-dp | One-dimensional DP
needs: [states-transitions]
level: 2
- best/count ending at position i; maximum subarray; take-or-skip choices

## grid-dp | Grid DP
needs: [states-transitions]
level: 2
- paths in a grid with obstacles; best path sum

## knapsack-01 | 0/1 knapsack
needs: [linear-dp]
level: 3
- dp over capacity in O(n * W); in the one-dimensional table iterate capacity downwards

## knapsack-unbounded | Unbounded knapsack and coin problems
needs: [knapsack-01]
level: 3
- fewest coins; number of ways; which loop order counts combinations and which counts orderings

## lis | Longest increasing subsequence
needs: [linear-dp]
level: 3
- O(n^2) DP, then O(n log n) with `lower_bound` on the tails array

## lcs-edit-distance | LCS and edit distance
needs: [grid-dp]
level: 3
- two-string DP over prefixes

## counting-dp | Counting under a modulus
needs: [linear-dp]
level: 2
- count ways with a DP; take the remainder at every addition

## reconstruction | Rebuilding the answer
needs: [knapsack-01]
level: 3
- store the choice or walk the table backwards to print one optimal solution

## state-design | Designing the state
needs: [knapsack-01, lis]
level: 4
- what must the state remember for the future to be independent of the past; dropping a dimension

## prefix-sum-transitions | Faster transitions with prefix sums
needs: [counting-dp]
level: 4
band: 1500
- a transition that sums a range of earlier states becomes O(1) with a running prefix
