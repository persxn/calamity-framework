# Verification

The learner's record is only worth something if what it counts is true. This
file says what must be checked, by whom, and how the check is recorded.

## Practice items

Two agents, two separate contexts. The one that writes an item never
verifies it, and the one that verifies never sees the key.

1. **Draft (examiner).** The examiner writes the item with its key and a
   solution, following `framework/rules/items.md`, saves the drafts as JSON
   under `.calamity/tmp/` and stores them:

       python3 engine/calamity.py item import --file .calamity/tmp/drafts.json --by examiner

   The engine seals the key, deletes the draft file and returns item ids.
   The examiner reports the ids and topics only: no answers, no solutions.

2. **Blind check (checker).** For each id the checker reads the item as the
   learner will see it:

       python3 engine/calamity.py item show <item>

   It first judges the question itself. An item is rejected, whatever its
   key, if it is ambiguous, has no correct option or more than one where one
   is expected, depends on information not in the stem, tests trivia rather
   than the topic, or relies on a fact that may be out of date:

       python3 engine/calamity.py item reject <item> --reason "..."

   Otherwise it solves the item independently. Wherever a computation can
   settle the answer, it computes: a short program, a brute force over all
   cases, a simulation, the real command. A numeric answer is derived twice
   by two routes. Then it submits its own answer:

       python3 engine/calamity.py item verify <item> --answer "<answer>" --by checker

   The engine compares that answer with the sealed key. A match makes the
   item `verified`. A mismatch rejects it; the checker is not told the key.
   A whole batch goes in one call:
   `item verify <item>=<answer> <item>=<answer> ... --by checker`.

3. **Hands-on items** (code, task, open) have a check instead of a key. The
   checker reads it with `item show <item> --check`, builds a reference
   solution in a scratch folder under `.calamity/tmp/`, runs the check for
   real, and also confirms that the check fails on an empty or deliberately
   wrong solution. Only then:

       python3 engine/calamity.py item verify <item> --ran --evidence "what was built, what was run, what passed, what failed as it should" --by checker

   If the check cannot be run on this machine, the item is not verified.
   Say what is missing instead.

4. **No repairs.** A rejected item is replaced by a fresh draft. Editing a
   stored item is not possible and not wanted: the log would no longer
   describe what the learner saw.

5. **Official questions.** Items transcribed from an official paper that the
   learner supplied carry `source.kind: official` with a reference (paper,
   year, question number). `item import --official` stores them as drafts
   with the official key, and the checker solves each one blind like any
   other item: a slip in the transcription must not reach the learner. A
   mismatch puts the item on hold as `disputed` until the transcription is
   compared with the paper (`item restore <item>` when it holds).

What reaches the learner: verified items only. `ask` refuses anything else.

## When the learner disagrees with a key

Do not defend the key from memory. Send only the item id to the checker
for a fresh blind solve (the objection may name the key). The checker
returns its own answer and does not run `item verify`, which the engine
refuses for a verified item. If its answer differs from the key, the key
does not hold:

    python3 engine/calamity.py item dispute <item> --reason "..." --void

`--void` cancels the answer that was graded against the wrong key, so the
topic's schedule and statistics return to what they were. If the key holds,
explain why, using the solution.

## Hands-on work and bosses

- A check is run, never assumed. "It should work" is not evidence.
- The learner writes the solution. You may explain, hint and review; you do
  not write the code that is being assessed.
- Evidence names what was run and what happened:
  `"docker build ok (182 MB); docker run + curl /health -> 200; USER is app"`.
- A boss passes only when every line under "Passes when" was checked and
  held. Record a failed attempt as a failure: it costs nothing and keeps the
  record straight.
- Run checks inside the exercise's own folder under `learner/work/`. A check
  never deletes files outside that folder, never needs elevated rights, and
  never sends the learner's data anywhere.

## What you teach

- Facts that change (APIs, versions, flags, exam rules, dates, contest
  rules) are checked against the official source when a syllabus is written
  and again when a learner meets something that looks out of date. A
  learner's syllabus lists the sources it was written from.
- Numbers about the outside world (subject weights, marks for a rank, rating
  expectations) are stored with their source and the date they were read,
  or labelled as estimates.
- Study notes contain what the session established. The notes writer does
  not add claims it has not checked, and code in notes is run before it is
  printed.

## What the engine enforces by itself

- Keys are sealed in the item file; `ask` and `item show` never print them
  before an answer is recorded.
- An item cannot be verified by its author, and its key cannot be revealed
  (`item show --reveal`) before the learner has answered it.
- Mastery counts only answers to verified items and judged Codeforces
  solves. Oral checks, answers given after seeing the solution the same day,
  and solves that followed an editorial schedule the topic but are not
  counted as evidence.
- Grades come from correctness, hints and time; nobody types a grade.

## The limit of this procedure

The examiner and the checker are separate contexts of the same kind of
model, so a blind spot they share can pass both. That is why the checker
computes instead of reasoning wherever it can, why official questions are
anchored to official keys, and why a learner's objection always triggers a
fresh check instead of an argument.
