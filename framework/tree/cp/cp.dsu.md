---
id: cp.dsu
title: Disjoint set union
track: cp
group: core
prereqs: [cp.graphs-basics]
tags: [cp]
weaves_into: [cp]
aliases: [dsu, union find, disjoint set]
cf_tags: [dsu]
band: 1400
est_hours: 10
order: 50
summary: "Merge sets and ask \"same set?\" in near-constant time."
---

`band` is the Codeforces rating from which this skill is expected; a topic's own `band` marks a part that belongs to a later rating. Practice problems come from `cf recommend --skill cp.dsu`.

# Boss

A timed set under contest conditions: 5 Codeforces problems the learner has never opened, tagged `dsu`, rated 1500 to 1800, in one sitting of 120 minutes. No editorial, no tags shown, no help.

Passes when:

- after `cf sync`, at least 4 of the 5 show an accepted verdict submitted inside the sitting
- each accepted solution is explained in two sentences: the idea and its complexity
- every problem left unsolved is upsolved within three days (`cf upsolve`)

# Topics

## union-find | Union-find
level: 2
- `find` with path compression and union by size; near-constant amortised cost

## components-online | Components while edges arrive
needs: [union-find]
level: 2
- number of components and their sizes after each added edge

## offline-reverse | Deletions in reverse
needs: [components-online]
level: 3
- answer "remove edge" queries by reading them backwards as additions; sort queries by threshold

## extra-data | Data on sets and weighted DSU
needs: [components-online]
level: 4
band: 1800
- keep a minimum, maximum or sum per set; store parity or distance to the root
