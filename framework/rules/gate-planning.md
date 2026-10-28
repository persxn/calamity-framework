# GATE: planning

The target in marks, the plan back from the exam date, the phases, triage
and dropping, two papers, and what to say about the numbers. Read by the
`gate-strategist` agent and by the gate skill before planning, triage or
any talk about the target. Facts about a year are in
`framework/gate/<year>.md`.

## The target

A rank is decided by everyone else's marks too, so it cannot be promised and
it cannot be converted to marks by a formula. The strategist:

1. looks up the marks that corresponded to the learner's target rank in the
   paper's last few years, noting where each figure comes from and how it
   was obtained;
2. takes the highest of those, adds a margin, and proposes it as the target
   in marks;
3. returns it with its basis, as commands the tutor runs once the learner
   agrees (the strategist itself changes no settings):

       calamity profile set gate.target_marks.CS 72
       calamity profile set gate.target_source --text "rank 1000 needed about N marks in 2024-2026 (sources: ...); +5 margin; read 2026-10-11"

4. tells the learner in one sentence that it is an estimate that moves with
   the paper's difficulty.

From then on `gate status` shows two numbers against the target: the last
mock, and "backed by practice" (subject weight x share of topics tested x
accuracy on verified answers). The second measures coverage, not the exam:
practice is untimed and one topic at a time, so a full mock usually scores
well below it. Never present it as a predicted score. `gate mocks` shows
the trend across mocks.

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
`calamity pause <subject>` and record the reason with
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

## What to say, and what not to

- Say what the numbers show: days left, hours needed against hours
  available, marks backed by practice, the mock trend.
- Do not say a rank is on track or out of reach. Say what the current marks
  would have meant in recent years, with the source, and what would move
  them.
- When the plan no longer fits the time, say so that day and offer the cuts.
