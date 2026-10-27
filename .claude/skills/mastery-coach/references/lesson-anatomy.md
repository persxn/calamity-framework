# Lesson anatomy

One unit is taught as a sequence of chunks. Each chunk covers one idea and ends with a check. The parts below are the *content* of a unit. Deliver them across several conversational turns, never as one wall of text.

## The parts of a unit

1. **The hook.** A problem or puzzle the learner can't yet solve: "Why does `ls -l` show a size of 4096 for every directory?" or "Why does this C program print a different number each run?"

2. **Why it exists.** The pain this feature was created to remove, and what people did before it.

3. **Definition, twice.** First in plain language ("a pointer is a note that says where something lives, not the thing itself"), then the precise, technical definition with the correct terms. New vocabulary goes into the glossary.

4. **The author's lens: the mechanism.** How it actually works, at the depth set out in `curriculum-design.md`. Use:
   - ASCII diagrams of memory, data flow, process trees, packets and state machines
   - step-by-step traces ("cycle 1: the PC holds 0x400; the control unit…")
   - analogies, always followed by where the analogy breaks down

5. **Install and set up**, if this unit introduces something new. Cover the commands for the learner's OS, how to verify it worked, and what can go wrong.

6. **First use.** The smallest working example, run in the learner's own terminal or editor. Ask them to run it and paste the output, so you're looking at reality rather than assumptions.

7. **The full surface.** Every flag, option, parameter or variant this unit owns, grouped by purpose. For each one, give what it does, a one-line example, and when you would actually want it. Obscure ones get a niche real-world scenario.
   Example for `ls`, grouped:
   - *What to show*: `-a`, `-A`, `-d`, `-R`, `-I`/`--hide`, `--ignore-backups`
   - *How much detail*: `-l`, `-n`, `-g`, `-o`, `-i`, `-s`, `--author`, `-Z`
   - *Sizes*: `-h`, `--si`, `--block-size`
   - *Sorting*: `-t`, `-S`, `-X`, `-v`, `-U`, `-r`, `-c`, `-u`, `--sort`, `--time`
   - *Format*: `-1`, `-C`, `-x`, `-m`, `--format`, `-w`, `-Q`, `--quoting-style`, `-b`, `-N`
   - *Decorations*: `-F`, `-p`, `--color`, `--hyperlink`, `--indicator-style`
   - *Time*: `--time-style`, `--full-time`
   - *Links*: `-L`, `-H`, `--dereference-command-line-symlink-to-dir`
   Always build the list from the real `man` page or `--help` output on the learner's system. GNU and BSD/macOS versions differ, and that difference is itself worth teaching.

8. **Case studies and scenarios.** Three to five realistic situations, each needing a different part of the surface: "You're on a server with 2 million files in one directory and `ls` hangs. Why? (sorting needs every entry read first.) What do you run instead? (`ls -U`, or `find -maxdepth 1`.)" Teach *when to use what*.

9. **Gotchas and failure modes.** The traps, the surprising behaviour, the bugs people ship.

10. **Unit exercises.** See `questions-and-recall.md`.

## Chunking

- One chunk is one idea: usually one diagram's worth, or one group of flags.
- End every chunk with 1–3 quick check questions. If the answers are wrong or shaky, explain again *from a different angle* (a new analogy, a new diagram, a trace) instead of repeating yourself.
- **Taught before tested.** A check question, and any example inside it, uses only terms, commands and ideas this lesson has already defined (or that the learner showed they know). Read each question back word by word before asking: if it names something untaught ("the shell", `grep`), define it in the chunk first or ask something else. Close each chunk with the facts its questions rely on, so they can be answered at once.
- At natural pauses, ask whether they want to keep going or stop here. Update state either way.
- Long mechanisms (like the CPU descent) are a *sequence* of chunks across several turns. Give the learner a sense of where they are in it: "We've built a register. Next we wire registers to an ALU."

## Hands-on

- Prefer the learner running things on their own machine over you describing output. Ask for the output, then read it with them.
- Running safe, read-only commands in a sandbox to demonstrate is fine. Never run destructive commands on the learner's machine. Give them the command and explain it, and let them decide.
- For "break it" challenges, use throwaway directories, containers or VMs, and say so.
