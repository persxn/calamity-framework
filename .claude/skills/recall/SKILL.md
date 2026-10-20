---
name: recall
description: "A rapid review round: only questions that are due, most forgotten first, from every skill, no new material. Use for a quick revision, a recall round, a warm-up, \"quiz me\", or when the learner has a few minutes."
argument-hint: "[how many | skill]"
---

# Recall round

Questions only. No teaching unless an answer is wrong, and then only the
repair. How to ask and judge is in `framework/method.md`; read it once per
session if it is not in context yet.

1. See what is due:

       python3 engine/calamity.py dash queue

   Nothing due: say so, show when the next reviews arrive (the "coming up"
   lines), and stop.

2. For each question, up to the number the learner asked for (default: all
   that are due, in batches of ten with a check-in between batches):

       python3 engine/calamity.py ask --due

   The engine serves the most urgent review and never new material. To
   stay inside one skill: `python3 engine/calamity.py next --skill <skill> --only`
   names the topic, then `ask --topic <key>`.

   - Show the question exactly as printed: the text between the first two
     lines of dashes, and nothing else. The line above it names the topic;
     do not show it or say which skill the question belongs to before the
     answer.
   - Record the reply: `python3 engine/calamity.py answer <item> --answer "..."`,
     or `--result pass|fail --evidence "..."` for a hands-on item after
     running its check (`item show <item> --check`).
   - Wrong: show the solution the engine prints, record the kind of
     mistake (`python3 engine/calamity.py mistake <item> <kind>`), give the
     one-paragraph repair, move on. The engine brings the topic back in a
     few minutes; ask it again before the round ends (`ask --topic <key>`).
   - If `ask --due` prints something other than an item (new material, a
     lecture to watch, done), the reviews are finished: stop.

3. `NEED_ITEM` (exit code 4): the topic has no verified item. Do not stall
   the round: ask the learner to explain the idea in their own words, judge
   it against the topic's objectives (no question or key of your own), and
   record that oral check

       python3 engine/calamity.py quick <key> pass|fail

   and afterwards send the printed block to the `examiner` agent and the new
   ids to the `checker` agent so the next review has a real item.

4. Finish with one line from `python3 engine/calamity.py today`: reviews
   done out of due, and what is left of the finish line.

Keep the pace up: one question, one answer, one line of feedback.
