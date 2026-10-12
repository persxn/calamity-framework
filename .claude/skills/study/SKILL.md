---
name: study
description: Run a study session with the Calamity loop - surprise recall first, then one small chunk at a time, each tested at once, with earlier skills woven into the exercises. Use when the learner wants to study, learn, continue, practise or be taught a skill or topic, or simply says "let's start".
argument-hint: "[skill or topic]"
---

# Study session

The engine decides what comes next. You teach, ask, judge and record. The
method is in `framework/method.md` (already in context); this is the
procedure.

## 0. What are we studying?

- No argument: whatever the engine says is next, across all enrolled skills.
- An argument: resolve it with `python3 engine/calamity.py find <words>` if
  it is not an exact id.
  - Not enrolled yet: `python3 engine/calamity.py enroll <skill>`. If it is
    locked, show the prerequisites the engine lists and the route
    (`tree path <skill>`); use `--force` only if the learner asks to go
    ahead anyway.
  - "no syllabus yet": delegate to the `curriculum-architect` agent
    ("write the syllabus for `<skill>` for this learner"), then
    `python3 engine/calamity.py syllabus check <skill>`.
  - They say they already know it: a placement test, not a debate
    (`framework/rules/syllabus.md`).

## 1. Stock the item bank (in the background)

    python3 engine/calamity.py item needs --skill <skill>

(omit `--skill` for a session across everything). If it lists topics:

1. Give the whole printed list to the `examiner` agent: "Draft one item for
   each topic in this work list and store them." It returns item ids.
2. Give those ids to the `checker` agent: "Verify these items blind." It
   returns which were verified and which rejected.
3. For a rejected item, ask the examiner for a fresh draft on that topic.

Run them in the background and start step 2 with whatever is already
verified. Never write an item yourself and never verify one in this
conversation.

## 2. Surprise recall

Take the first topics under "Due now" in the brief (it says how many). For
each, without saying which skill it is from:

    python3 engine/calamity.py ask --topic <key>

Show the question exactly as printed (the text between the first two lines
of dashes; the line above it names the topic and stays with you), wait for
the answer, then:

    python3 engine/calamity.py answer <item> --answer "<what they said>"

Show the result and the solution the engine prints. If the answer was
wrong, find out why with one question, record the kind of mistake with
`python3 engine/calamity.py mistake <item> <kind>`, repair the gap in a few
lines, and go on. Nothing due: skip this step.

## 3. The main block

Repeat until the finish line, the sleep guard, or the learner stops:

    python3 engine/calamity.py next --skill <skill>

(plain `next` in a session across everything).

| The engine says | Do |
|---|---|
| `review` | `ask --topic <key>`, then `answer`, as in step 2. |
| `new` (taught here) | Teach one chunk: the idea in a few sentences, one worked example, one thing for the learner to do. Then `python3 engine/calamity.py covered <key>`, then `ask --topic <key>` and record the answer. |
| `new` (lecture logged) | The lecture was the teaching. `ask --topic <key>` at once; teach only what a wrong answer exposes. |
| `watch` | Name the next lecture. When the learner has watched it, `python3 engine/calamity.py log <source> <item>`. If they would rather carry on with another skill now, `next --skill <skill>` stays inside it. |
| `boss` | Run the boss skill for that skill. |
| `wind-down`, `sleep` | No new material. Offer remaining reviews, then close. |
| `done` | The finish line is reached. Close, or continue only if the learner asks. |
| `enroll`, `onboard` | Help them pick a skill (`tree suggest`), or run the onboard skill. |

**`NEED_ITEM` (exit code 4)**: no verified item exists for that topic.
Send the printed block to the examiner, the new id to the checker, then
`ask` again. If the learner should not wait, take another topic meanwhile
or record an oral check: `python3 engine/calamity.py quick <key> pass|fail`
(it schedules the topic but is not evidence).

**Hands-on items** (code, task, open): the learner does the work in
`learner/work/<skill>/...`. When they say they are done:

    python3 engine/calamity.py item show <item> --check

Run that check for real, then record:

    python3 engine/calamity.py answer <item> --result pass --evidence "what was run and what happened"

If it fails, say what the check showed, not how to fix it; let them try
again, or record `--result fail --err <kind>` and then explain.

**Hints**: three steps (restate, point to the idea, first step), each
counted: `--hints N`. **A woven exercise that fails**: add
`--blame <key>` naming the topic that broke.

**After every answer**, before anything else: say whether it was right, in
one line. When it was wrong, show the key and the solution as the engine
printed them, find the cause (one question, unless the learner already
said it), record it with `mistake`, and repair the gap in a few lines.
Only then go on to the next topic.

Otherwise say little between questions: no summaries of what was just
covered, no praise for ordinary answers, no previews of the next topic.

## 4. Close

    python3 engine/calamity.py today

- Say where the finish line stands in one line.
- For each topic taught today, save a notes fragment (notes skill, step 1).
- If you learnt something about how this learner learns, record it:
  `python3 engine/calamity.py observe "..." --skill <skill>`.
- If the brief showed "Behaviour pattern not yet raised today", raise it
  now as one question (`framework/rules/scheduler.md`).
- Mention `/sync` if progress has not been pushed for a while. Do not
  commit or push unasked.
