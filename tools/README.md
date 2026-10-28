# Development tools

Checks that go beyond the unit tests. None of them is needed to study with
the framework, and none touches this checkout: each works in a temporary
folder and removes it afterwards. Standard library only, like the engine.

| Tool | What it checks | Typical run |
|---|---|---|
| `tools/e2e.py` | The whole framework as two laptops use it: onboarding, syllabi, items made and checked, study, a woven exercise, a GATE course, Codeforces from recorded data, notes and a PDF (when a TeX engine is installed), dashboards, two laptops merging through git, and a framework update for a clone and for a copy that began as an archive. Needs git. | `python3 tools/e2e.py` (about a minute) |
| `tools/fuzz.py` | Random command sequences: no command may crash, the state served through the replay snapshot must equal a full replay after every step, and each run's events must replay to the same state from shuffled files. | `python3 tools/fuzz.py --runs 20 --steps 60` |
| `tools/demo.py` | Produces the sample output shown in the README and the guides, from pretend learners in a temporary copy of the framework. | `python3 tools/demo.py --out /tmp/calamity-samples` (a folder outside the checkout) |
| `tools/bench.py` | Times commands on a long log, with and without the replay snapshot. | `python3 tools/bench.py <learner repository> --events 50000` |
| `tools/tokens.py` | Token use of Claude Code sessions in a checkout, read from their transcripts: per session (the first request's context is the fixed cost of every request), per skill, per agent, and the largest tool results. Numbers and names only, never content. Read-only. | `python3 tools/tokens.py --skills` |
| `tools/font_samples.py` | The same notes page (headings, terms, definition, key-idea and pitfall boxes, GATE maths, a table, code, recall) set in each candidate font family for the Calamity Paper design system (WP-27, D12), with every TeX engine installed; a PNG per page and one combined PDF. | `python3 tools/font_samples.py --out /tmp/fonts` |
| `tools/baseline.py` | Three scripted sessions (a recall round, a two-topic study block, a weekly review) with pretend learners in throwaway copies, measured with `tools/tokens.py`; `docs/maintainers/token-baseline.md` keeps the results. It runs Claude Code headless and spends plan usage, so it is run by hand, never in CI. | `python3 tools/baseline.py --model sonnet` |
| `tools/evals.py` | The behaviour evals in `evals/` through `claude plugin eval`, on the Claude account Claude Code is logged into (no token): the cases the branch touches, or `--all`, or `--case <glob>`; once each on Sonnet, with each failing grader and its reason. It spends plan usage, so it is run by hand before merging a behaviour change, never in CI. | `python3 tools/evals.py` (`--dry-run` lists the cases) |

`evals/` holds the behaviour cases (`evals/README.md` lists them);
`tools/evals.py` runs them. Like `tools/baseline.py` they call the model,
so they are run by hand.

On Windows use `python` or `py -3` instead of `python3`.

## Git hooks

`tools/git-hooks/` keeps study records out of the framework repository:
`pre-commit` refuses files under `learner/` (other than its README) when
`origin` is the framework, and `pre-push` refuses to push a study record to
it from any clone. Turn them on once per clone with
`git config core.hooksPath tools/git-hooks`; `CONTRIBUTING.md` explains
the two clones they are meant for.

## Companion tool

`tools/timetable.py` is not a check — it's a learner-facing day planner. Run
it in a terminal and it opens a curses TUI: move through the day's
time-slots, attach goals to a slot, add unscheduled goals, tick them off, move
between days with ← →, and leave a note on any day (an exam, an event, time
that will be lost) that Claude can then read. The blocks come from the engine
(`python3 engine/calamity.py day <date> --json`, which reads
`learner/schedule.md`); goals, notes and date-specific shifts live in
`learner/timetable.json` (so they sync with the learner's progress). Without
a terminal, or where curses is missing (Windows), it prints the day instead;
`timetable help` lists the scripting subcommands. It works on the checkout it
belongs to (or `CALAMITY_ROOT`). `python3 tools/timetable.py install` puts a
`timetable` launcher in `~/.local/bin` and prints the line that puts that
folder on the PATH for bash, zsh or fish; nothing else is installed.

Continuous integration runs the unit tests (`python3 engine/calamity.py selftest`)
on Linux, macOS and Windows with every supported Python, and `tools/e2e.py`
and a short `tools/fuzz.py` on each system. Run a longer fuzz before a
release and after any change to how the log is replayed.

A fuzz failure prints its seed: `python3 tools/fuzz.py --first <seed> --runs 1`
repeats it exactly.
