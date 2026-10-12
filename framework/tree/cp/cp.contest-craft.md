---
id: cp.contest-craft
title: Contest craft
track: cp
group: craft
prereqs: [cp.cpp]
tags: [cp]
weaves_into: [cp]
aliases: [contest strategy, upsolving, stress test, virtual contest]
band: 800
est_hours: 10
order: 10
summary: "The habits around the algorithms: reading, testing, stress tests, upsolving, and staying steady in a contest."
---

`band` is the Codeforces rating from which this skill is expected; a topic's own `band` marks a part that belongs to a later rating. Practice problems come from `cf recommend --skill cp.contest-craft`.

# Boss

Take a full virtual contest at your division and hand in a written review within 24 hours.

Passes when:

- the review lists each problem with time spent, wrong submissions and the cause of each
- the first unsolved problem is upsolved, and marked with `cf mark` if the editorial was used
- a stress-test script exists under learner/cp/ and was run at least once during upsolving

# Weave

These habits are practised inside every problem, not as separate drills.

# Topics

## reading-statements | Reading a statement
level: 1
- restate the task in one sentence; list inputs, outputs and constraints; work the samples by hand

## testing-before-submit | Testing before submitting
level: 1
- run the samples, the smallest input, a corner case and a maximum-size input for time

## stress-testing | Stress testing
needs: [testing-before-submit]
level: 3
- a slow but obviously correct solution, a random generator and a loop that compares the two

## contest-strategy | Strategy during a contest
needs: [reading-statements]
level: 2
- read every problem you might reach; solve in order of expected time; decide when to move on
- what a wrong submission costs under each scoring system

## upsolving | Upsolving
needs: [contest-strategy]
level: 2
- after every contest solve the first problem you did not solve; this is where the rating comes from

## using-editorials | Using an editorial well
needs: [upsolving]
level: 2
- think for a set time first; read one hint, not the whole text; implement without looking
- write the idea in two lines and solve it again a week later

## virtual-contests | Virtual contests and rhythm
needs: [upsolving]
level: 2
- a steady weekly number of contests, real or virtual, each followed by a written review

## staying-steady | Staying steady
needs: [contest-strategy]
level: 2
- what to do after a wrong answer, when stuck for twenty minutes, and after a bad contest
