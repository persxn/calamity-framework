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

This file covers a coaching turn: one problem, contests, teaching, files.
Onboarding is in `framework/rules/cp-onboarding.md`; levels, the week,
the analysis and the pace in `framework/rules/cp-planning.md`.

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
