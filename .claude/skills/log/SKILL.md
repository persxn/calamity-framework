---
name: log
description: Record study done outside this session - a lecture or chapter watched from a connected course or playlist, or a workout - so that it enters the plan and gets tested. Use when the learner says they watched, finished or completed a lecture, video, chapter or class, did a workout, or wants to undo a log entry.
argument-hint: "<source> <lecture id, number or title> | workout <minutes>"
---

# Log

## A lecture or chapter

    python3 engine/calamity.py log <source> <lecture>

`<lecture>` may be its id, its number in the source, or a piece of its
title that matches one lecture only. If the learner did not name the
source, `python3 engine/calamity.py source status` lists them with the
next lectures; if they have exactly one source, use it.

- Several at once: run the command once per lecture.
- "I am up to lecture N" for things watched before today:
  `python3 engine/calamity.py log <source> <lecture> --upto`
  (recorded as watched earlier, so it does not count as today's work).
- A mistake: `python3 engine/calamity.py log <source> <lecture> --undo`.
- A quiz or assignment score from the source: add `--score 8/10`.
- No source connected yet: run the bridge skill first.
- The engine says the title matches several lectures: show its list and
  ask which.

The engine answers with the topics that lecture makes ready to be tested.
Offer the test straight away; the minutes after a lecture are when testing
pays most:

    python3 engine/calamity.py ask --topic <key>

(the normal ask and answer loop of the study skill). If the lecture is not
mapped to any topic, say so and offer to map it
(`framework/rules/bridge-rulebook.md`, "Mapping lectures to topics").

## A workout

    python3 engine/calamity.py workout <minutes> [--note "run, 5 km"]

## Other study time

Time spent on a contest, a book or a class is not logged as minutes. What
counts is what was learnt: log the lecture or chapter if a source covers
it, credit solved Codeforces problems with the cp skill, and let the next
recall test the rest.

Confirm in one line what was logged. Do not log anything the learner did
not say they did.
