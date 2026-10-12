# The GATE companion

For the Computer Science (CS) and Data Science and AI (DA) papers. It
follows you through your own course or playlist, tests every lecture the
day you watch it, brings every topic back until the exam, plans backwards
from the exam date, and keeps one question in view: where does the next
hour buy the most marks?

Start with `/onboard gate` (or choose GATE during onboarding), then use
`/gate` for anything exam-related.

## The facts it works from

`framework/gate/2027.md` holds what the organisers published for GATE
2027, read from the official site (https://gate2027.iitm.ac.in) on
2026-10-12:

- exam days 6, 7, 13, 14, 20 and 21 February 2027, results on 19 March
  2027, organised by IIT Madras; the site says the dates are liable to
  change;
- 65 questions (10 General Aptitude, 55 subject), 100 marks, 3 hours;
- CS: General Aptitude 15, Engineering Mathematics 13, subject 72 marks;
  DA: General Aptitude 15, subject 85 marks;
- multiple choice (MCQ), multiple select (MSQ) and numerical (NAT)
  questions; a wrong 1-mark MCQ costs 1/3, a wrong 2-mark MCQ 2/3; MSQ and
  NAT carry no negative marks and MSQ has no partial marks.

Until you know your paper's date, the countdown uses the first exam day.
When the admit card names it: "my DA paper is on 14 February" (stored as
`gate.exam_date.DA`). To correct a fact for yourself, the same keys go in
`learner/gate/2027.md`.

## Onboarding

Claude asks the year and paper, whether you have registered, your paper's
date if known, what you are aiming for (a rank, a score, an institute),
earlier mocks, what you study from, and how many hours a day go to GATE.
Every subject of your paper is enrolled; a course or playlist is connected
with `/bridge` ([study sources](study-sources.md)); and the
`gate-strategist` agent writes a first plan in `learner/gate/plan.md`.

**The target.** A rank depends on everyone else's marks, so it cannot be
promised or converted to marks by a formula. The strategist looks up the
marks that matched your target rank in recent years for your paper, notes
where each figure comes from, adds a margin, and proposes a target in
marks, which is labelled an estimate.

## The daily loop

1. Surprise recall across all subjects.
2. A lecture from your course, `/log <source> <lecture>`, and its test
   straight away. The course does the teaching; Claude teaches only what
   the test exposes.
3. Reviews as they come due.
4. `/today` for the finish line, `/gate` once a week.

Practice questions are in the exam's style: MCQ, MSQ and NAT, worth 1 or 2
marks, with the exam's negative marking applied in every marks line and in
timed tests.

## Planning backwards

`gate triage` ranks subjects by the marks still to gain per hour of study
left. Here it is for a pretend learner after six simulated weeks
(`tools/demo.py`):

```
subject                    paper  marks  tested  accuracy  to gain  hours left  marks/h  verdict
-------------------------  -----  -----  ------  --------  -------  ----------  -------  -------
gate.general-aptitude      all     15.0   16/16       92%      1.8          1h     2.25  focus
gate.cs.compiler-design    CS      8.0*     7/7       89%      1.5          1h     1.50  focus
gate.cs.databases          CS      8.0*   11/11       91%      1.1          1h     1.09  focus
gate.cs.digital-logic      CS      8.0*     8/8       92%      1.3          5h     0.26  focus
gate.cs.discrete-math      CS      5.5*   12/12       82%      1.1          5h     0.23  keep
gate.cs.calculus           CS      2.5*     0/5         -      2.5         20h     0.12  keep
gate.cs.linear-algebra     CS      2.5*     0/5         -      2.5         25h     0.10  keep
gate.cs.probability        CS      2.5*     0/5         -      2.5         30h     0.08  keep
gate.cs.programming-ds     CS      8.0*    7/10       86%      4.3         60h     0.07  keep
gate.cs.algorithms         CS      8.0*   10/10       86%      1.6         36h     0.05  keep
gate.cs.toc                CS      8.0*     9/9       92%      1.4         37h     0.04  keep
gate.cs.computer-networks  CS      8.0*   16/16       98%      0.6         21h     0.03  keep
gate.cs.operating-systems  CS      8.0*   11/11       88%      1.6         60h     0.03  keep
gate.cs.coa                CS      8.0*   10/10       89%      1.5         60h     0.02  keep
* marks marked with a star are priors, not counts from official papers. Replace them with: gate weight <subject> <marks> --source "..."  or  gate weights --apply (after importing official papers).
'to gain' = marks not yet backed by verified answers. 'marks/h' ranks where the next hour pays most.
Hours are estimates from the subject files. Dropping a subject is the learner's decision; 'candidate to drop' only appears inside the last 10 weeks.
```

Weights marked `*` are planning priors, not counts from official papers:
the official pattern fixes only General Aptitude and, for CS, Engineering
Mathematics. Replace them with counts from official papers you import, or
with a figure and its source (`gate weight <subject> <marks> --source "..."`).

The strategist turns this into a plan: days left times your GATE hours,
the last six weeks held back for revision and mocks, the hours each
subject still needs, and, if they do not fit, what each possible cut would
cost in marks. You decide; General Aptitude is never cut.

| Phase | Days left | What changes |
|---|---|---|
| Foundation | more than 84 | Cover the syllabus in triage order; every lecture tested the same day |
| Build | 43 to 84 | Finish the remaining subjects; sectional tests weekly; first full mocks |
| Revision | 22 to 42 | No new subjects; two full mocks a week, each with an error review |
| Final | 21 or fewer | Nothing new; reviews held tighter; every topic gets one last review, ending three days before the exam |

## Mocks

Record every mock, full or sectional: "I scored 54.33 in full test 3 of my
series, GA 11.33, OS 5.67". Then, within a day, go through each wrong or
guessed question with Claude: find its topic, name the kind of error, and
bring the topic back into review. `gate errors` then shows where the marks
leak; careless and misread errors are fixed by exam habits, not by more
theory.

```
date        paper  marks/100  vs target  source           sections
----------  -----  ---------  ---------  ---------------  -----------------------
2026-09-19  CS         38.67      -31.3  sectional mix 1  GA 9, DM 7.33, DL 5
2026-10-03  CS         47.33      -22.7  sectional mix 2  GA 10.67, DM 9, DL 6.33
CS: last 2 average 43.0, best 47.3, change since first +8.7
```

`gate status` shows the countdown, the phase, the last mock against your
target, and per subject what is covered, tested and solid. Its "backed by
practice" figure (weight x share of topics tested x accuracy on practice
questions) measures coverage, not the exam: practice is untimed and one
topic at a time, so a full mock usually scores well below it. The mock is
the measure.

Official past papers are the best mocks: keep the most recent years unseen
for the last phases, and sit them timed at the exam's hour. Their questions
can be transcribed into your question bank as `official` items, with their
reference, and checked against the official key. The framework ships no
question bank and recommends no test series by name; asked, the strategist
compares what is on offer now, with sources and the date.

## Two papers

When you sit CS and DA, topics that are the same knowledge in both
syllabi are linked: an answer in one credits the other, so nothing is
studied or reviewed twice. Shared ground comes first.

## What it never does

- Promise a rank, or call a target safe or hopeless.
- State a subject weight, cut-off or marks-for-rank figure without its
  source and date, or without calling it an estimate.
- Reproduce a coaching institute's questions, or call a question official
  that was not transcribed from an official paper you supplied.
- Drop a subject for you: it shows the numbers, and you decide.

The full playbook is in `framework/rules/gate-playbook.md`.
