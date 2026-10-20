# Competitive programming: planning

What the learner works on at each level, the shape of a week, how to read
`cf analyse`, and the pace against the target. Read by the `cp-coach`
agent and by the cp skill before planning or analysing. Coaching one
problem or contest is in `framework/rules/cp-playbook.md`.

## What to work on at each level

A guide, not a law: the learner's own analysis overrides it.

| Rating | Practise problems rated | Skills to build | Contests |
|---|---|---|---|
| unrated to 1000 | 800 to 1100 | C++, the STL, complexity, implementation, math basics, contest craft | Div. 4, Div. 3, Educational |
| 1000 to 1200 | 1000 to 1400 | sorting and greedy, strings, prefix sums and two pointers, binary search, constructive | Div. 3, Div. 2 |
| 1200 to 1400 | 1300 to 1600 | bit manipulation, number theory, graph traversal, DP foundations | Div. 2, Educational |
| 1400 to 1600 | 1500 to 1800 | combinatorics, DSU, trees, shortest paths, interactive | Div. 2 |
| 1600 to 1900 | 1700 to 2100 | range queries, advanced DP, game theory, string algorithms, advanced graphs | Div. 2, Div. 1 + Div. 2 |
| 1900 to 2200 and beyond | 2000 to 2400 | advanced techniques, advanced math, geometry, and speed on the early problems | Div. 1, Div. 1 + Div. 2 |

`cf recommend` picks unsolved problems rated about 100 to 300 above the
current rating (the band is rounded outward to hundreds), weighted toward weak tags, and hides the tags: recognising the
technique is part of the practice. `--skill cp.dp-basics` restricts the set
to one skill's tags; `--low` and `--high` move the band.

## The week

Shape the week around these, sized to the learner's hours:

- **Two contests**, live when the calendar allows, virtual otherwise
  (`cf contests` lists both).
- **Upsolving after each**: at least the first problem that was not solved
  (`cf upsolve`).
- **Three or four practice sets** of three to five problems in the band.
- **One or two technique lessons** from the tree, each followed by problems
  on that technique (`cf recommend --skill <skill>`).
- **Re-solves** that have come due (listed by `cf upsolve`).

Set the weekly number of in-band problems from what the learner actually
did in the last thirty days (`cf analyse`), and raise it by a tenth or two
a week. A heroic number that is missed teaches nothing. Write the week into
`learner/cp/plan.md`.

## Reading the analysis

`cf analyse` lists tags weakest first. The weakness score combines three
things: how far the tag's level (the three hardest problems solved in it)
sits below the learner's overall level, how often problems with the tag
were tried and left unsolved, and how little of the tag has been solved
when the tree says it is due at this rating.

- Pick two or three focus tags among those marked "due at this rating".
  The last column names the skill of the tree that teaches each.
- A high `tries` figure is an implementation problem, not a knowledge
  problem: bring in stress testing, sanitizers and the pre-submit routine
  (`cp.contest-craft`, `cp.cpp/undefined-behaviour`).
- Problems attempted in contests and never solved are the first upsolving
  list.
- Use sub-tags to see inside a broad tag: "dp" hides knapsack, bitmask and
  digit DP, and a learner is rarely weak at all of them.

## Pace, and telling the truth about it

`cf rating` shows the gap to the target, the points a month the target
date needs, and the pace of the last ninety days.

- Reaching 1800 in eight to twelve months, and 2200 after that, is a hard
  target that some learners meet and many do not; it depends on the
  starting point, the hours and the consistency. Commit to the process and
  report the pace. Never promise the date.
- A single contest says little. Judge the trend over five or more.
- A new account's displayed rating is still settling during its first six
  rated contests, and the gains in them overstate real progress. Read the
  pace only after those.
- When the pace is short of the target, say so with the two numbers, and
  decide with the learner whether the hours or the date will change.

When the rating has not moved over about eight rated contests, check in
this order:

1. **Is the band right?** Solving under half of the practice problems
   without an editorial means it is too high; over four in five means it is
   too low.
2. **Where does contest time go?** Slow early problems call for timed sets
   of easy problems; a wall at one problem index calls for that level in
   practice.
3. **Have the weak tags changed?** If not, they need lessons, not more
   random problems.
4. **Enough contests?** Fewer than two a week: add virtual ones.
