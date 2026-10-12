---
id: cp.graphs-advanced
title: "Graphs: advanced"
track: cp
group: advanced
prereqs: [cp.shortest-paths-mst, cp.trees]
tags: [cp]
weaves_into: [cp]
aliases: [scc, bridges, 2-sat, max flow, matching]
cf_tags: [graphs, flows, graph matchings, 2-sat]
band: 1800
est_hours: 40
order: 50
summary: "Strong components, bridges, 2-SAT, Euler tours, matchings and flows."
---

`band` is the Codeforces rating from which this skill is expected; a topic's own `band` marks a part that belongs to a later rating. Practice problems come from `cf recommend --skill cp.graphs-advanced`.

# Boss

A timed set under contest conditions: 5 Codeforces problems the learner has never opened, tagged `graphs` or `flows`, rated 1800 to 2100, in one sitting of 120 minutes. No editorial, no tags shown, no help.

Passes when:

- after `cf sync`, at least 4 of the 5 show an accepted verdict submitted inside the sitting
- each accepted solution is explained in two sentences: the idea and its complexity
- every problem left unsolved is upsolved within three days (`cf upsolve`)

# Topics

## scc | Strongly connected components
level: 4
- Tarjan or Kosaraju in O(n + m); the condensation is a DAG, so DP over it

## bridges-articulation | Bridges and articulation points
level: 4
- low-link values from one DFS; two-edge-connected components

## dag-techniques | Working on DAGs
level: 3
- count paths, longest path and reachability by DP in topological order

## shortest-path-structure | The structure of shortest paths
level: 4
- count shortest paths; the DAG of edges that lie on some shortest path

## two-sat | 2-SAT
needs: [scc]
level: 4
band: 2000
- one vertex per literal, an implication per clause; satisfiable exactly when no variable shares a component with its negation

## euler-paths | Eulerian paths and circuits
level: 4
band: 1900
- the degree conditions; Hierholzer's algorithm

## bipartite-matching | Bipartite matching
level: 5
band: 2000
- Kuhn's augmenting paths; vertex cover and independent set through König's theorem

## max-flow | Maximum flow and minimum cut
needs: [bipartite-matching]
level: 5
band: 2100
- Dinic's algorithm; modelling with capacities; reading a minimum cut off the residual graph
