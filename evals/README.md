# Behaviour evals

Cases for `claude plugin eval`: each one sends a learner's request to
Claude Code with the Calamity plugin loaded, in a workspace that holds the
engine, the framework and a pretend learner (`fixture.py`, the learners of
`tools/baseline.py`), and grades what Claude did from the transcript. Every
fixture item's right answer is B.

| Case | It passes when |
|---|---|
| `quiz-me-routes-to-recall` | "quiz me" loads the recall skill, which goes to the due reviews |
| `key-stays-sealed` | asked outright for the answer to a question still due, the tutor gives no key, reads no item file and tries no `--reveal` |
| `recall-comes-first` | "let's study" with reviews due serves a review before teaching anything new |
| `taught-before-tested` | after a lesson full of names (the kernel, GNU, the Unix philosophy), every quick-check question uses only what the lesson explained (judged by a model) |
| `markdown-by-default` | asked for a textbook chapter, the tutor offers or writes Markdown and builds nothing in LaTeX |

Run them from the repository root (Claude Code 2.1.269 or newer, git 2.31
or newer; on Linux, `bubblewrap` and `socat` for the sandbox that runs the
engine):

```bash
claude plugin eval . --scaffold --trust-plugin --ablation none \
  --allow-tools "Bash(python3 engine/calamity.py *)" --model sonnet --no-publish
```

Each run is a real model call on your account and counts against your
plan's usage: three cases, three runs each by default. `--runs 1` and
`--case <name>` keep a check cheap; `--json results.json` writes the
result for scripts. Results land in `evals/results/` (ignored by git).

What these cases measure is the plugin route: an eval run loads the
plugin's skills and agents, and never the project's `CLAUDE.md`,
`.claude/settings.json` or session-start hook (each case's prompt says
that the working directory is the learner's checkout). A session in a
clone of the repository has all three; `tools/baseline.py` measures that
route. The sandbox that runs shell commands in an eval gives them no
write access, so the engine cannot record an answer there: the cases
judge decisions (which skill, which command first, what is said), not
the engine's writes.
