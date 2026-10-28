---
name: stock
description: "Stock the item bank ahead (families for today and tomorrow, examiner then checker), headless at night or by hand."
when_to_use: "Run by the nightly scheduler (stock render) or by the learner; never during a study session."
disable-model-invocation: true
---

# Stock the bank

This runs with no learner present, usually headless at night
(`python3 engine/calamity.py stock render` schedules it). Nobody will answer
a question: decide from the engine's output, and finish. Use the engine
command the brief names (`engine:`); it is written `python3
engine/calamity.py` here.

1. The work list:

       python3 engine/calamity.py item needs --days 2 --per-topic 3

   `ITEMS: stocked` (or the learner is not onboarded): say so in one line and
   stop.
2. Split the listed topics into batches of at most 8. For each batch, one
   `examiner` agent, prompted with the engine command and:
   "Stock item families for these topics: <keys>. Read the details with
   `item needs --full --days 2 --per-topic 3`. Write each topic's family as
   its `family:` line says, across its objectives and depths."
   Batches may run in parallel.
3. One `checker` agent per examiner's returned ids (never the examiner
   that wrote them): "Verify these drafts blind: <ids>."
4. Check the result:

       python3 engine/calamity.py item needs --days 2 --per-topic 3

   and end with three lines: items verified, items rejected or disputed,
   topics still short (and why, from the agents' reports).

## Rules

- Never open files under `learner/items/` or the agents' scratch; never
  print a key, an answer or a solution. The output goes to a log file the
  learner may read before answering those items.
- Do not teach, record answers, change the profile or the schedule, or
  commit. Items are the only thing this run adds.
- Stop after one pass. Topics still short wait for the next run or the
  study session's own `NEED_ITEM`.
