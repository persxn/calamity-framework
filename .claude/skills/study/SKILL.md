---
name: study
description: "A study session: surprise recall first, then one small chunk at a time, each tested at once, earlier skills woven in. Use when the learner wants to study, learn, continue, practise or be taught a skill or topic, or says \"let's start\"."
argument-hint: "[skill or topic]"
---

# Study session

The engine decides what comes next; you teach, ask, judge and record. How
to ask and judge is in `framework/method.md` (already in context); this is
the procedure. Commands are shown for Linux and macOS; on Windows use the
command the brief names after `engine:`.

## 0. Open

- `NOT ONBOARDED` in the brief: run the onboard skill instead.
- Inside the sleep window: say so once; reviews only if the learner insists.
- An argument names what to study. Resolve it with
  `python3 engine/calamity.py find <words>` if it is not an exact id.
  - Not enrolled: `python3 engine/calamity.py enroll <skill>`. If it is
    locked, show the prerequisites the engine lists and the route
    (`tree path <skill>`); `--force` only if the learner wants it anyway.
  - "no syllabus yet": delegate to the `curriculum-architect` agent ("write
    the syllabus for `<skill>` for this learner"), then
    `python3 engine/calamity.py syllabus check <skill>`.
  - They say they already know it: a placement test, not a debate
    (`framework/rules/syllabus.md`).

## 1. Stock the item bank, in the background

    python3 engine/calamity.py item needs --skill <skill>

(without `--skill` for a session across everything). If it lists topics,
ask the `examiner` agent to stock them ("stock the item bank for
`<skill>`"; it reads the details itself), then give the ids it returns to
the `checker` agent to verify blind. For an item the checker rejects, ask
the examiner for a fresh one. Start step 2 meanwhile with what is already
verified. Never write an item yourself and never verify one here.

## 2. Surprise recall

As many times as the brief says ("Surprise-recall candidates"):

    python3 engine/calamity.py ask --due

Ask without saying which skill a question comes from and without warming
the learner up. Nothing due: skip this step.

## 3. The main block

Repeat until the finish line, the sleep guard, or the learner stops:

    python3 engine/calamity.py ask --skill <skill>

(plain `ask` in a session across everything). It serves the next question,
a review or a topic already taught, or prints what comes instead:

| It prints | Do |
|---|---|
| an item | Ask and record it (below). |
| `NEXT: new` | Teach one chunk: the idea in a few sentences, one worked example, one thing for the learner to do. Then `python3 engine/calamity.py ask --topic <key> --taught`, which records the teaching and serves the question. |
| `NEXT: watch` | Name the next lecture. When the learner has watched it, `python3 engine/calamity.py log <source> <item>`; its test follows. If they would rather carry on with another skill, `ask --skill <other>`. |
| `NEXT: boss` | Run the boss skill for that skill. |
| `NEXT: syllabus` | Delegate to the `curriculum-architect` agent ("write the syllabus for `<skill>` for this learner"), then `python3 engine/calamity.py syllabus check <skill>`. |
| `NEXT: wind-down`, `sleep`, `done` | No new material. Offer what reviews remain, then close. |
| `NEXT: enroll`, `onboard` | Help them pick a skill (`tree suggest`), or run the onboard skill. |

**Asking and recording.** Show the question exactly as the engine prints
it, between the dashes. Record the reply with
`python3 engine/calamity.py answer <item> --answer "<what they said>"`.
For a hands-on item (code, task, open) the learner works in
`learner/work/<skill>/...`; when they are done, get the check with
`python3 engine/calamity.py item show <item> --check`, run it for real,
and record `--result pass|fail --evidence "what was run and what happened"`.
If it fails, say what the check showed, not how to fix it; let them try
again, or record the failure with `--err <kind>` and then explain.

**After every answer**, before anything else: say whether it was right, in
one line. When it was wrong, show the key and the solution as the engine
printed them, find the cause (one question, unless the learner already
said it), record it with `mistake`, and repair the gap in a few lines.
Only then go on.

**`NEED_ITEM`** (exit code 4): no verified item for that topic yet. Give
the topic to the examiner, the new id to the checker, then ask again. If
the learner should not wait, take another topic meanwhile, or record an
oral check, which schedules the topic but is not evidence:
`python3 engine/calamity.py quick <key> pass|fail`.

**Hints**: three steps (restate, point to the idea, first step), each
counted with `--hints N`. **A woven exercise that fails**: add
`--blame <key>` for the topic that broke.

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
