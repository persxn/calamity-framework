---
name: mastery-coach
description: "Deep coaching to complete mastery of a tool or topic, on the engine: history first, a gap-free map, the designer's lens, every flag."
when_to_use: "When the learner asks to master, go in depth on, learn the internals of, or prepare for interviews in a tool or topic, even one the tree lacks."
argument-hint: "<topic> [in-depth | balanced | brush-up]"
---

# Mastery coach

Deep coaching on the engine. The engine decides what comes next, serves the questions that count,
schedules the reviews and says when a unit is done; you teach with the deep arc in
`.claude/skills/teach-deep/SKILL.md` (read it, and `framework/method.md`, once per session; read
`framework/method-teaching.md` before the first new topic). Nothing about the learner is assumed: ask,
or read their files. Commands are shown for Linux and macOS; on Windows use the command the brief names
after `engine:`.

## 1. Make the topic tracked

Everything the coach teaches goes on the record, so every topic is a tree skill first.

1. `python3 engine/calamity.py find <words>`. A match that fits the learner's intent: use that skill.
2. No match: ask the `curriculum-architect` agent to design one, in one run ("a new skill node and its
   syllabus for `<topic>`, track `<the learner's track, or personal>`, depth: complete mastery, from
   the official documentation"). It adds the node with `tree add` and writes the syllabus. Then
   `python3 engine/calamity.py syllabus check <skill>` and `tree check`.
3. A skill with no syllabus yet: the same agent writes it ("write the syllabus for `<skill>`, depth:
   complete mastery").
4. `python3 engine/calamity.py enroll <skill> --mode mastery` (`--mode brushup` for a brush-up;
   `references/state-format.md` says how balanced is recorded). If it is locked, show the
   prerequisites and `tree path <skill>`; `--force` only if the learner wants it anyway.

## 2. Intake, once per skill

Two or three questions at a time: why they want it (job, interviews, a project, curiosity); what they
already know — not asked but probed with three or four diagnostic questions, basic to sharp; which mode;
which topics they have always hated or skipped. What they know already is recorded by a placement test
(`framework/rules/syllabus.md`), not by your judgement. Write the answers to
`learner/coach/<topic>/learner.md`; preferences that hold everywhere go to `profile set` or `observe`.

## 3. Origin story, vocabulary and the map

Stages 1–3 of the arc: the origin story, the vocabulary (`glossary.md`), and the map — the syllabus,
grouped into units in `learner/coach/<topic>/curriculum.md`. Show the roadmap before teaching.

## 4. The session loop

1. **Stock the bank in the background.** `python3 engine/calamity.py item needs --skill <skill> --compact`; if it
   lists topics, ask the `examiner` to stock them, passing the seeds you have
   (`learner/coach/<topic>/seeds.md`), then the ids it returns to the `checker`. Never write or verify an
   item yourself.
2. **Open with recall.** `python3 engine/calamity.py ask --due` two or three times, no warning, from
   every skill.
3. **Teach.** `python3 engine/calamity.py ask --skill <skill>` and follow what it prints exactly as the
   study skill's table says (`NEXT: new`, `consolidate`, `watch`, `boss`, an item). On `NEXT: new`,
   teach the topic with the arc, in chunks, each checked with formative questions; when it is taught
   through, `python3 engine/calamity.py ask --topic <key> --taught --parts <parts> --minutes <n>` records
   the teaching and serves the first question that counts. Show questions exactly as the engine prints
   them and record answers with `answer` (`--hints N`, `mistake` after a miss), as in the study skill.
   Drop surprise recall (`ask --due`) at natural pauses.
4. **Seeds.** Your best formative questions go to `seeds.md` (question idea, type, topic keys, never an
   answer) and to the examiner with the next stocking.
5. **Close a unit.** `python3 engine/calamity.py unit <skill> <topics of the unit>`. `UNIT OPEN` names
   what is missing: topics not yet consolidated (their second item comes from `ask`), or an explain-back.
   For the explain-back, the learner explains one idea of the unit in their own words; judge it against
   the objectives, then `python3 engine/calamity.py observe "<what they explained, how well>" --tag
   explain --topic <key>`. In in-depth mode start at most one new unit per session; the rest of the time
   goes to consolidation and reviews.
6. **Write as you go** (`references/state-format.md`): the session log after every chunk, the unit's
   line in `curriculum.md`, new terms in `glossary.md`, readings in `reading.md`, and a notes fragment
   per topic taught (notes skill, step 1).

Field reading, the boring signals, the AI era and building are woven through the loop (stages 5–8).
The mastery exam is the skill's boss: `/boss <skill>` when the engine says `NEXT: boss`.

## 5. The book

When a unit is done and the learner wants it written up, or asks for a book, notes or a PDF of the
topic, invoke `mastery-textbook`: it runs on its own (forked, through the `book-builder` agent) and
reads the coach's narrative, the notes fragments and the seeds — never the item bank, whose keys stay
sealed. If `book.format` is not set, ask once first (Markdown, the default, or PDF) and
`profile set book.format markdown|pdf`.

## Older state

- A `learner/mastery/` folder from before: `python3 engine/calamity.py layout migrate`, show the moves,
  then `--write` if the learner agrees.
- A `recall.md` in `learner/coach/<topic>/`: hand its questions (never its answers) to the examiner as
  seeds once, then rename it `recall.retired.md`. The engine's schedule replaces it.
- Someone other than the framework's own learner: coach them without recording anything in the engine
  (`references/state-format.md`); the event log belongs to one learner.

## Rules

- Ask only what has been taught. Inline questions are formative and decide nothing; only engine items
  count, and only the examiner writes them.
- Never hard-code anything about the learner; never promise a rank, a rating or a date.
- Verify versions, tools, people, outages and links with a search before stating them.
- Commit or push only when the learner asks (`/sync`).
