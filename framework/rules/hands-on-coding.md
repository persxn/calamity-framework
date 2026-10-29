# Hands-on coding

Read this whenever the learner is asked to write, complete, extend or
reproduce code: a practice exercise while teaching, a `code` or `task`
item, a drill that asks for new code, a project milestone, a project boss,
a competitive-programming implementation. How to ask, judge and record is
`framework/method.md`; this file is how a coding exercise is handed over,
watched and closed.

The failure it prevents: pasting the finished program, or a finished
program with two easy cases left out, and calling the rest an exercise.
Reading a complete program feels like learning and builds very little;
writing the part that carries the idea is the exercise. **The learner's
hands write the parts that carry the idea, from a brief, never from your
code.**

## 1. The brief: what you hand over

Before the learner types, give these, in plain words first and code last.
On an engine item the stem is the brief: show it exactly as the engine
prints it, create the setup it describes, and add nothing that would be a
hint; the rest of this file (the watch, judging, the steps after a pass)
applies as written.

1. **What the program does.** A short paragraph: its purpose, its input,
   its output, and what it deliberately leaves out.
2. **The parts, in the order to build them.** For each function or part:
   - its job, in one or two sentences;
   - its signature in words ("takes the source text and a position; returns
     the next token and moves the position past it");
   - its prototype or stub, with an empty body and a `/* your code */`
     comment under the line that restates the job (never the steps).
3. **A sample run to match.** An input, the exact expected output, and one
   edge case (an empty input, the end of the text, a maximum size).
4. **The check you will run.** The build command with its flags, the test
   command or the expected-output comparison, so the learner can run it
   too.
5. **Hints, held back.** For each part prepare the three rungs of
   `framework/method.md` (restate the task; point to the idea; give the
   first step). Release one rung at a time, only when the learner asks or
   is plainly stuck (no progress over two watch events, or about ten
   minutes), and count them.

A brief for a lexer in C, shortened:

```c
/* token.h is given: the Token struct and the TokenKind enum. */

/* Returns the next token that starts at src[*pos] and moves *pos past it.
   Spaces, tabs and newlines before it are skipped. At the end of the text
   it returns a token of kind T_EOF and leaves *pos there. */
Token next_token(const char *src, size_t *pos)
{
    /* your code */
}
```

Sample run: `printf 'x1 = 42 + y;' | ./lex` prints
`ID(x1) ASSIGN NUM(42) PLUS ID(y) SEMI EOF`. Check:
`gcc -std=c11 -Wall -Wextra -fsanitize=address,undefined -o lex lex.c` and
the three sample files compared with `diff`.

## 2. What you may write, and what you never write

You may write the scaffolding: a file skeleton (includes, the types and
structs the topic does not teach, stubs with empty bodies and a comment
that restates each job, a `main` that only wires the parts together and prints), test
inputs and expected outputs, a Makefile or the build and run commands, a
test harness, and worked examples of a *different* problem (rung 0 below).

You never write the body of a part the learner is to write, a nearly
complete program whose gaps are the easy parts, or the fix after a failed
run (say what the check showed, not how to fix it). In a lexer lesson the
scanning loop and the token decisions are the learner's; the `Token`
struct may be given.

A full solution comes only after the learner's own working attempt is
recorded, or after they give up and the attempt is recorded as a fail
(`--result fail`, or on a practice exercise said plainly as one). Then
show it and compare it with theirs, line by line.

## 3. The faded ladder

Where an exercise starts is decided by evidence, not by a guess. Five
rungs, from most support to none:

| Rung | You give | The learner writes | When |
|---|---|---|---|
| 0, worked | a complete program for a *sibling* problem, its steps labelled by purpose ("skip blanks", "read a number"); the learner predicts its output before it runs | nothing new: predicts, traces, then changes one thing | the first chunk of a topic, when the record shows nothing like it written |
| 1, completion | the brief and a skeleton with the **core** steps blank, faded from the end: first the last step, then the last two | the blank core steps | after rung 0, or after a fail at rung 2 |
| 2, stubs | the brief, the signatures and empty stubs | every body | the default for "write a program" |
| 3, spec | the brief without signatures | the design (the parts and their signatures, reviewed before coding), then the bodies | after a clean pass at rung 2 on the topic |
| 4, from memory | the task's name and the sample run; a blank file, no notes, timed | all of it | a day or more after a pass (section 6) |

Move up a rung after a clean pass (no hints), down one after a fail or two
or more hints, and say which rung an exercise is on. Do not keep a learner
on rungs 0 and 1 once the record shows they can do rung 2: support that
helps a beginner gets in the way of someone further on. Note the rung and
how it went in the coach log or with
`calamity observe "rung 2, lexer: pass, one hint" --topic <key>`.

## 4. Predict, then run

Before any program runs, the tutor's example or the learner's own code,
the learner says in one line what it will print (or, for a broken build,
what the compiler will say). Then run it. A wrong prediction is the lesson:
trace it with a table (line, each variable, the output so far) until the
gap is found, before any fix.

## 5. The live watch

When the learner writes in a file rather than in the chat, watch the file
and make short suggestions as they work.

1. **Agree the file.** `learner/work/<skill>/<exercise>/<file>` (the
   skeleton goes there, written with the Edit or Write tool). Tell the
   learner the watch is on, that you will look about every 30 seconds and
   say at most one short thing, and that "quiet" turns it off.
2. **Arm the Monitor tool** with
   - `command`:
     `python3 framework/scripts/watch.py learner/work/<skill>/<exercise>/<file>`
     (on Windows the interpreter the brief's engine line uses: `python` or
     `py -3`), optionally with `--check "<a cheap check>"`;
   - `description`: `changes to <file>`;
   - `timeout_ms`: `1800000` (the 30-minute cap).

   The script reads the file every 30 seconds (`--every N` changes that),
   compares content hashes, and prints one line per change, such as
   `19:02:11 changed lex.c: +6 -1 lines from line 40 (now 88); check: exit 0`.
   A save that changes nothing prints nothing. `--check` runs one command
   after each change: only a cheap one that writes nothing in `learner/`
   (`gcc -fsyntax-only -Wall -Wextra <file>`, or a build into
   `.calamity/tmp/watch/`); never an item's check, which is run once, when
   the learner says they are done; never anything under `learner/items/`.
3. **On each event**, read the file with the Read tool, then say **one**
   thing in at most three lines:
   - the next step ("`next_token` handles names; numbers next");
   - a bug, named by its line and the idea behind it, not fixed ("line 52:
     what happens to `*pos` when the loop reaches the end of the text?");
   - or a question that makes them check their own reasoning.

   Never the corrected code, never two points at once, never a suggestion
   repeated before they have acted on it. If nothing meaningful changed (a
   comment, spacing, a half-typed line, work going the right way), say
   nothing more than "noted".
4. **Hints count.** On an engine item, a suggestion that points to the
   idea, names a bug or gives a step is a hint rung (`--hints N`); a
   question or a build status is not. There is no watch at all during a
   boss test, a placement test, anything timed under exam conditions or a
   rated contest; on a project boss, only if the learner asks, and then it
   reports only the build status.
5. **Re-arm and stop.** The monitor ends after 30 minutes with one notice:
   arm it again if the exercise goes on. When the exercise ends (done,
   given up, another topic, the session's close), stop it with TaskStop.
   One watch at a time. Where the Monitor tool is not available, ask the
   learner to say "look" when they want a suggestion, and read the file
   then.

## 6. Judge, record, then make it stick

1. **Judge by running it.** On an item, `calamity item show <item> --check`,
   run the check for real, and record
   `calamity answer <item> --result pass|fail --evidence "what ran, what happened" --hints N`
   (with `--err <kind>` on a fail), as `framework/method.md` says. On a
   practice exercise, run the sample and the edge case in front of the
   learner.
2. **After a pass, one step deeper** (take a different one each time):
   - *explain your code*: you pick two lines; the learner says why each is
     there and what breaks without it;
   - *change a requirement live*: "now hexadecimal numbers too";
   - *break it*: you name one small change (flip a comparison, drop a
     line); the learner predicts which test catches it, then runs the
     tests.
3. **Write it again from memory.** A program learnt once is forgotten like
   any fact. After a code topic passes, add a seed for a rung-4 item to
   `learner/coach/<topic>/seeds.md` (deep coaching), or pass it to the
   `examiner` with the next stocking: "rewrite-from-memory · `<key>` —
   write `<program>` from a blank file to match this sample run, no notes".
   The examiner writes it as a `code` item, the checker verifies it, and
   the engine brings it back on its own schedule. A five-minute rewrite of
   the core part from memory also makes a good opener for the next
   session's recall.
