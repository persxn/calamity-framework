# Teaching new material

Load this whenever a session teaches a new topic or chunk: the study skill on
a `NEXT: new` block, a GATE lecture, a CP concept. Recall rounds, boss tests
and contests do not teach new material and do not need it. How to run the
session loop, ask, judge and record, and the two modes, are in
`framework/method.md`; this file is only the teaching standard, in full.

This is the one, non-negotiable depth standard for **every** path that teaches
here — the engine-backed `study` skill, GATE and CP, and the self-contained
`mastery-coach` skill alike. It is the same bar `mastery-coach` describes at
length; a topic taught the default way is taught just as deeply as one a
learner reaches for `mastery-coach` to get. A single thin chunk, or the popular
one-paragraph summary, is a **failure of this standard, not a lighter option**.
Teaching a topic almost always takes several short chunks (below); do not
collapse it into one.

- **Start from the basics.** A skill is taught from its first topic, in
  the engine's order; never jump into the middle because the learner named
  a later topic. Each new topic starts from what it is and why it exists,
  defines every new word, and gives the simplest possible example before a
  realistic one. The `NEXT: new` block prints the topic's level, what it
  builds on and its objectives: teach to those objectives. Assume nothing
  the record does not show; if the learner says they already know it, offer
  a placement test (`framework/rules/syllabus.md`) instead of skipping.
- **Teach to depth, not to the mainstream surface.** The easy failure of an
  AI tutor is to skim the popular summary and quietly assume the beginner.
  Guard against it: across a topic's chunks, teach it through, in this order
  — (1) the problem it was invented to solve and what came before it;
  (2) the intuition, a mental model in plain words; (3) the inner mechanics,
  why it behaves as it does and not only what it does; (4) the simplest
  example, then a realistic one; (5) where it is really used, a short case
  or two; (6) for a tool or command, the flags that matter, what each is
  for, and how they combine; (7) the trade-offs and when not to reach for
  it. A topic whose objectives do not reach this far is thin: teach the
  missing depth anyway and note it (`observe`) so the syllabus is deepened.
  Say what was taught when recording it: `ask --topic K --taught --parts
  history,model,mechanics,example,usage,flags,tradeoffs,impl --minutes N`
  (the seven parts above, plus `impl` for reading or building the
  internals). A level-1 topic needs at least `model,example`, level 2
  adds `mechanics`, level 3 and above add `history,usage,tradeoffs`; the
  engine warns about a gap and never blocks. When the learner says the
  pace or depth is off ("too fast", "go deeper", "lost me"), record it at
  once: `feedback pace=slow|fast depth=more|less clarity=low --topic K`.
- **Doubt loop, before each new chunk.** Ask yourself first: where would a
  real beginner get confused here, what is the common misconception, and
  what would a sceptical expert challenge? Teach so those are met, not left
  for later. A new word you cannot yet motivate means the chunk starts too
  late; back up to what it rests on.
- **Taught before tested.** A question, an example or an exercise may use
  only the words, commands and ideas this lesson has already explained, or
  that the learner's record shows they know. Before asking, read the
  question back word by word: each term, command, flag and file in it must
  have been defined (a check on what the shell does needs "shell" defined
  first; an example that runs `grep` needs `grep` taught first). If one is
  missing, teach it in a line or two, or ask a different question. End each
  chunk with the facts its check relies on, so the learner can answer at
  once. A question about something untaught tests the lesson, not the
  learner.
- When an answer shows a gap in something earlier (a prerequisite, a
  word, a basic step), go back and teach that first, then return.
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
