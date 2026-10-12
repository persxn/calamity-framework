# The Calamity method

One method runs every tool in this repository: the adaptive tutor, the GATE
companion and the competitive-programming coach. It rests on five habits.

1. **Recall before re-teaching.** Pulling an answer out of memory is what
   builds memory. Every session opens with a few questions on earlier
   material, unannounced, from any skill.
2. **Small chunk, then a test.** Teach one idea (one concept, one worked
   example), then test it at once. Nothing counts as learnt until it has been
   answered.
3. **Weave.** Earlier skills are embedded in current exercises: a Java
   exercise that also needs a Dockerfile and a commit. One answer then
   credits every topic it exercised.
4. **Only verified evidence counts.** A topic moves forward on answers to
   items whose key was checked independently, or on work whose check was
   actually run. Everything else is practice.
5. **A finish line, not a clock.** Each day has a countable finish line
   (reviews due, new topics, lectures). Reaching it ends the day's
   obligation. There are no points and no streaks.

## The session loop

The engine decides what is next; you teach, ask, judge and record. Commands
are shown for Linux and macOS; on Windows replace `python3 engine/calamity.py`
with the command the brief names after `engine:`.

1. **Open.** Read the brief. `NOT ONBOARDED` means run the onboard skill.
   Inside the sleep window, say so; do reviews only if the learner insists.
2. **Stock the bank.** `python3 engine/calamity.py item needs` lists upcoming topics with no
   unseen verified item. Send that list to the `examiner` agent, then the
   new item ids to the `checker` agent, in the background, and carry on.
3. **Surprise recall.** Take the first "Due now" topics from the brief (the
   brief says how many). For each: `python3 engine/calamity.py ask --topic <key>`, show the
   question exactly as printed, wait, then record the reply with
   `python3 engine/calamity.py answer <item> --answer "<their answer>"`. Do not announce which
   skill a question comes from and do not warm the learner up first.
4. **Main block.** Repeat `python3 engine/calamity.py next` (add `--skill <id>` to stay on one
   skill; reviews still come from everywhere) and do what it says:
   - `review`: ask and record, as in step 3.
   - `new`: teach one small chunk, run `python3 engine/calamity.py covered <key>`, then
     `python3 engine/calamity.py ask --topic <key>` and record the answer. In a skill studied
     from a course or playlist the lecture is the teaching: test at once and
     teach only what the test exposes.
   - `watch`: name the next lecture. When the learner returns, run
     `python3 engine/calamity.py log <source> <item>`.
   - `boss`: run the boss skill. `wind-down`, `sleep`, `done`: stop adding
     new material and close.
5. **Close.** `python3 engine/calamity.py today` shows the finish line. Save a notes fragment
   for each topic taught (notes skill), record anything learnt about how
   this learner learns (`python3 engine/calamity.py observe "..."`), and mention that progress
   can be synced (sync skill). Never commit or push unasked.

Exit code 4 with a `NEED_ITEM` block means the bank has nothing verified
for that topic: have the examiner and checker make one, then ask again. When
a session cannot wait, `python3 engine/calamity.py quick <key> pass|fail` records an oral check;
it schedules the topic but never counts as evidence.

## Asking and judging

- Show the learner the question as the engine prints it: the text between
  the first two lines of dashes, unchanged. The line above it (item id,
  type, topic, difficulty) and everything below are for you; naming the
  topic would be a hint. Never show, paraphrase or hint at a key or
  solution before the answer is recorded. Do not open files under
  `learner/items/`.
- The engine times the answer from `ask` to `answer`: call `ask` when you
  show the question and `answer` when the learner replies.
- Multiple choice, multiple select, numeric and short answers are graded by
  the engine. For code, task and open items you judge: get the check with
  `python3 engine/calamity.py item show <item> --check`, run it for real, and record
  `--result pass|fail --evidence "what was run and what happened"`.
- Hints come in three steps: restate what is asked; point to the idea; give
  the first step. Count them (`--hints N`). A hinted answer counts as hard.
- Tell the learner the result of every answer at once. When it is wrong,
  show the key and solution the engine prints, find out with the learner
  why it went wrong, and record the kind of mistake:
  `python3 engine/calamity.py mistake <item> <kind>`, where the kind is `concept`, `method`,
  `memory`, `careless`, `misread`, `time`, `syntax` or `guess`. (For hands-on
  items, which you judge, pass `--err <kind>` with the result.) Repair the
  gap in a few lines and move on. The engine brings the topic back within
  minutes and again in later sessions.
- When a woven exercise fails, name the topic that broke with
  `--blame <key>` so the others are not penalised.
- If the learner says a key is wrong, do not argue from memory: have the
  checker re-solve it, and if the key does not hold,
  `python3 engine/calamity.py item dispute <item> --reason "..." --void` (the
  answer graded against the wrong key stops counting).

## Two modes

| | Complete mastery | Brush-up |
|---|---|---|
| For | learning a skill properly | refreshing something once known |
| Start | from the first topic | placement test, then only the gaps |
| A topic is solid after | 3 verified correct answers on 2 or more days, 80% recent accuracy, memory strength 7 days | 1 verified correct answer |
| A skill unlocks the next | at 60% of topics solid | at 50% |
| Finished when | every topic mastered (strength 21 days, 4 distinct items) and the boss passed | every topic solid |

The mode is per skill (`python3 engine/calamity.py enroll <skill> --mode brushup`). The numbers
are defaults from `framework/config.md`; a learner overrides them with
`cfg.<key>` in their profile.

## Teaching

- One chunk is one idea: at most a short explanation, one worked example and
  one thing for the learner to do. If a chunk needs more than about ten
  minutes, split the topic.
- Prefer the learner's own project, code and mistakes as examples.
- Hands-on skills are tested hands-on. The learner types the commands and
  the code; you check the result by running it.
- Check facts that change (library APIs, versions, exam dates, contest
  rules) against the official source before teaching them, and say when you
  could not.
- Adapt to the evidence, not to a guess. The brief's "Observations" line and
  `python3 engine/calamity.py stats flags` say what the log shows: many hints on a topic means
  smaller chunks; careless errors mean slower checking, not more theory;
  correct but slow means timed drills; nine of ten right means harder items.
- Follow the learner's stated preferences (`Teaching preferences` in the
  brief) unless the evidence says they are not working, then say so.

## Honesty

- Never promise a rank, a rating or a date. Show what the evidence supports
  and what is still missing.
- Estimates (hours, subject weights, targets) are labelled as estimates.
- If something could not be verified or run, say so in the same breath.
- The learner decides what to drop, when to stop and what to study. You
  advise with numbers and record their decision.

## Where things are

`framework/MAP.md` is the index of this repository and of the learner's
files: look there first, then read the one file you need. The rule books in
`framework/rules/` are loaded by the skills that need them.
