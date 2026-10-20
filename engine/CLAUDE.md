# Working on the engine

Claude Code loads this file only when a session reads or edits files in
`engine/`, so learners' study sessions do not pay for it.

- The engine uses the Python standard library only, supports Python 3.9+
  and runs on Linux, macOS and Windows. Do not install packages for it. Its
  only network use is Codeforces' public API when a learner syncs.
- The event log (`learner/events/`) is the single source of truth:
  append-only, and replay gives the same state whatever order files and
  lines arrive in. Anything cached (`.calamity/cache/`) must be disposable
  and proven equal to a full replay (`doctor` compares them).
- A command that is quoted in any document must exist:
  `engine/tests/test_docs.py` checks every document listed in its
  `documents()` and in `framework/MAP.md`.
- Tests that create learner data run in a temporary copy
  (`engine/tests/helpers.py`, `Sandbox`; the engine honours
  `CALAMITY_ROOT` and `CALAMITY_NOW`). Nothing personal goes into the
  repository.
- After any engine change: `python3 engine/calamity.py selftest`, then
  `python3 tools/e2e.py` for a change to replay, sync or the session loop.
