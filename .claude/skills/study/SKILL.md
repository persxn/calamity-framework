---
name: study
description: "A study session: surprise recall, then one small chunk at a time, each tested at once, earlier skills woven in."
when_to_use: "When the learner wants to study, learn, continue, practise or be taught a skill or topic, or says \"let's start\"."
argument-hint: "[skill or topic] [--deep]"
---

# Study session

The engine decides what comes next; you teach, ask, judge and record. Read
`framework/method.md` once at the start of the session: it says how to
ask, judge and run the loop; this is the procedure. The first time the
session teaches new material (a `NEXT: new` block), also read
`framework/method-teaching.md`, the teaching standard in full; with `--deep`, or
when the learner asks for depth, also `.claude/skills/teach-deep/SKILL.md`, and teach each new
topic with its arc (the same loop as `/mastery-coach`). Engine commands are written
`calamity <command>`; if the brief names another engine command after
`engine:`, use that one, and name it in every prompt you give an agent.

If the engine cannot record (an `ask` or `answer` fails: a read-only
checkout, a lock, an error), say so in a line, add what
`calamity next` says comes next (it reads only), and stop.
Teach nothing and answer nothing in its place, and offer no unrecorded
lesson: what is not recorded is not studied, and the order the engine
keeps (a topic secured before the next) holds either way.

## 0. Open

