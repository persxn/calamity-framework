# GATE playbook

The GATE companion is the tutor pointed at one exam date. It follows the
learner through their own course or playlist, tests each lecture the day it
is watched, brings every topic back until the exam, and keeps one question
in view: where does the next hour buy the most marks?

Facts about a year (dates, pattern, marking) are in `framework/gate/<year>.md`.
Subjects and topics are the `gate`, `gate-cs` and `gate-da` tracks of the
tree. Everything about a particular learner is asked, never assumed.

## Onboarding a GATE learner

Ask in small groups, and record each answer as it comes.

| Ask | Record |
|---|---|
| Which year are you sitting? | `profile set gate.year 2027` |
| Which paper or papers? | `profile set gate.papers CS,DA` and add `gate-cs`, `gate-da` to `tracks` |
| Have you registered? | `profile set gate.registered true` |
| Do you know your paper's date yet? | `profile set gate.exam_date.CS 2027-02-07` (until then the engine counts down to the first exam day) |
| What are you aiming for: a rank, a score, an institute? | `profile set gate.target_rank 1000`; the target in marks comes later, with a source |
| Have you sat GATE or full mocks before? Scores? | `gate mock ...` for each, with its date |
| What do you study from, per paper? | the bridge skill connects each source |
| Where are you in it? | nothing, unless the source shows progress: then `log <source> <lecture> --upto` |
| Are you in a test series? | note it in `learner/gate/plan.md`; if not, see "Mocks" |
| How many hours a day can go to GATE, next to everything else? | `profile set cfg.gate.daily_hours 6` |
| Which subjects feel strong or weak? | an observation only; tests decide |

Then:

    python3 engine/calamity.py gate enroll
    python3 engine/calamity.py gate status
    python3 engine/calamity.py gate triage

- If the year has no file in `framework/gate/`, read the organisers' site
  for that year, write `learner/gate/<year>.md` with the same keys, and
  compare that year's syllabus documents with the shipped topic lists
  (`source_url` in each subject file). Differences go into
  `learner/syllabus/<subject>.md`.
- A learner is at the start of the syllabus unless their source says
  otherwise. Subjects they finished before arriving are sampled with a
  placement test (`framework/rules/syllabus.md`) instead of being walked
  through topic by topic.
- Hand the answers to the `gate-strategist` agent for the first plan.

## The target

A rank is decided by everyone else's marks too, so it cannot be promised and
it cannot be converted to marks by a formula. The strategist:

1. looks up the marks that corresponded to the learner's target rank in the
   paper's last few years, noting where each figure comes from and how it
   was obtained;
2. takes the highest of those, adds a margin, and proposes it as the target
   in marks;
3. records it with its basis:

       python3 engine/calamity.py profile set gate.target_marks.CS 72
       python3 engine/calamity.py profile set gate.target_source --text "rank 1000 needed about N marks in 2024-2026 (sources: ...); +5 margin; read 2026-10-11"

4. tells the learner in one sentence that it is an estimate that moves with
   the paper's difficulty.

From then on `gate status` shows two numbers against the target: the last
mock, and "backed by practice" (subject weight x share of topics tested x
accuracy on verified answers), which is a floor, not a forecast. `gate mocks`
shows the trend across mocks.

## Planning backwards

The strategist writes `learner/gate/plan.md` from these steps and redoes
them every two weeks or after any mock.

1. **Time.** Days left (`gate status`) x daily GATE hours. Hold back the
   last six weeks for revision and mocks; what remains is the time for new
   material.
2. **Need.** `gate triage` gives hours left per subject. Add them up.
3. **Fit.** If the need exceeds the time, something gives: more hours, or
   fewer subjects. Walk up the triage table from the bottom (lowest marks
   per hour) and show what each cut frees and what it costs in marks. The
   learner chooses. General Aptitude is never cut: it is 15 marks for the
   least study.
4. **Order.** Subjects in triage order, shared subjects first when two
   papers are being taken.
