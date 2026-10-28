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

The analysis ends with the program's measures, by the problems' rating
band: solves, the median time to an accepted submission (from the contest's
start, or from `cf assign`, where known), wrong submissions before it, and
the share solved after an editorial (`cf mark <problem> editorial`). On an
untagged set the learner names the technique before solving, and the tutor
records whether it was right: `cf mark <problem> recognized|missed`. The
recognition line is that share.

## The program

A training plan and a pace check, not a promise: rating gains vary widely.
The USACO Guide is the backbone, with CSES and Codeforces; the doctrine's
six practice stages and 25-minute rule hold throughout. While GATE comes
first the program runs at the learner's CP hours; full intensity fits from
late February 2027 (decision D7 kept the target at the profile's
`cp.target_rating` by `cp.target_date`).

| Phase | Focus | Weekly volume | Moves on when |
|---|---|---|---|
| 1 (weeks 1-4) | placement; C++ and STL just in time; implementation speed; ad-hoc and maths basics | 30-40 problems at 800-1100; 1-2 virtual Div. 3/4 | median time to AC on 1000-rated problems is 20 minutes or less |
| 2 (weeks 5-12) | sorting and greedy, prefix sums and two pointers, binary search, number theory basics, constructive, bits | 25 in the band (rating +100 to +300); 2 contests; upsolve to performance +300 | 60% or more of the band solved without an editorial |
| 3 (weeks 13-24) | graphs (BFS/DFS, shortest paths, DSU, trees), DP basics to intermediate, combinatorics; untagged recognition sets | 25 in the band; 2 contests; a weekly recognition set | performance 1500 or more in 3 of the last 5 contests |
| 4 (weeks 25-34) | advanced DP, segment tree and BIT, strings, game theory basics; contest craft (A-C under 45 minutes) | 20 in the band plus speed drills; 2 contests | a performance trend of 1650 or more; then hold |

- **Every week:** 4 practice days, 2 contests (live or virtual), 1 review
  day (upsolving and the re-solve queue), 1 rest day.
- **Outside Codeforces:** CSES, USACO and AtCoder problem sets are practice
  sets (`practice add cses --kind cses --items 300 --key none`, then
  `practice map`), numbered by their place in the judge's list. They count
  as volume and recognition practice; they schedule topics but are not
  rating evidence.
- **The monthly checkpoint:** the expected rating on the straight line from
  the plan's start to the target against the actual. Six weeks more than
  100 points behind: replan with the learner (load, band, phase or date).
  The phase's exit test, not the calendar, moves it on.

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
