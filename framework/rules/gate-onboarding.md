# GATE: onboarding

How a GATE learner is set up: year, papers, registration, target, sources,
hours. The daily loop and mocks are in `framework/rules/gate-playbook.md`;
targets, plans, phases and triage in `framework/rules/gate-planning.md`.

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
| Are you in a test series? | note it in `learner/gate/plan.md`; if not, see "Mocks and test series" in `framework/rules/gate-playbook.md` |
| How many hours a day can go to GATE, next to everything else? | `profile set cfg.gate.daily_hours 6` |
| Which subjects feel strong or weak? | an observation only; tests decide |

Then:

    calamity gate enroll
    calamity gate status
    calamity gate triage

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
