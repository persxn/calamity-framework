---
id: cp.constructive
title: Constructive problems
track: cp
group: foundations
prereqs: [cp.implementation, cp.math-basics]
tags: [cp]
weaves_into: [cp]
aliases: [constructive, constructive algorithms]
cf_tags: [constructive algorithms]
band: 1000
est_hours: 20
order: 80
summary: "Build an object with the required property, or prove none exists."
---

`band` is the Codeforces rating from which this skill is expected; a topic's own `band` marks a part that belongs to a later rating. Practice problems come from `cf recommend --skill cp.constructive`.

# Boss

A timed set under contest conditions: 5 Codeforces problems the learner has never opened, tagged `constructive algorithms`, rated 1100 to 1400, in one sitting of 120 minutes. No editorial, no tags shown, no help.

Passes when:

- after `cf sync`, at least 4 of the 5 show an accepted verdict submitted inside the sitting
- each accepted solution is explained in two sentences: the idea and its complexity
- every problem left unsolved is upsolved within three days (`cf upsolve`)

# Topics

## small-cases-patterns | Patterns from small cases
level: 1
- solve n = 1..6 by hand or by brute force and read the structure off the answers

## invariants | Invariants and monovariants
needs: [small-cases-patterns]
level: 3
- a quantity an operation never changes proves impossibility; one that always decreases proves termination

## parity-symmetry | Parity, alternation and symmetry
needs: [small-cases-patterns]
level: 2
- constructions that alternate, mirror, or split by odd and even

## permutations-arrays | Building permutations and arrays
needs: [parity-symmetry]
level: 2
- shifts, reversals and swaps of the identity; fix the hard constraint first and fill the rest

## necessary-then-sufficient | From a necessary condition to a construction
needs: [invariants]
level: 3
- find what any solution must satisfy, then show a build whenever it holds; "print any" answers
