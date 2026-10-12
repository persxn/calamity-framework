---
id: cp.graphs-basics
title: "Graphs: traversal"
track: cp
group: core
prereqs: [cp.stl, cp.complexity]
tags: [cp]
weaves_into: [cp]
aliases: [graphs, bfs, dfs, topological sort]
cf_tags: [graphs, dfs and similar]
band: 1200
est_hours: 30
order: 30
summary: "Represent a graph and answer reachability, shortest unweighted paths, components, cycles and order."
---

`band` is the Codeforces rating from which this skill is expected; a topic's own `band` marks a part that belongs to a later rating. Practice problems come from `cf recommend --skill cp.graphs-basics`.

# Boss

A timed set under contest conditions: 5 Codeforces problems the learner has never opened, tagged `graphs` or `dfs and similar`, rated 1300 to 1600, in one sitting of 120 minutes. No editorial, no tags shown, no help.

Passes when:

- after `cf sync`, at least 4 of the 5 show an accepted verdict submitted inside the sitting
- each accepted solution is explained in two sentences: the idea and its complexity
- every problem left unsolved is upsolved within three days (`cf upsolve`)

# Topics

## representation | Representing a graph
level: 1
- adjacency lists from an edge list; directed versus undirected; 1-indexed vertices

## dfs | Depth-first search
needs: [representation]
level: 2
- recursive DFS with a visited array; what the recursion tree looks like
- very deep recursion can overflow the stack on some judges: know the iterative form

## bfs | Breadth-first search
needs: [representation]
level: 2
- shortest paths in an unweighted graph; BFS from several sources at once

## components | Connected components
needs: [dfs]
level: 2
- count and label components; sizes of components

## grid-graphs | Grids as graphs
needs: [bfs]
level: 2
- flood fill and shortest paths on a grid without building an explicit graph

## bipartite | Bipartite graphs
needs: [bfs]
level: 2
- two-colour by BFS or DFS; a graph is bipartite exactly when it has no odd cycle

## cycle-detection | Cycle detection
needs: [dfs]
level: 3
- undirected: an edge to a visited vertex that is not the parent; directed: an edge to a vertex on the stack

## topological-sort | Topological sort and DAGs
needs: [cycle-detection]
level: 3
- Kahn's algorithm with in-degrees; DFS finishing order; longest path by DP over the order

## functional-graphs | Functional graphs
needs: [cycle-detection]
level: 3
band: 1500
- every vertex has one outgoing edge: each component is a cycle with trees hanging into it
