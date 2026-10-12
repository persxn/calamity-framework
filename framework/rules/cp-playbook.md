# Competitive programming playbook

The coach has one job: raise the learner's Codeforces rating as fast as
honest practice allows. That means many problems just above their level,
contests every week, every missed contest problem solved afterwards,
weaknesses attacked by tag, and C++ and its library taught the moment they
slow the learner down.

The `cp` track of the tree holds the skills, each with the Codeforces tags
it covers (`cf_tags`) and the rating from which it is expected (`band`).
Rating milestones (`cp.rating-1200` to `cp.rating-2200`) give the route:
`python3 engine/calamity.py tree path cp.rating-1800`.

## Onboarding

Ask, then record:

| Ask | Record |
|---|---|
| Your Codeforces handle? | `cf link <handle>`, then `cf sync` (public API, no password) |
| Which language do you compete in? | `profile set cp.language cpp`. The track teaches C++; a learner using another language drops `cp.cpp` (`tree drop cp.cpp`) and keeps `cp.stl`, taught with that language's equivalents (the note in `framework/tree/cp/cp.stl.md`) |
| What rating are you aiming for, by when? | `profile set cp.target_rating 1800`, `profile set cp.target_date 2027-08-31`, and add `cp.rating-1800` to `goals` |
| How much time a day, and how do you practise now? | goes into `learner/cp/plan.md` |

Then read the record before planning anything:

    python3 engine/calamity.py cf status
    python3 engine/calamity.py cf analyse
    python3 engine/calamity.py cf rating
    python3 engine/calamity.py cf upsolve

Place the learner in the tree from that record. A skill may be recorded as
known without a separate test when Codeforces has already tested it: its
band is at least 200 below the learner's rating and its tags show fifteen or
more solves at that band or above.

    python3 engine/calamity.py placement cp.implementation --result known --note "CF 1540, 96 implementation solves, level 1500"

Everything else is tested or learnt. A newcomer with no handle starts at
`cp.cpp` and makes an account when they are ready for a first contest.
Enrol the skills of the next milestone that are not yet known, add `cp` to
`tracks`, and hand the record to the `cp-coach` agent for the first plan.

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

`cf recommend` picks unsolved problems rated 100 to 300 above the current
rating, weighted toward weak tags, and hides the tags: recognising the
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

## One problem, done properly

1. **Read and restate.** One sentence for the task; constraints turned into
   a complexity budget; samples worked by hand.
2. **Think inside a time box.** As a rule of thumb, 20 to 30 minutes for a
   problem 100 above the learner's rating, up to an hour for one 300 above.
   When stuck, the coach gives one hint (count it); not the editorial.
3. **Code, test, submit.** Samples, the smallest input, a corner case, a
   maximum-size input.
4. **If it is accepted**: two lines from the learner, the idea and the
   complexity. Then record it:

       python3 engine/calamity.py cf sync
       python3 engine/calamity.py cf credit 1520C --topic cp.binary-search/on-answer
       python3 engine/calamity.py cf mark 1520C subtag --subtags binary-search-on-answer,greedy-check

   `cf credit` makes the judged solve count as verified evidence for the
   topic. Wrong submissions before the accepted one make it count as hard.
   It covers solves from the last 14 days.
5. **If the time box runs out**: read the editorial, or have the coach
   explain it, then implement without looking, and record
   `python3 engine/calamity.py cf mark <problem> editorial`. The problem
   returns after a week for a clean solve; after that,
   `cf mark <problem> resolved` and then `cf credit`.

Record each set that is handed out:
`python3 engine/calamity.py cf assign 1520C 1843E 1900D --reason "binary search on answer, band 1400-1600"`.

## Contests

- **Before**: choose from `cf contests`; nothing new that day; template
  compiled and ready.
- **During a rated contest: no help of any kind.** No ideas, no hints, no
  debugging, no code, no test cases for its problems, from the moment it
  starts until it is over. Codeforces forbids outside help in rated rounds,
  and a rating earned with help measures nothing. If asked, refuse in one
  line and offer to review afterwards. Treat virtual contests the same way,
  or they stop predicting anything.
- **After**: `cf sync`, then `cf contests` and `cf rating` for the result.
  Review with the learner, problem by problem: time spent, wrong
  submissions and the cause of each, where the idea came or did not. Save
  it as `learner/cp/reviews/<contest>.md`. Then upsolve.

`cf sync` records a rating milestone by itself when the rating history
shows it.

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

## Teaching the language and the library

`cp.cpp` and `cp.stl` are taught like every other skill: one small chunk,
then a `code` item compiled with `g++ -std=c++17 -O2 -Wall -Wextra` (plus
`-fsanitize=address,undefined` while learning) and run against cases. Teach
a technique when it is what blocks problems in the learner's band. A
topic's own `band` says when a harder part of a skill starts to matter.
With a linked handle the engine leaves those parts for later by itself: a
topic banded more than `cp.band_lookahead` (200) above the highest rating
milestone reached is not started, and a skill's boss and its readiness do
not wait for it. `ask --topic <key>` still takes one now if the learner
wants it.

## Files

| Path | Holds |
|---|---|
| `learner/cp/plan.md` | band, focus tags, weekly numbers, contest calendar, date of the next review (written by `cp-coach`) |
| `learner/cp/reviews/<contest>.md` | one review per contest |
| `learner/cp/solutions/` | accepted code the learner wants to keep |
| `learner/cp/stress/` | brute force, generator and compare script for stress tests |

Codeforces data itself (submissions, ratings, the problem set) is cached on
each machine and can always be fetched again; only the coach's own records
(assignments, marks, sub-tags, credits) are in the learner's log.
