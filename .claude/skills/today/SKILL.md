---
name: today
description: Show today's plan and finish line - what is due, what is new, the next lecture, and the single next thing to do. Use when the learner asks what to do today, what is left, where they stand for the day, or how to spend the next hour.
---

# Today

    python3 engine/calamity.py today
    python3 engine/calamity.py next

Answer in a few lines, numbers first:

1. The finish line: reviews done of due, new topics done of the day's
   quota, lectures if they keep a lecture quota, and what is still to go.
2. The next action, in plain words (which topic to review, what to learn,
   which lecture to watch).
3. If `learner/schedule.md` exists, the block of the day shape this belongs
   to. Do not recite the whole schedule.
4. Only if it applies: inside the sleep window, or new material paused
   because the window is close; a boss that has come due; a pattern the
   brief marked as not yet raised today (one question, as described in
   `framework/rules/scheduler.md`).

If the learner asks how to use a fixed amount of time ("I have forty
minutes"), order it as the engine does: failed topics, due reviews, then
new material, and say roughly how far that time goes.

Do not pad it. No motivation speech, no recap of yesterday unless asked.
Offer to start (`/study` or `/recall`).
