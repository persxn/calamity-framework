# GATE playbook

The GATE companion is the tutor pointed at one exam date. It follows the
learner through their own course or playlist, tests each lecture the day it
is watched, brings every topic back until the exam, and keeps one question
in view: where does the next hour buy the most marks?

Facts about a year (dates, pattern, marking) are in `framework/gate/<year>.md`.
Subjects and topics are the `gate`, `gate-cs` and `gate-da` tracks of the
tree. Everything about a particular learner is asked, never assumed.

This file covers the daily work: the loop, mocks and test series, past
questions. Onboarding is in `framework/rules/gate-onboarding.md`; the
target, the plan, phases and triage in `framework/rules/gate-planning.md`.

## The daily loop

1. Surprise recall across all subjects.
2. Lecture from the source, then `calamity log <source> <lecture>`,
   then its test straight away. `next` surfaces it as "lecture logged, not
   tested yet". Teach only what the test exposes; the course did the
   teaching.
3. Reviews as they come due.
4. `today` for the finish line; `gate status` once a week.

A learner who studies other tracks as well gets GATE and the others in
turn. `calamity profile set focus gate` puts GATE ahead of
everything else, which is the right setting for the revision and final
phases.

Items are in exam style: MCQ, MSQ and NAT, 1 or 2 marks, with the exam's
marking (a wrong 1-mark MCQ costs 1/3, a wrong 2-mark MCQ 2/3, MSQ and NAT
cost nothing). The engine applies it in tests and in every marks line.

## Mocks and test series

- **Record every mock**, full or sectional:

      calamity gate mock CS 54.33 --source "series name, full test 3" --sections "GA=11.33,EM=8,OS=5.67"

- **Review within a day.** For each question that was wrong or guessed:
  find its topic (`find <words>`), name the kind of error, and bring the
  topic back:

      calamity quick gate.cs.operating-systems/deadlock fail --err concept --note "mock 3 Q41: Banker's safe sequence"

  `gate errors` then shows where the marks are leaking. Careless and
  misread errors are fixed by exam habits (re-read the last line, check
  units), not by more theory. A question from a topic not studied yet
  gets no entry: the engine refuses it, because that topic is still ahead
  in the plan and there is nothing to bring back.
- **Official past papers are the best mocks.** Keep the most recent years
  unseen for the revision and final phases and sit them timed, at the
  exam's hour, with the on-screen calculator the exam provides.
- **Choosing a test series.** The framework recommends none by name. When
  the learner asks, the strategist looks at what is on offer now and reports
  with sources and the date: how closely each follows the official pattern
  (65 questions, 3 hours, the MCQ/MSQ/NAT mix), the quality of its
  solutions, its analytics, its schedule against the plan, and its price.
  Suggest starting sectional tests once half of a subject is tested and
  full mocks in the build phase.
- A mock score is the measure. If mocks and "backed by practice" disagree,
  believe the mocks and find out why.

## Past questions

The framework ships no question bank. Official papers and keys are
published by the organising institutes; the learner brings the paper, and
its questions are transcribed as `official` items with their reference
("GATE CS 2024 Q.31"), mapped to topics, imported and checked
(`framework/rules/verification.md`). Do not reproduce a coaching
institute's questions or solutions, and do not present a question written
from memory as official.
