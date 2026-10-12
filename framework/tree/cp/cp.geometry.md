---
id: cp.geometry
title: Geometry
track: cp
group: advanced
prereqs: [cp.math-basics, cp.sorting-greedy]
tags: [cp]
weaves_into: [cp]
aliases: [geometry, convex hull, cross product]
cf_tags: [geometry]
band: 1800
optional: true
est_hours: 25
order: 60
summary: "Computational geometry in integers wherever possible: cross products, intersections, areas, hulls."
---

`band` is the Codeforces rating from which this skill is expected; a topic's own `band` marks a part that belongs to a later rating. Practice problems come from `cf recommend --skill cp.geometry`.

# Boss

A timed set under contest conditions: 5 Codeforces problems the learner has never opened, tagged `geometry`, rated 1700 to 2000, in one sitting of 120 minutes. No editorial, no tags shown, no help.

Passes when:

- after `cf sync`, at least 4 of the 5 show an accepted verdict submitted inside the sitting
- each accepted solution is explained in two sentences: the idea and its complexity
- every problem left unsolved is upsolved within three days (`cf upsolve`)

# Topics

## vectors-cross-dot | Vectors, dot and cross products
level: 3
- orientation of three points from the sign of a cross product, in `long long`

## segments-lines | Segments and lines
needs: [vectors-cross-dot]
level: 4
- do two segments intersect; is a point on a segment; a line as ax + by = c

## polygon-area | Polygons
needs: [vectors-cross-dot]
level: 4
- area by the shoelace formula (keep twice the area as an integer); point in polygon; Pick's theorem

## convex-hull | Convex hull
needs: [vectors-cross-dot]
level: 4
- Andrew's monotone chain in O(n log n); handling collinear points

## precision | Precision
level: 3
- stay in integers when you can; compare doubles with an epsilon; prefer cross products to angles

## angular-sweep | Angular sorting and sweeps
needs: [convex-hull]
level: 5
band: 2000
- sort points by angle without `atan2`; sweep a line or a ray across events
