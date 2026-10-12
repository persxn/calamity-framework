# Changelog

All notable changes to the Calamity Framework. The version is in
`framework/VERSION`; learners update with `/update-framework`, which never
touches their data.

## 1.0.0 (2026-10-12)

The first public release.

### The learning system

- Sixteen skills (slash commands) and eight agents for Claude Code: a study
  loop with surprise recall, small chunks tested at once and earlier skills
  woven into new exercises; onboarding; dashboards; notes; syncing;
  reminders; updates.
- An adaptive tutor over a skill tree of 150 skills and 418 shipped topics
  in six tracks: the developer path (`10x`), AI engineering (`ai`),
  competitive programming (`cp`), and GATE (`gate`, `gate-cs`, `gate-da`).
  Routes to a goal, skills that can run side by side, alternatives (slots),
  placement tests, mastery and brush-up modes, and skills added or dropped
  per learner.
- A GATE companion: GATE 2027 facts from the official site (checked
  2026-10-12), subjects for the CS and DA papers, triage by marks per hour,
  a plan back from the exam date, the exam's marking in practice and timed
  tests, mocks and their review, a final phase that gives every topic one
  last review before the exam.
- A competitive-programming coach that reads a Codeforces handle through
  the public API: tag analysis, practice sets above the rating with tags
  hidden, upsolving, contests, rating milestones, judged solves credited as
  evidence.
- Practice items written by one agent and verified blind by another before
  a learner sees them; keys stay sealed until an answer is recorded.
- Notes per topic, LaTeX sections and one PDF per skill (Tectonic, TeX Live
  or MiKTeX).

### The engine (`engine/calamity.py`)

- Python standard library only, Python 3.9 or newer, Linux, macOS and
  Windows; tested on all three with Python 3.9 to 3.15.
- An append-only event log per machine and month, replayed on every command
  into the same state whatever order files and lines arrive in; git merges
  between laptops without conflicts.
- FSRS-6 review scheduling (a port of py-fsrs 6.3.2, checked number for
  number), a daily finish line instead of points or streaks.
- A replay snapshot that a command may start from instead of the whole log,
  proven equal to a full replay by the tests, the fuzzer and `doctor`.
- Safe under concurrent commands (an inter-process lock), damaged log lines
  and bad settings (reported, never fatal), Windows file locks and code
  pages.
- Optional session-start hook, status line and operating-system reminders,
  installed only when asked and removable with one command.

### Development

- 221 unit tests (`selftest`), an end-to-end run of two laptops and a
  framework update (`tools/e2e.py`), a fuzzer (`tools/fuzz.py`), sample
  output from pretend learners (`tools/demo.py`), and continuous
  integration on Linux, macOS and Windows.
