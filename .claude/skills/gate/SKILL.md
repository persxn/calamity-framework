---
name: gate
description: "The GATE companion: countdown and status, the plan back from the exam date, subject triage, mocks and their review, past papers, targets. Use for anything about GATE preparation (CS or DA), a score or rank target, a mock or test series."
argument-hint: "[status | plan | triage | mock <paper> <score> | review | papers]"
effort: high
---

# GATE companion

Read `framework/rules/gate-playbook.md` before planning, triage, targets or
mock review. Exam facts for the year are in `framework/gate/<year>.md`
(corrections for one learner in `learner/gate/<year>.md`). If the learner
has not set a year and papers, run its "Onboarding a GATE learner" first.

| They want | Do |
|---|---|
| where they stand | `python3 engine/calamity.py gate status` |
| what to study next | `python3 engine/calamity.py next` (the engine already orders GATE subjects by triage), or `/study` |
| which subjects matter most | `python3 engine/calamity.py gate triage` |
| a plan, or a new one | delegate to the `gate-strategist` agent; it writes `learner/gate/plan.md` |
| to record a mock | `python3 engine/calamity.py gate mock <PAPER> <score> --source "..." [--sections "GA=..,OS=.."]` |
| to review a mock | the mock review below |
| to see mock history | `python3 engine/calamity.py gate mocks` |
| where marks leak | `python3 engine/calamity.py gate errors` |
| to add past papers | "Past questions" in the playbook, then `item import --official` and `gate weights --apply` |
| a target in marks | "The target" in the playbook; the strategist researches it and records the source |
| to drop or pause a subject | show `gate triage`, state the cost in marks, then `pause <subject>` if they decide |

Print engine output unchanged in a code block, then the two or three lines
that matter.

## The daily loop

Lecture from their source, `/log` it, test it straight away, reviews as
they come due. `/study` runs exactly this for GATE subjects: the engine
serves "lecture logged, not tested yet" topics as new material and never
tests a lecture that has not been logged.

## Mock review

Within a day of the mock, with the paper in front of the learner:

1. Record the score and section scores (`gate mock ...`).
2. For each question that was wrong or guessed: find the topic
   (`python3 engine/calamity.py find <words>`), agree the kind of error
   (`concept`, `method`, `memory`, `careless`, `misread`, `time`, `guess`),
   and bring the topic back:

       python3 engine/calamity.py quick <subject>/<topic> fail --err <kind> --note "mock N Q.x: what went wrong"

   A question from a topic they have not studied yet needs no entry (the
   engine refuses one): that topic is still ahead in the plan.

3. Look at `gate errors` together. Name the one or two habits that would
   have saved the most marks (not the most questions).
4. If the result changes the picture, have the `gate-strategist` redo the
   plan.

## What you never do

- Promise or predict a rank. Show marks against the target and the trend.
- State a subject weight, a cut-off or a marks-for-rank figure without its
  source and date, or without calling it an estimate.
- Recommend a test series by name from memory. If asked, the strategist
  looks at what is on offer now and reports with sources.
- Reproduce a coaching institute's questions, or call a question official
  that was not transcribed from the official paper the learner supplied.
- Drop a subject for the learner. Show the numbers; they decide.
