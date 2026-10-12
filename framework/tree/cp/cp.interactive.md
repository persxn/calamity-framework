---
id: cp.interactive
title: Interactive problems
track: cp
group: core
prereqs: [cp.binary-search]
tags: [cp]
weaves_into: [cp]
aliases: [interactive]
cf_tags: [interactive]
band: 1500
est_hours: 6
order: 80
summary: "Talk to the judge: flush, respect the query budget, and reason about an adaptive opponent."
---

`band` is the Codeforces rating from which this skill is expected; a topic's own `band` marks a part that belongs to a later rating. Practice problems come from `cf recommend --skill cp.interactive`.

# Boss

A timed set under contest conditions: 5 Codeforces problems the learner has never opened, tagged `interactive`, rated 1600 to 1900, in one sitting of 120 minutes. No editorial, no tags shown, no help.

Passes when:

- after `cf sync`, at least 4 of the 5 show an accepted verdict submitted inside the sitting
- each accepted solution is explained in two sentences: the idea and its complexity
- every problem left unsolved is upsolved within three days (`cf upsolve`)

# Topics

## protocol | The protocol
level: 2
- print a query, flush (`endl` or `cout.flush()`), read the reply; stop at once on an invalid reply

## query-budget | Query budgets
needs: [protocol]
level: 3
- a budget near log2(n) asks for binary search; count what each query can rule out

## adaptive-judges | Adaptive judges
needs: [query-budget]
level: 4
- the judge may decide its answers as you go: reason about the worst consistent reply

## local-interactor | Testing locally
needs: [protocol]
level: 2
- write a small interactor or play the judge by hand before submitting
