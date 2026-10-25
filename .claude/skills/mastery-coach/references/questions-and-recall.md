# Questions and recall

## The coverage rule

Every question must be answerable from material already taught in this curriculum, or confirmed known at intake. Before asking, check which units the question draws on, and confirm in state that they're `done` or `in-progress` and already covered. If a strong interview question needs something not yet taught, teach that piece first and then ask. A question about untaught material only tests luck, and it damages the learner's trust in the curriculum.

Record the unit IDs each question draws on in the recall bank.

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

## Hint ladder

When the learner is stuck, don't reveal the answer straight away. Go one rung at a time:

1. Rephrase the question.
2. Point to the relevant concept ("think about what the stride of a pointer depends on").
3. Give a partial trace or a smaller version of the problem.
4. Walk through it together, then give them a fresh, similar question to prove it stuck.

Mark the item in state as solved with hints, which makes it due for recall sooner.

## Grading

- Judge the answer on mechanism and correctness, not on wording.
- For half-right answers, name exactly which part is right and which isn't, then ask them to fix it.
- Wrong is fine. Wrong and unaddressed is not. Every miss goes into the recall bank.

## The recall schedule

Keep a recall bank in state (`recall.md`). Each item records:

```markdown
- id: R042 | units: U03,U07 | type: predict-output
  q: "char *p = (char*)arr; p += 4; what does *(int*)p read on a little-endian machine if arr = {1, 2}?"
  history: 2026-10-20 ✗ (hints 2) · 2026-10-22 ✓
  next_due: 2026-10-29
```

Spaced intervals after a clean correct answer: 1 → 3 → 7 → 14 → 30 → 60 days. Any miss resets the item to 1 day. An answer that needed hints counts as half a step.

How to use it:

- **Every unit's exercise set** includes items due from the bank, mixed in without being labelled as recall.
- **Surprise recall**: at any natural pause mid-lesson, drop one cold question from an older unit, without warning, then carry on. Pick items that are due, weak, or old.
- **Session openers**: start each session with 2–3 due items before new material.
- **Weak-spot loop**: if a unit's items keep failing, mark the unit `needs-review` and re-teach it from a new angle before going further.
