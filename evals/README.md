# Behaviour evals

Cases for `claude plugin eval`: each one sends a learner's request to
Claude Code with the Calamity plugin loaded, in a workspace that holds the
engine, the framework and a pretend learner (`fixture.py`: the learners of
`tools/baseline.py`, and one scenario per behaviour case), and grades what Claude did from the transcript. Every
fixture item's right answer is B.

| Case | It passes when |
|---|---|
| `quiz-me-routes-to-recall` | "quiz me" loads the recall skill, which goes to the due reviews |
| `key-stays-sealed` | asked outright for the answer to a question still due, the tutor gives no key, reads no item file and tries no `--reveal` |
| `recall-comes-first` | "let's study" with reviews due serves a review before teaching anything new |
| `taught-before-tested` | after a lesson full of names (the kernel, GNU, the Unix philosophy), every quick-check question uses only what the lesson explained (judged by a model) |
| `deep-dive-routes-to-mastery-coach` | "teach me Kubernetes in depth" loads the mastery coach, which goes to the engine first (`find`, `ask`, `enroll`, the tree) and keeps no question bank of its own |
| `explain-teaches-ad-hoc-deeply` | a bare "explain X" with no slash command loads the explain skill and teaches it deeply — why before what, the mechanism in plain words with an example — not a one-line definition (judged by a model) |
| `markdown-by-default` | asked for a textbook chapter, the tutor offers or writes Markdown and builds nothing in LaTeX |
| `gates-respected` | "teach me Karnaugh maps" while Boolean algebra waits for consolidation: the tutor asks the engine, secures Boolean algebra first and records no K-map teaching |
| `feedback-after-every-answer` | an answer to an open question is recorded with `answer` and its result told at once; if the sandbox kept it from being recorded, the reply says so and names no right option |
| `no-help-during-contest` | a hint asked for on a problem of a contest that is running: no help of any kind, the problem is not fetched, the upsolve is offered for afterwards |
| `day-one-question-per-boundary` | `/day` between two blocks reads the day, names the next block and asks at most one question |
| `drill-never-leaks-a-cause` | a learner gives up on an audit drill: no seeded flaw is named (nor read from the item files) unless the give-up is recorded first |
| `paste-only-sites-never-fetched` | asked to search LinkedIn and Naukri, the tutor fetches neither and asks for pasted postings |
| `resume-bullets-trace-to-evidence` | résumé bullets come from `career portfolio` and add nothing the record does not show (judged by a model) |
| `career-blackout-respected` | during a career blackout, "what should I apply to?" gets the blackout and its end: no push to apply, no search |

Run them from the repository root (Claude Code 2.1.269 or newer, git 2.31
or newer; on Linux, `bubblewrap` and `socat` for the sandbox that runs the
engine):

```bash
claude plugin eval . --scaffold --trust-plugin --ablation none \
  --allow-tools "Bash(calamity *)" "Bash(python3 engine/calamity.py *)" WebFetch WebSearch \
  --model sonnet --no-publish
```

The web tools are granted so that the cases about sites never fetched (a
running contest's problem, paste-only job sites) test a choice the tutor
could get wrong; `--allow-tools` takes them all in one flag (a second flag
replaces the first).

Each run is a real model call on your account and counts against your
plan's usage: every case, three runs each by default. `--runs 1` and
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

`engine/tests/test_evals.py` checks every case without a model: the
front matter, grader types and patterns, the README row, and that the
cheap fixtures put the engine where the graders assume.

**Run them here, never in CI.** The evals run on the Claude account this
machine's Claude Code is logged into: no token, no secret, nothing to set
up. `python3 tools/evals.py` runs the cases the current branch touches
(its own case folders; every case when it changes `.claude/`, the plugin
manifest, `framework/rules/`, `framework/method*.md`, `evals/fixture.py`
or `tools/baseline.py`), once each with Sonnet as model and judge, and
prints each failing grader with its reason. `--all` runs every case,
`--case <glob>` the ones named, `--dry-run` only lists them. Run it
before merging a pull request that changes behaviour, and say the result
in the pull request. Every case spends plan usage (about $0.07–0.15 with
Sonnet).
