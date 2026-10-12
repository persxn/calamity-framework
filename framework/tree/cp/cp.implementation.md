---
id: cp.implementation
title: Implementation and brute force
track: cp
group: foundations
prereqs: [cp.stl]
tags: [cp]
weaves_into: [cp]
aliases: [simulation, brute force, ad hoc]
cf_tags: [implementation, brute force]
band: 800
est_hours: 20
order: 20
summary: "Turn a statement into correct code quickly: simulation, case analysis, complete search, grids."
---

`band` is the Codeforces rating from which this skill is expected; a topic's own `band` marks a part that belongs to a later rating. Practice problems come from `cf recommend --skill cp.implementation`.

# Boss

A timed set under contest conditions: 5 Codeforces problems the learner has never opened, tagged `implementation` or `brute force`, rated 900 to 1200, in one sitting of 120 minutes. No editorial, no tags shown, no help.

Passes when:

- after `cf sync`, at least 4 of the 5 show an accepted verdict submitted inside the sitting
- each accepted solution is explained in two sentences: the idea and its complexity
- every problem left unsolved is upsolved within three days (`cf upsolve`)

# Weave

Implementation discipline carries into every later topic: plan first, corner cases listed, clean first submit.

# Topics

## simulation | Simulating a process
level: 1
- translate the statement into state variables and one step function; run it exactly as described
- notice when the process is too long to simulate and needs a shortcut

## case-analysis | Case analysis and corner cases
level: 1
- enumerate the cases before coding; test n = 1, all equal, already sorted, maximum values

## complete-search | Complete search
needs: [simulation]
level: 2
- try every candidate, pair or triple when the constraints allow it
- enumerate subsets with bitmasks and orderings with `next_permutation`

## grids | Grids
needs: [simulation]
level: 2
- read a character grid; move with `dx`/`dy` arrays; check bounds in one place

## plan-then-type | Plan, then type
needs: [case-analysis]
level: 2
- write the approach in three lines of comments first; name things; avoid copy-pasted branches

## debugging | Debugging a wrong answer
needs: [complete-search]
level: 3
- reread the statement; build the smallest failing test; trace by hand; check overflow and indexing
- compare against a brute force on random small tests
