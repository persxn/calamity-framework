# Contributing

Thank you for helping. The framework is three things that must keep
agreeing with one another: the engine (`engine/`), the prompts Claude reads
(`CLAUDE.md`, `.claude/skills/`, `.claude/agents/`, `framework/rules/`)
and the skill tree (`framework/tree/`). The tests check that they do.

## Set up

There is nothing to install. You need Python 3.9 or newer and git.

```bash
git clone https://github.com/persxn/calamity-framework.git
cd calamity-framework
python3 engine/calamity.py selftest
python3 engine/calamity.py doctor
python3 engine/calamity.py tree check
```

On Windows use `python` or `py -3` instead of `python3`.

Work on the framework in a checkout that holds no study record of your own:
`learner/` must ship with nothing but `learner/README.md`. If you also
study with Calamity, do it in a second clone whose `origin` is your own
private repository (the sync skill sets one up) and whose `upstream` is the
framework.

Turn on the git hooks once per clone:

```bash
git config core.hooksPath tools/git-hooks
```

In a clone whose `origin` is the framework repository (or a fork: any
repository named `calamity-framework`), `pre-commit` refuses staged files
under `learner/` other than `learner/README.md`. In every clone,
`pre-push` refuses to push commits that add a study record to such a
repository, so `git push upstream` from a study clone cannot publish one.
Git runs them with its own `sh`, Git for Windows included. The self-test
checks the same rule: in a clone of the framework, `git ls-files learner`
lists `learner/README.md` alone.

## Before you open a pull request

| Check | Command |
|---|---|
| Unit tests, including the documents lint | `python3 engine/calamity.py selftest` |
| The skill tree | `python3 engine/calamity.py tree check` |
| The whole framework end to end (needs git) | `python3 tools/e2e.py` |
| Replay under random commands, after a change to the engine's state or log | `python3 tools/fuzz.py --runs 20 --steps 60` |

Continuous integration runs the unit tests, the tree check and `doctor` on
Linux, macOS and Windows with Python 3.9 to 3.15, and the end-to-end run
and a short fuzz on each system. See `tools/README.md` for what each tool
does.

## Rules the code keeps

- **Standard library only**, Python 3.9 or newer, Linux, macOS and Windows.
  No dependency, ever, for the engine.
- **The event log is the only source of truth.** It is append-only, and
  replaying it must give the same state whatever order files and lines
  arrive in. Anything derived and stored (the replay snapshot) must be
  disposable and proven equal to a full replay; `tools/fuzz.py` checks this
  after every step.
- **Every file write goes through `store.write_text`** (atomic, LF, UTF-8);
  appends to the log go through `Repo.append` (locked). A test fails if a
  module writes a file any other way.
- **A user's mistake is an error message, not a traceback**: raise
  `CalError` with what to do next. Exit codes are documented in
  `framework/rules/engine.md`.
- **Every fix comes with a test that fails without it.**
- No network use except the Codeforces API, and no telemetry.

## Rules the documents keep

- Every engine command quoted in a document must exist with the flags
  shown. `engine/tests/test_docs.py` checks the README, `docs/`, the rule
  books, the skills, the agents and this file. A new document goes into its
  `documents()` list and into `framework/MAP.md`.
- A new command or flag is documented in `framework/rules/engine.md`.
- Facts that change (exam dates, Claude Code's installation, the Codeforces
  API) are taken from the official source and dated.
- No counts that drift: say "the skill tree", not "164 skills".
- `framework/VERSION` is the version. A release changes it together with
  `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`; a test
  holds them equal.
- Sample output comes from `tools/demo.py` and is labelled as coming from a
  pretend learner.
- No points, streaks or other gamification: the daily finish line is a
  deliberate design decision.

## Adding a skill to the tree

1. Search first: `python3 engine/calamity.py find <words>`. It may exist
   under another name.
2. Create `framework/tree/<track>/<id>.md` in one of the four shapes in
   `framework/rules/tree-editing.md` (taught skill, milestone, competitive
   programming, or GATE subject): the shared front matter plus the shape's own
   fields, then its sections (for a taught skill: `# Scope`, `# Boss` with
   checks that can be run, and `# Topics` if it ships a syllabus).
3. Run `python3 engine/calamity.py tree check` and the self-test.

## Changing a skill, an agent or a rule book

Keep them short: what Claude reads every session costs tokens on every
turn. Skills and agents run each engine command on its own, in the form
`python3 engine/calamity.py ...` from the repository root, because that is
the form `.claude/settings.json` pre-approves.

## Commits and pull requests

Small, focused pull requests with a message that says why. Never include
anyone's `learner/` data, `.calamity/`, `.claude/settings.local.json`,
credentials or course material.

By contributing you agree that your contribution is licensed under the MIT
licence in `LICENSE`.
