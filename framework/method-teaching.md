# Teaching new material

Load this whenever a session teaches a new topic or chunk: the study skill on
a `NEXT: new` block, a GATE lecture, a CP concept. Recall rounds, boss tests
and contests do not teach new material and do not need it. How to run the
session loop, ask, judge and record, and the two modes, are in
`framework/method.md`; this file is only the teaching standard, in full.

This is the one, non-negotiable depth standard for **every** path that teaches
here — `study`, GATE and CP, and `mastery-coach` alike. The deep arc in
`.claude/skills/teach-deep/SKILL.md` builds on it at length; a topic taught the default way is taught just as deeply as one a
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
  Assuming a prerequisite *in substance* — building on an idea the record
  does not evidence because it seems advanced or "well known" — breaks this
  even when the lesson looks thorough and the diagram is complete. When a
  topic rests on something unevidenced, teach that piece first in a line or
  two, or confirm it; never build on top of it and hope.
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
- **The order the learner meets it in.** The depth above is the *content*;
  this is the *order*, and it binds tracked study every bit as much as
  `mastery-coach`: (1) **why** — the real problem that makes the concept
  necessary; (2) **what** — name it and its minimum prerequisites, with a
  concrete example; (3) **what breaks without it**; (4) **the mechanism that
  fixes that**; (5) **watch it work** — one example walked step by step,
  tracking the state (memory, data flow, the tree, the trust boundary);
  (6) **edge cases** — where it fails and why alternatives do not always
  work; (7) **connect** — its place in the bigger system; (8) **formalise** —
  precise definitions and standard terms, only now; (9) **practise** — the
  engine's items; (10) **compress** — the recap below. One line: problem
  first, intuition before formalism, show it working, break it, then test on
  something new. Do not invert it: rushing to rigor, breadth or edge cases
  before the core picture lands is the usual way depth is faked — completeness
  in the first pass crowds out the one idea that has to land first. For a
  security topic, trace the whole causal chain — faulty assumption → root
  cause → fix → verification of the fix — never reduce it to tool commands.
- **Make the intuition land (how each chunk is delivered).**
  - **Concrete before symbolic.** Use distinguishable, traceable values the
    learner can run in their head (`a + b * c`, the numbers `2, 3, 4`) before
    any abstract meta-symbol (`id + id * id`, where everything looks the same
    and the structure hides). The symbolic form comes only once the picture is
    understood.
  - **Draw it first for anything structural.** For parse trees, grouping,
    state, memory, data flow or trust boundaries, give the diagram first and
    let it carry the idea; the stated principle is its caption, not the
    teaching. Asserting "precedence is depth" without the picture that makes
    it self-evident is telling, not teaching.
  - **Build up.** Show how the small pieces compose into the big ones (atoms →
    factors → terms → expressions), so the structure feels inevitable rather
    than arbitrary.
  - **Every worked example is labelled and walked.** Say what it demonstrates
    before it, name which case it is, and walk each step with its state and
    reasoning. Never drop a derivation or a trace in whole and move on.
  - **Beginner register.** Short sentences, one idea each; define every term
    inline the first time it appears; a plain metaphor before the formal name.
    Defer rigor and edge cases to their own steps — never crowd the first
    intuition pass with undefined jargon.
  - **No ambiguous labels.** Never show the internal scaffold words raw
    ("without it", "with it", a bare "it"): replace the placeholder with the
    concrete concept or mechanism the chunk is about, so no heading, definition
    or sentence is unclear about what it names, and every pronoun has one
    named referent.
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
- **Close a topic by compressing it.** When its chunks are done, give the
  learner a compact recap they can keep, and save it as the topic's notes
  fragment (`notes`): the mental model in one paragraph (how to picture it
  running); the key relationships as a small diagram or `A → B → C`;
  the precise definitions, with the terms a textbook, exam or interview uses;
  three to seven must-remember points; the concise exam-or-interview version;
  and one reconstruction question that asks the learner to rebuild the
  mechanism, not recall a word (formative, or a seed for the `examiner`). The
  recap compresses only what was taught; nothing new appears in it. A topic
  that was taught but never compressed is not finished.
- Prefer the learner's own project, code and mistakes as examples.
- Hands-on skills are tested hands-on. The learner types the commands and
  the code; you check the result by running it.
- Check facts that change (library APIs, versions, exam dates, contest
  rules) against the official source before teaching them, and say when you
  could not.
- Adapt to the evidence, not to a guess. The brief's "Observations" line and
  `calamity stats flags` say what the log shows: many hints on a topic means
  smaller chunks; careless errors mean slower checking, not more theory;
  correct but slow means timed drills; nine of ten right means harder items.
- Follow the learner's stated preferences (`Teaching preferences` in the
  brief) unless the evidence says they are not working, then say so.
