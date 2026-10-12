---
id: cp.game-theory
title: Game theory
track: cp
group: advanced
prereqs: [cp.dp-basics, cp.bit-manipulation]
tags: [cp]
weaves_into: [cp]
aliases: [games, nim, grundy]
cf_tags: [games]
band: 1700
est_hours: 12
order: 40
summary: Decide who wins a two-player game with perfect play.
---

`band` is the Codeforces rating from which this skill is expected; a topic's own `band` marks a part that belongs to a later rating. Practice problems come from `cf recommend --skill cp.game-theory`.

# Boss

A timed set under contest conditions: 5 Codeforces problems the learner has never opened, tagged `games`, rated 1800 to 2100, in one sitting of 120 minutes. No editorial, no tags shown, no help.

Passes when:

- after `cf sync`, at least 4 of the 5 show an accepted verdict submitted inside the sitting
- each accepted solution is explained in two sentences: the idea and its complexity
- every problem left unsolved is upsolved within three days (`cf upsolve`)

# Topics

## win-lose-states | Winning and losing positions
level: 3
- a position is winning when some move leads to a losing one; compute it backwards

## strategy-arguments | Symmetry and parity strategies
needs: [win-lose-states]
level: 3
- mirror the opponent; count moves; find the pattern with a brute force over small positions

## nim | Nim
needs: [win-lose-states]
level: 3
- the first player wins exactly when the xor of the pile sizes is non-zero, and why

## sprague-grundy | Sprague-Grundy numbers
needs: [nim]
level: 4
band: 1900
- the mex of the reachable values; independent games combine by xor