- `NOT ONBOARDED` in the brief: run the onboard skill instead.
- Inside the sleep window: say so once; reviews only if the learner insists.
- An argument names what to study. Resolve it with
  `calamity find <words>` if it is not an exact id.
  - Not enrolled: `calamity enroll <skill>`. If it is
    locked, show the prerequisites the engine lists and the route
    (`tree path <skill>`); `--force` only if the learner wants it anyway.
  - "no syllabus yet": delegate to the `curriculum-architect` agent ("write
    the syllabus for `<skill>` for this learner"), then
    `calamity syllabus check <skill>`.
  - They say they already know it: a placement test, not a debate
    (`framework/rules/syllabus.md`).
  - They name a topic further along: study its skill from where the
    engine says (`ask --skill <skill>`), not from that topic. If its
    earlier topics are new to them, say in one line that you will start
    there so the named topic makes sense.

## 1. Stock the item bank, in the background

    calamity item needs --skill <skill> --compact

(without `--skill` for a session across everything). If it lists topics,
ask the `examiner` agent to stock them ("stock the item bank for
`<skill>`"; it reads the details itself), then give the ids it returns to
the `checker` agent to verify blind. For an item the checker rejects, ask
the examiner for a fresh one, at most twice per topic; then leave that
topic and say so. Start step 2 meanwhile with what is already verified.
Never write an item yourself and never verify one here.

The agents run on this session's model. If the output ends with a
`settings:` line, pass it on in one line (the stronger setting while items
are written, the lighter one for reviews); the learner decides.

## 2. Surprise recall

As many times as the brief says ("Surprise-recall candidates"):

    calamity ask --due

Ask without saying which skill a question comes from and without warming
the learner up. Nothing due: skip this step.

## 3. The main block

Repeat until the finish line, the sleep guard, or the learner stops:

    calamity ask --skill <skill>

(plain `ask` in a session across everything). It serves the next question,
a review or a topic already taught, or prints what comes instead:

| It prints | Do |
|---|---|
| an item | Ask and record it (below). |
| `NEXT: new` | Teach the topic from where the block says to start (its `start from` line, `level`, `builds on` and `objectives`), **to the full depth contract in `framework/method-teaching.md`** — the same bar as the `mastery-coach` skill, never the popular one-paragraph summary. That almost always takes **several short chunks**, not one: why it exists and what came before, the mental model in plain words, the inner mechanics (why it behaves so, not only what it does), the simplest example then a real one, where it is used, and — for a tool — the flags that matter and the trade-offs. Define every new word. Check understanding between chunks and don't push past a shaky answer. Only once the topic is taught through, run `calamity ask --topic <key> --taught --parts <parts> --minutes <n>`, which records the teaching (the parts of the depth contract you actually taught: `history,model,mechanics,example,usage,flags,tradeoffs,impl`, and about how long it took) and serves the question; if it prints a `warning:` that parts are missing, teach them before the next topic; then save its notes fragment at once (notes skill, step 1) so the taught content is logged for the textbook, not left in chat. If `ask` adds a `note:` that earlier topics were never studied, go back to them first. |
| `NEXT: consolidate` | The topic was answered right once; a second item secures it. Ask it as you would a review (`ask` serves an item it has not been answered right on); no reteaching unless the answer shows a gap. With `not before HH:MM`, go on with what `ask --skill <other>` serves meanwhile. |
| `NEXT: watch` | Name the next lecture. When the learner has watched it, `calamity log <source> <item>`; its test follows. If they would rather carry on with another skill, `ask --skill <other>`. |
| `NEXT: boss` | Run the boss skill for that skill. |
| `NEXT: syllabus` | Delegate to the `curriculum-architect` agent ("write the syllabus for `<skill>` for this learner"), then `calamity syllabus check <skill>`. |
| `NEXT: wind-down`, `sleep`, `done` | No new material. Offer what reviews remain, then close. |
| `NEXT: enroll`, `onboard` | Help them pick a skill (`tree suggest`), or run the onboard skill. |

**Asking and recording.** Show the question exactly as the engine prints
it, between the dashes. Record the reply with
`calamity answer <item> --answer "<what they said>" --next --skill <skill>`
(without `--skill` in a session across everything). After a right answer
`--next` also serves the next question in the same call: say the result in
one line, then show the question below `=== NEXT`, treating it as the
output of `ask`. After a wrong answer it serves nothing; repair first,
then `ask`.
For a hands-on item (code, task, open) the learner works in
`learner/work/<skill>/...`; when they are done, get the check with
`calamity item show <item> --check`, run it for real,
and record `--result pass|fail --evidence "what was run and what happened"`.
If it fails, say what the check showed, not how to fix it; let them try
again, or record the failure with `--err <kind>` and then explain.

**Drills** (written by the `drill-smith`; `framework/rules/items.md`,
"Drills"). `debug`, `debug-docs`: the learner copies the fixture to a
folder of their own under `learner/work/<skill>/` and fixes it there; pass
means the check passes, no test file changed (`git diff --stat`) and the
diff stays inside `bounds`. In `debug-docs` every hint points to the docs
page (page, then section, then paragraph) and nothing else; record it with
`--note no-ai`. `read`: time it from the moment the question is shown and
record the location the learner gives with `--answer "path:symbol"`.
`audit`, `prompt`: judge the answer against the rubric (for an audit, each
flaw found and why it is wrong), then `--result`. `chaos`: make a throwaway
copy of the project (`git worktree add`), apply the injection that
`item show <item> --check` describes, and let the learner diagnose from the
logs alone. For a missing drill, ask the `drill-smith`, not the examiner.
A learner who gives up gets the cause only after `--result fail` is
recorded, from the solution the engine prints then; never from your own
reading of the code (`framework/method.md`, "Asking and judging").

**After every answer**, before anything else: say whether it was right, in
one line. When it was wrong, show the key and the solution as the engine
printed them, find the cause (one question, unless the learner already
said it), record it with `mistake`, and repair the gap in a few lines.
Only then go on.

**`NEED_ITEM`** (exit code 4): no verified item for that topic yet. Give
the topic to the examiner, the new id to the checker, then ask again (at
most two rounds; then move on and say so). If the learner should not wait,
take another topic meanwhile, or record an oral check (they explain the
idea in their own words, judged against the objectives; no question or key
of your own), which schedules the topic but is not evidence:
`calamity quick <key> pass|fail`.

**Hints**: three steps (restate, point to the idea, first step), each
counted with `--hints N`. **A woven exercise that fails**: add
`--blame <key>` for the topic that broke.

Otherwise, between questions — not while teaching a new topic, which gets
its full depth — say little: no summaries of what was just covered, no
praise for ordinary answers, no previews of the next topic.

## 4. Close

    calamity today

- Say where the finish line stands in one line. If `today` prints a
  `session:` line, pass it on once: a fresh session for the next block
  costs less per question. Never nag.
- For each topic taught today, save a notes fragment (notes skill, step 1).
- If you learnt something about how this learner learns, record it:
  `calamity observe "..." --skill <skill>`.
- If the brief showed "Behaviour pattern not yet raised today", raise it
  now as one question (`framework/rules/scheduler.md`).
- Mention `/sync` if progress has not been pushed for a while. Do not
  commit or push unasked.
