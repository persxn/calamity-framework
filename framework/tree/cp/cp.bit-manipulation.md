---
id: cp.bit-manipulation
title: Bit manipulation
track: cp
group: foundations
prereqs: [cp.math-basics]
tags: [cp]
weaves_into: [cp]
aliases: [bitmasks, xor, bits]
cf_tags: [bitmasks]
band: 1100
est_hours: 15
order: 90
summary: "Bits as a data structure: masks, XOR algebra, and solving one bit at a time."
---

`band` is the Codeforces rating from which this skill is expected; a topic's own `band` marks a part that belongs to a later rating. Practice problems come from `cf recommend --skill cp.bit-manipulation`.

# Boss

A timed set under contest conditions: 5 Codeforces problems the learner has never opened, tagged `bitmasks`, rated 1200 to 1500, in one sitting of 120 minutes. No editorial, no tags shown, no help.

Passes when:

- after `cf sync`, at least 4 of the 5 show an accepted verdict submitted inside the sitting
- each accepted solution is explained in two sentences: the idea and its complexity
- every problem left unsolved is upsolved within three days (`cf upsolve`)

# Topics

## bit-operations | Bit operations
level: 1
- and, or, xor, not, shifts; test, set and clear bit k; use `1LL << k` beyond 31

## xor-properties | XOR properties
needs: [bit-operations]
level: 2
- x ^ x = 0, so equal pairs cancel; prefix xor gives range xor
- a + b = (a ^ b) + 2 * (a & b)

## bit-by-bit | Solving bit by bit
needs: [xor-properties]
level: 3
- treat each bit independently; count each bit's contribution to a sum
- decide bits greedily from the highest down

## subsets-as-masks | Subsets as masks
needs: [bit-operations]
level: 3
- loop over all 2^n masks; loop over the submasks of a mask; all (mask, submask) pairs cost 3^n

## and-or-segments | AND, OR and gcd over growing segments
needs: [bit-by-bit]
level: 4
band: 1700
- extending a segment changes its AND, OR or gcd at most about log(max value) times
