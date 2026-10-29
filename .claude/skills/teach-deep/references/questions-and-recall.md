# Questions and recall

Two kinds of question run through deep teaching, and only one of them decides anything:

- **Formative** — asked inline while you teach, to check a chunk landed. You judge them in
  conversation; they never touch the record. Ask as many as the chunk needs.
- **Summative** — the engine's items, written by the `examiner`, verified blind by the `checker`,
  served by `ask` and recorded by `answer`. Only these move a topic toward `consolidating` and
  beyond, schedule reviews, and open the next unit.

Your best formative questions are *seeds*: hand them to the examiner (below) so the bank has items in
that spirit. The examiner writes its own items from them; you never write an item or its key.

## The coverage rule

Every question must be answerable from material already taught in this curriculum, or confirmed known at intake. Before asking, check which units the question draws on, and confirm from `curriculum.md` and the session log that they were taught. If a strong interview question needs something not yet taught, teach that piece first and then ask. A question about untaught material only tests luck, and it damages the learner's trust in the curriculum.

When you seed a question, name the topic keys it draws on.

## What interview-grade means

The questions should feel like a sharp senior engineer is asking them. They test mechanisms and intuition, not recall of trivia.

| Type | Shape | Example |
|---|---|---|
| Mechanism trace | "Walk me through exactly what happens when…" | "…you run `docker run nginx`, from the CLI to a running process." |
| Why-by-design | "Why did the designers choose X over Y?" | "Why is a Git commit identified by a hash of its content instead of an incrementing number?" |
| Predict the output | Show code or a command; the learner predicts before running it | Pointer arithmetic on an `int*` vs a `char*`; `ls -la` in a directory with odd permissions |
| Find the bug | Realistic code, config or command with a subtle flaw | A Dockerfile that busts the layer cache on every build |
| Read the signal | A log, error, stack trace or exit code; what happened, at which layer, what to do next | See `debugging-literacy.md` |
| Trade-off | "When would you *not* use X?" | "When is `rebase` the wrong choice over `merge`?" |
| Design under constraint | "Design X given these limits" | "Ship a 20 MB image for a Go service, with no shell in the final image" |
| Scale it up | "What breaks at 1000× the load?" | "Your `ls`-based backup script meets a directory of 10M files" |
| Follow-up chain | After any answer, ask the next "why" and "what if" an interviewer would ask | "OK, and what if the file is a symlink to a directory?" |

Mix types within every exercise set. Include at least one hands-on task the learner does on their machine.

## Making it fun

Recall works better when it doesn't feel like a test:

- **Scenarios**: "It's 3 a.m., you're on call, and this is the only log line you have…"
- **Combination tasks**: use something old inside something new. While learning bash scripting, "write a script that reports hidden files (`ls -A`) older than 7 days, sorted by size."
- **Puzzles and golf**: "Do it in one pipeline." "Do it without `grep`."
- **Break it on purpose**: "Make this container crash with exit code 137. Why 137?"
- **Speed rounds**: five rapid-fire questions across old units.
- **Reverse questions**: give the answer and have them write the question, or give the output and have them write the command.
- **Rewrite from memory**: a day or more after a program was written, the core part again from a blank file,
  no notes, timed; seed it for the examiner (`framework/rules/hands-on-coding.md`, section 6).

## Hint ladder

When the learner is stuck, don't reveal the answer straight away. Go one rung at a time:

1. Rephrase the question.
2. Point to the relevant concept ("think about what the stride of a pointer depends on").
3. Give a partial trace or a smaller version of the problem.
4. Walk through it together, then give them a fresh, similar question to prove it stuck.

On an engine item, count each rung with `--hints N` when you record the answer: the engine brings the topic back sooner.

## Grading

- Judge the answer on mechanism and correctness, not on wording.
- For half-right answers, name exactly which part is right and which isn't, then ask them to fix it.
- Wrong is fine. Wrong and unaddressed is not. A miss on an engine item is recorded with its kind (`mistake`) and comes back on the engine's schedule; a miss on a formative question is repaired on the spot and, if it shows a real gap, becomes a seed.

## Seeds, and the recall schedule

The engine keeps the recall schedule (FSRS) for every item; there is no `recall.md` any more. What you
keep is a short list of seeds per topic in `learner/coach/<topic>/seeds.md`: the question idea, its
type and the topic keys, **never an answer**:

```markdown
- predict-output · c-pointers/arithmetic, c-pointers/casts — reading an int through a char* advanced by 4,
  on a little-endian machine
```

Pass the new seeds to the `examiner` with the topics that need items ("stock `<skill>`; seeds for
`<key>` in `learner/coach/<topic>/seeds.md`"), then the ids it returns to the `checker`. An older
`recall.md` from before the engine took over is handed over the same way once, questions only (its
recorded answers stay where they are and are never pasted into a prompt), and then renamed
`recall.retired.md`.

How recall now runs:

- **Session openers**: `ask --due` two or three times before new material (the engine serves what is
  due, most forgotten first, from every skill).
- **Surprise recall**: at any natural pause mid-lesson, one `ask --due`, without warning, then carry on.
- **Unit exercises**: the engine's items for the unit's topics, mixed with reviews the engine weaves in.
- **Weak-spot loop**: if a unit's topics keep slipping back to `learning`, re-teach the unit from a new
  angle (`unit <skill> <topics>` shows where each one stands) before going further.
