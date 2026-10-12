---
id: cp.combinatorics
title: Combinatorics and probability
track: cp
group: core
prereqs: [cp.number-theory]
tags: [cp]
weaves_into: [cp]
aliases: [combinatorics, counting, ncr, expected value, probability]
cf_tags: [combinatorics, probabilities]
band: 1300
est_hours: 25
order: 20
summary: "Count without enumerating: binomials under a modulus, inclusion-exclusion, contributions, expected values."
---

`band` is the Codeforces rating from which this skill is expected; a topic's own `band` marks a part that belongs to a later rating. Practice problems come from `cf recommend --skill cp.combinatorics`.

# Boss

A timed set under contest conditions: 5 Codeforces problems the learner has never opened, tagged `combinatorics` or `probabilities`, rated 1400 to 1700, in one sitting of 120 minutes. No editorial, no tags shown, no help.

Passes when:

- after `cf sync`, at least 4 of the 5 show an accepted verdict submitted inside the sitting
- each accepted solution is explained in two sentences: the idea and its complexity
- every problem left unsolved is upsolved within three days (`cf upsolve`)

# Topics

## counting-rules | Counting rules
level: 2
- sum and product rules; permutations and combinations; counting the complement

## ncr-mod-p | Binomial coefficients modulo a prime
needs: [counting-rules]
level: 2
- precompute factorials and inverse factorials in O(n); answer nCr in O(1)
- return 0 when r is out of range

## stars-and-bars | Stars and bars
needs: [ncr-mod-p]
level: 2
- ways to split n identical items into k groups, with and without empty groups

## contribution | Counting by contribution
needs: [counting-rules]
level: 3
- sum over all subsets or pairs by asking how many times each element or pair is counted

## inclusion-exclusion | Inclusion-exclusion
needs: [ncr-mod-p]
level: 3
- count objects with none of several bad properties; alternate signs over subsets of properties

## expected-value | Probability and expected value
needs: [contribution]
level: 3
band: 1600
- linearity of expectation; indicator variables
- print p/q under a modulus as p times the inverse of q

## catalan | Catalan numbers
needs: [ncr-mod-p]
level: 4
band: 1700
- balanced sequences, triangulations, monotone paths; the reflection argument
