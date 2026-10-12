---
id: cp.trees
title: Trees
track: cp
group: core
prereqs: [cp.graphs-basics]
tags: [cp]
weaves_into: [cp]
aliases: [trees, lca, tree dp, binary lifting]
cf_tags: [trees]
band: 1400
est_hours: 25
order: 60
summary: "Root a tree and compute over it: subtree values, diameter, entry and exit times, lowest common ancestors."
---

`band` is the Codeforces rating from which this skill is expected; a topic's own `band` marks a part that belongs to a later rating. Practice problems come from `cf recommend --skill cp.trees`.

# Boss

A timed set under contest conditions: 5 Codeforces problems the learner has never opened, tagged `trees`, rated 1500 to 1800, in one sitting of 120 minutes. No editorial, no tags shown, no help.

Passes when:

- after `cf sync`, at least 4 of the 5 show an accepted verdict submitted inside the sitting
- each accepted solution is explained in two sentences: the idea and its complexity
- every problem left unsolved is upsolved within three days (`cf upsolve`)

# Topics

## rooting | Rooting a tree
level: 2
- parent, depth and subtree size from one DFS

## subtree-dp | Values from children
needs: [rooting]
level: 2
- compute a value for every vertex from its children's values

## diameter | Diameter
needs: [rooting]
level: 2
- two traversals from the farthest vertex; or the two deepest children at every vertex

## euler-tour | Entry and exit times
needs: [rooting]
level: 3
- a subtree is one contiguous range of the DFS order; test "u is an ancestor of v" in O(1)

## lca | Lowest common ancestor by binary lifting
needs: [euler-tour]
level: 3
band: 1600
- jump tables of 2^k-th ancestors; distance between two vertices; the k-th ancestor

## path-sums | Path queries with prefix values
needs: [lca]
level: 4
band: 1700
- a path value as prefix(u) + prefix(v) - 2 * prefix(lca), adjusted for the lca itself
- add a value along a path with differences, then push up with one DFS

## rerooting | Rerooting
needs: [subtree-dp]
level: 4
band: 1800
- answers for every root in O(n) by moving the root across one edge at a time
