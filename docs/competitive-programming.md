# The competitive-programming coach

One job: raise your Codeforces rating as fast as honest practice allows.
That means many problems just above your level, contests every week, every
missed contest problem solved afterwards, weaknesses attacked by tag, and
C++ and its library taught the moment they slow you down.

Start with `/onboard cp` (or choose competitive programming during
onboarding), then use `/cp`.

## Linking your handle

```bash
python3 engine/calamity.py cf link <your handle>
python3 engine/calamity.py cf sync
```

The engine reads your public record through Codeforces' official API:
submissions, rating history, the problem set and the contest list. No
password, key or cookie is involved. Codeforces asks API clients to make at
most one call every two seconds (https://codeforces.com/apiHelp), and the
engine waits between calls; a full sync takes about fifteen seconds. The
data is cached on each computer in `.calamity/cache/cf/` and can always be
fetched again; only the coach's own records (assignments, marks, credits)
go into your log.

No handle yet? You start at `cp.cpp` and make an account when you are ready
for a first contest.

## Where you stand

The examples below come from a pretend learner (`tools/demo.py`) whose
Codeforces data is made-up test data from the engine's own tests, not a
real account.

```
tester: rating 1234, max 1301, 4 rated contests
date        contest                rank  rating  change
----------  ---------------------  ----  ------  ------
2026-07-24  Round 900 (Div. 3)     4000     900    +900
2026-08-23  Educational Round 150  3000    1150    +250
2026-09-22  Round 910 (Div. 2)     2500    1301    +151
2026-10-07  Round 920 (Div. 2)     5200    1234     -67
last 30 days: +84 over 2 contest(s)
last 90 days: +1234 over 4 contest(s)
Fewer than six rated contests: Codeforces is still settling a new account's displayed rating, so these early gains overstate the pace.
target 1800: 566 point(s) to go by 2027-08-31, which needs about +53 a month; the last 90 days ran at +411 a month
A rating target is a direction, not a promise: it moves with contests entered and problems solved above your level.
next milestone: cp.rating-1400 | Codeforces 1400 (Specialist) (166 to go)
synced 10h ago
```

`cf analyse` lists your tags weakest first. The weakness score combines how
far a tag's level (the three hardest problems solved in it) sits below your
overall level, how often problems with the tag were tried and left
unsolved, and how little of it you have solved when the tree says it is due
at your rating. The last column names the skill of the tree that teaches
it.

```
tester: rating 1234 (max 1301) · 8 solved in all, 8 in the last 180 days · practice level 1140
solved: 2 in 7 days, 7 in 30 days
solved by rating (last 180 days): 800:1  900:1  1000:2  1100:2  1200:1  1300:1

tags, weakest first (level = mean of the 3 hardest solved; tries = wrong tries before AC)
tag             solved  unsolved  level  tries  weakness  due at this rating  tree skill
--------------  ------  --------  -----  -----  --------  ------------------  -----------------
dp                   1         1      -    0.0      0.63  yes                 cp.dp-basics
binary search        1         0      -    1.0      0.51  yes                 cp.binary-search
greedy               1         0      -    1.0      0.51  yes                 cp.sorting-greedy
math                 2         0      -    0.0      0.48  yes                 cp.math-basics
implementation       5         0   1067    0.0      0.28  yes                 cp.implementation

due at this rating but not practised in the last 180 days: bitmasks (cp.bit-manipulation), brute force (cp.implementation), combinatorics (cp.combinatorics), constructive algorithms (cp.constructive), dfs and similar (cp.graphs-basics), dsu (cp.dsu), graphs (cp.graphs-basics), number theory (cp.number-theory), probabilities (cp.combinatorics), sortings (cp.sorting-greedy), strings (cp.strings-basics), ternary search (cp.binary-search), trees (cp.trees), two pointers (cp.prefix-sums-two-pointers)
synced 10h ago
```

## Practice sets

`cf recommend` picks unsolved problems rated 100 to 300 above your rating,
weighted toward your weak tags, with the tags **hidden**: recognising the
technique is part of the practice.

```
practice set for rating 1234: problems rated 1300-1600
problem  name     rating  solved by
-------  -------  ------  ---------
1605F    Bridges    1600       1518
1601B    Tiles      1500       1370
1602C    Queue      1300       1407
1600A    Fence      1400       1333
open one: https://codeforces.com/problemset/problem/<contest>/<index>
tags are hidden on purpose: recognising the technique is part of the practice (--show-tags to see why each was chosen).
record the set: cf assign 1605F 1601B 1602C 1600A --reason "..."
```

For each problem: read it and restate it, think inside a time box (about
20 to 30 minutes for one 100 above your rating), code, test, submit. When
it is accepted, two lines from you (the idea and the complexity), then:

```bash
python3 engine/calamity.py cf sync
python3 engine/calamity.py cf credit 1520C --topic cp.binary-search/on-answer
```

`cf credit` counts the judged solve as verified evidence for the topic;
wrong submissions before it make it count as a hard one. If the time box
runs out, read the editorial, implement without looking, and mark it
(`cf mark <problem> editorial`): it comes back in a week for a clean solve.

## Contests

- Before: `cf contests` lists the upcoming ones and virtual-contest
  candidates at your level. Nothing new that day.
- **During a rated contest, no help of any kind**: no ideas, hints,
  debugging, code or test cases, from the moment it starts until it is
  over. Codeforces forbids outside help in rated rounds, and a rating
  earned with help measures nothing. Virtual contests are treated the same.
- After: `cf sync`, a review problem by problem (time spent, each wrong
  submission and its cause), saved in `learner/cp/reviews/`, then upsolving
  (`cf upsolve`).

Rating milestones (`cp.rating-1200` to `cp.rating-2200`) are recorded by
`cf sync` as soon as your rating history shows them.

## The plan

The `cp-coach` agent reads your record and writes `learner/cp/plan.md`:
what limits your rating now (knowledge, implementation, contest handling or
volume, with the evidence), the band of problem ratings, focus tags, skills
to learn next, the week's load (raised a tenth or two from what you
actually did), and your pace against your target.

`cf rating` shows the gap to your target, the points a month the target
date needs, and the pace of the last ninety days. The coach never promises
a rating or a date; when the pace falls short, it says so with both
numbers, and you decide what changes.

## The skills

The `cp` track has 35 skills with 194 topics, from C++ and the STL through
complexity, implementation, sorting and greedy, binary search, number
theory, graphs, DP, trees, range queries and onwards, each with the
Codeforces tags it covers and the rating from which it is expected. They
are taught like any other skill (`/study cp.stl`), usually with code
compiled with warnings and sanitizers and run against cases, and followed
by problems on the technique (`cf recommend --skill cp.binary-search`).

A skill can be marked known from your record alone when Codeforces has
already tested it: its band is at least 200 below your rating and you have
solved fifteen or more problems with its tags at that band or above.

The full playbook is in `framework/rules/cp-playbook.md`.
