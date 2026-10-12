---
id: cp.shortest-paths-mst
title: Shortest paths and spanning trees
track: cp
group: core
prereqs: [cp.graphs-basics, cp.dsu]
tags: [cp]
weaves_into: [cp]
aliases: [dijkstra, shortest paths, mst, minimum spanning tree, kruskal]
cf_tags: [shortest paths]
band: 1500
est_hours: 20
order: 70
summary: "Dijkstra and its relatives, and minimum spanning trees."
---

`band` is the Codeforces rating from which this skill is expected; a topic's own `band` marks a part that belongs to a later rating. Practice problems come from `cf recommend --skill cp.shortest-paths-mst`.

# Boss

A timed set under contest conditions: 5 Codeforces problems the learner has never opened, tagged `shortest paths`, rated 1600 to 1900, in one sitting of 120 minutes. No editorial, no tags shown, no help.

Passes when:

- after `cf sync`, at least 4 of the 5 show an accepted verdict submitted inside the sitting
- each accepted solution is explained in two sentences: the idea and its complexity
- every problem left unsolved is upsolved within three days (`cf upsolve`)

# Topics

## dijkstra | Dijkstra's algorithm
level: 2
- a min-heap of (distance, vertex); skip stale entries; non-negative weights only; `long long` distances

## zero-one-bfs | 0-1 BFS
needs: [dijkstra]
level: 2
- edge weights 0 and 1 with a deque: push front for 0, back for 1

## bellman-ford | Bellman-Ford
needs: [dijkstra]
level: 3
- n - 1 rounds of relaxing every edge; detecting a negative cycle

## floyd-warshall | Floyd-Warshall
needs: [dijkstra]
level: 3
- all pairs in O(n^3) for n up to about 500; the intermediate vertex is the outer loop

## kruskal | Minimum spanning tree: Kruskal
level: 2
- sort edges and join components with a DSU; why the lightest edge across a cut is safe

## prim | Minimum spanning tree: Prim
needs: [kruskal]
level: 3
- grow one tree with a heap; when it beats Kruskal (dense graphs)

## state-graphs | Shortest paths over states
needs: [dijkstra]
level: 4
band: 1700
- make (vertex, extra information) the node: used a coupon, parity of steps, remaining fuel
