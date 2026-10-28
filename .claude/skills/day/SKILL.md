---
name: day
description: "Run the day: the block under way, one due task, surprise recall, then the block's work, closing at the finish line."
when_to_use: "When a session opens with /day (auto.start), or the learner says to just run the day or the next block."
argument-hint: "[block name]"
---

# Run the day

The orchestrator: you take the learner through the block they are in, the way they would run it
themselves, and ask at most one question at each block boundary. The engine says where the day is and
what is due; the other skills do the work. Read `framework/method.md` once per session.

## 1. Where the day is

    python3 engine/calamity.py day
    python3 engine/calamity.py tasks

`day` marks the block under way (`▸`) and the finish line; `tasks` lists the work around the studying
that has fallen due. Then:

- **Inside the sleep window**: say so in one line and stop; reviews only if the learner insists.
- **Between blocks**: name the next one and when it starts, offer what fits the gap (`ask --due` for a
  few minutes of recall), and stop when they say so.
- **A block under way**: go on below with its name and purpose.

## 2. One task, if it belongs here

At most one task from `tasks`, and only one that fits the block (a review block: `weekly-review` on its
day; a study block: `stock` before new material, `notes` at its end; the close: `push`). Run it through
the skill it names (`/coach`, `/gate`, `/cp`, `/stock`, `/notes`, `/sync`), then
`python3 engine/calamity.py tasks done <id>`. If the learner would rather not now:
`python3 engine/calamity.py tasks snooze <id>`. Never more than one per block.

## 3. Surprise recall

Two or three `python3 engine/calamity.py ask --due`, unannounced, as the study skill does. Nothing due:
skip it.

## 4. The block's work

Map the block's name and purpose to the skill that does it, and run that skill's procedure in this
session (do not hand the learner a command):

| The block is for | Run |
|---|---|
| recall, reviews, revision | the recall skill |
| GATE theory, a subject, new material | the study skill with that subject (`study <skill>`) |
| a lecture, a course, watching | the next lecture (`source status`), then `log` when it is watched, and its test |
| GATE practice, previous papers, a question book | the practice skill (`practice due` first) |
| a mock | the gate skill's mock flow |
| competitive programming, Codeforces, a contest | the cp skill (`set`, `contest`, `upsolve`) |
| developer track, a tool in depth | the mastery-coach skill on the goal's next skill |
| a workout | nothing to teach: `workout <minutes>` when they are back |
| a close, a wind-down, the review of the day | step 5 |

Keep to the block's end time. When it ends, say so in one line and ask the one question: go on into
the next block, or stop here.

## 5. Close

    python3 engine/calamity.py today
    python3 engine/calamity.py day

The finish line in one line; a notes fragment for every topic taught today (notes skill, step 1); what
you learnt about how they learn (`observe`); a `/sync` reminder when `tasks` lists `push`. Commit or
push only when the learner asks.

## Rules

- The day's shape is the learner's (`learner/schedule.md`): run it, never reshape it here; changes go
  through `/coach`.
- One question per block boundary, no more; between them, the block's skill decides what to say.
- Exam days and missed days follow the learner's recorded policy (`observations --tag coach`).
