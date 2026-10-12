---
name: boss
description: "Run a boss, the project or timed test that proves a skill, or a capstone milestone. Use when a boss is due or the learner wants to prove or finish a skill, or asks for a project, mock or final test on one."
argument-hint: "[skill]"
effort: high
---

# Boss

A boss comes up when every topic of a skill is solid. Passing it is the
last step to mastery, and it is what unlocks a capstone.

    python3 engine/calamity.py boss status            # which are due
    python3 engine/calamity.py boss status <skill>    # one specification

If the state is "not due yet", say how many topics are still short and
offer a study session instead. The learner may attempt it early if they
insist; a failed attempt costs nothing.

## A project boss (the skill file has a `# Boss` section)

1. Read out the brief and every line under "Passes when". Where the brief
   leaves a choice to the tutor (a domain, a size limit, a bar), fix it now
   and say it, so the target cannot move later.
2. The work goes in `learner/work/<skill>/boss/`, in its own git history
   if the learner knows git. They build it. You may answer questions about
   concepts and review what they wrote; you do not write the solution, and
   you do not give the steps.
3. Weave: ask `python3 engine/calamity.py weave <skill>` and require the
   earlier skills it names where they fit naturally (a Dockerfile, tests, a
   pipeline, a commit history).
4. When they say it is done, check **every** line under "Passes when" by
   running it. Read `framework/rules/verification.md`, "Hands-on work and
   bosses".
5. Record the outcome with what was run:

       python3 engine/calamity.py boss record <skill> pass --evidence "repo path; each check and its result"
       python3 engine/calamity.py boss record <skill> fail --evidence "which check failed and how"

   One failed check is a fail. Say exactly which check failed and what it
   showed; they fix it and you check again.

## A test boss (no `# Boss` section: GATE subjects and others)

A timed mixed test of the skill stands in.

    python3 engine/calamity.py test build --skills <skill> --n 10 --minutes 25 --label "boss: <skill>"

- Exit code 4: the bank is short. Send the printed list to the `examiner`
  agent, the new ids to the `checker` agent, then build again.
- Exam conditions: no hints, no feedback between questions. For each item
  in order: `python3 engine/calamity.py ask --id <item> --test <test>`,
  then `python3 engine/calamity.py answer <item> --answer "..."`. A skipped
  question is simply not answered.
- When they finish or time is up: `python3 engine/calamity.py test finish <test>`.
  It prints the score (with GATE marking where it applies) and the
  solutions of the missed items. Go through those with the learner and
  record each kind of mistake: `python3 engine/calamity.py mistake <item> <kind>`.
- Pass mark: 80% for a skill test, unless the learner's plan sets another.
  Record it: `python3 engine/calamity.py boss record <skill> pass --kind test --evidence "test <id>: 8.67 of 10"`.

## A capstone milestone

Milestones (`mern-stack`, `fullstack-production`, `ten-x`, `ai-capstone`
and the like) have no topics: they are a boss and nothing else. Treat them
as a project boss over several sessions. Agree the scope in writing first
(a short design note in `learner/work/<milestone>/DESIGN.md`), and check in
at each session without taking over.

Rating milestones of the competitive-programming track are recorded by
`python3 engine/calamity.py cf sync` when Codeforces shows the rating; they
are not attempted here.

## Afterwards

Show what passing unlocked (the engine prints it) and the next suggestion
(`python3 engine/calamity.py tree suggest`). Save a notes fragment about
the project: what was built, what broke, what they would do differently.