5. **Weekly quota.** Lectures per day (`profile set cfg.lectures_per_day 3`),
   new topics per day, and the test for the week.

```markdown
---
updated: 2026-10-11
papers: [CS, DA]
days_left: 118
---

# Position
# Target and its basis
# Hours: available, needed, gap
# Subject order and dates
# Cuts considered (and what the learner decided)
# This fortnight
# Mock calendar
# Changes
```

## The daily loop

1. Surprise recall across all subjects.
2. Lecture from the source, then `python3 engine/calamity.py log <source> <lecture>`,
   then its test straight away. `next` surfaces it as "lecture logged, not
   tested yet". Teach only what the test exposes; the course did the
   teaching.
3. Reviews as they come due.
4. `today` for the finish line; `gate status` once a week.

A learner who studies other tracks as well gets GATE and the others in
turn. `python3 engine/calamity.py profile set focus gate` puts GATE ahead of
everything else, which is the right setting for the revision and final
phases.

Items are in exam style: MCQ, MSQ and NAT, 1 or 2 marks, with the exam's
marking (a wrong 1-mark MCQ costs 1/3, a wrong 2-mark MCQ 2/3, MSQ and NAT
cost nothing). The engine applies it in tests and in every marks line.

## Phases

The engine names the phase from the days left.

| Phase | Days left | What changes |
|---|---|---|
| Foundation | more than 84 | Cover the syllabus in triage order. Every lecture tested the same day. A short topic test each week. |
| Build | 43 to 84 | Finish the remaining subjects. Sectional tests weekly. First full mocks, one every week or two. |
| Revision | 22 to 42 | No new subjects. Two full mocks a week, each followed by an error review. Notes condensed to recall prompts. |
| Final | 21 or fewer | Nothing new. The engine tightens reviews and gives every topic that would not otherwise return one last review, spread across the phase and ending three days before the exam. A mock every other day at the exam's hour. Sleep protected. |

## Triage and dropping

`gate triage` ranks subjects by marks still to gain per hour of study left:

- `marks`: the subject's weight. A star marks a prior, not a count.
- `to gain`: marks not yet backed by verified answers.
- `hours left`: the subject's estimated hours x the share not yet solid.
- `verdict`: `focus` for the top third; `candidate to drop` only inside the
  last ten weeks, for a subject that is barely started, costly and low in
  the ranking.

Weights first. Before trusting the ranking, replace priors: import official
past papers the learner supplies (`item import --official`, then
`gate weights --apply`), or set a figure with its source
(`gate weight gate.cs.toc 8 --source "..."`).

Dropping is the learner's call. When they make it:
`python3 engine/calamity.py pause <subject>` and record the reason with
`observe`. Paused subjects keep their progress and can be resumed. Inside a
subject, selective study means doing the topics with the most past
questions first; it never means skipping the test of a lecture that was
watched.

## Two papers

When a learner sits CS and DA, topics that are the same knowledge in both
syllabi are linked: an answer in one credits the other, so nothing is
studied or reviewed twice. Plan the shared ground first (linear algebra,
probability, calculus, programming and data structures, databases, logic),
then each paper's own subjects. Set both exam dates once they are known;
each subject counts down to its own paper.

## Mocks and test series

- **Record every mock**, full or sectional:

      python3 engine/calamity.py gate mock CS 54.33 --source "series name, full test 3" --sections "GA=11.33,EM=8,OS=5.67"

- **Review within a day.** For each question that was wrong or guessed:
  find its topic (`find <words>`), name the kind of error, and bring the
  topic back:

      python3 engine/calamity.py quick gate.cs.operating-systems/deadlock fail --err concept --note "mock 3 Q41: Banker's safe sequence"

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

## What to say, and what not to

- Say what the numbers show: days left, hours needed against hours
  available, marks backed by practice, the mock trend.
- Do not say a rank is on track or out of reach. Say what the current marks
  would have meant in recent years, with the source, and what would move
  them.
- When the plan no longer fits the time, say so that day and offer the cuts.
