# Changelog

All notable changes to the Calamity Framework. The version is in
`framework/VERSION`; learners update with `/update-framework`, which never
changes their record in `learner/`.

## Unreleased

### The learning system

- The AI Engineering track is built out: maths, ML, LLMs, agents,
  inference, training and infrastructure, with milestones; `10x/cpp`
  joins the developer path. The four shapes a skill file can take are
  documented in `framework/rules/tree-editing.md`.
- Deep teaching is the default on every path. A depth contract (the
  problem and its history, intuition, inner mechanics, examples, case
  studies, flags and how they combine, trade-offs) and a doubt check before
  teaching; syllabi, items and the examiner aim at the mechanism and the
  trade-off rather than recall. The teaching standard lives in
  `framework/method-teaching.md` and loads only when a session teaches;
  `framework/method.md` keeps the loop, asking, judging and modes. Study's
  `NEXT: new` teaches a topic's whole arc across chunks.
- Companion skills with a loop of their own: `mastery-coach` (deep
  coaching of any tool or topic: history and philosophy first, a
  gap-free roadmap, interview-grade drills and surprise recall),
  `mastery-textbook` (a LaTeX study book that grows with the coaching,
  compiled to PDF) and `build-it-yourself` (learn a project by rebuilding
  or designing it and shipping it yourself). Their state lives in
  `learner/mastery/`; `PLUGINS.md` draws the line between them, the
  engine and the notes skill.
- A plugin scaffold: `.claude-plugin/plugin.json` and `marketplace.json`
  describe Calamity as a plugin; using the repository as a project is
  unchanged.
- `tools/timetable.py`: a terminal day planner over `learner/schedule.md`,
  with goals, notes and per-day overrides in `learner/timetable.json`.
- The day has one format and one parser. `learner/schedule.md` keeps its
  blocks in the front matter (`weekday`, `weekend`, optionally `mon` ...
  `sun`). `day` shows a day with the current block, its note and goals
  and the finish line. `day note`, `day goal` and `day done` replace hand
  edits of `learner/timetable.json`, and the brief says which block a
  session falls in (`Now:`). `day migrate` converts the earlier table
  format. `tools/timetable.py` reads its blocks from the engine, works
  on its own checkout, never runs `sudo`, and `timetable install` adds a
  launcher in `~/.local/bin` only when asked.
- Mastery Gate v2: progress is paced by evidence. A topic is
  `consolidating` once it is answered right on a second item at least 20
  minutes after the first, and it must be consolidated before it is
  solid. A topic opens only when what it builds on is consolidated (GATE:
  answered right on a verified item); an oral check opens nothing. At most
  two topics per skill are open at once (GATE three, brush-up four);
  `next` then says `consolidate` and new material comes from another
  lane. The finish line counts consolidated topics, and accuracy for
  `solid` counts only answers that are evidence. Pace profiles in
  `framework/config.md` (`pace.mastery`, `pace.exam`, `pace.brushup`,
  `pace.track.<track>`) can be overridden per learner.
- Study books and long-form notes are Markdown by default (from learner
  feedback: writing and reviewing LaTeX was slow and costly). The brief
  asks once for `book.format` (`markdown` or `pdf`). `notes assemble`
  writes `<skill>-notes.md`, `mastery-textbook` writes a chapter per
  Markdown file, and `framework/rules/markdown-books.md` sets the house
  style. A PDF comes only on request, from the engine: `book pdf <file
  or folder>` and `notes pdf` convert the Markdown themselves, so no
  model writes LaTeX for it. The typeset LaTeX edition stays for
  learners who choose `pdf`.
- Taught before tested (from learner feedback: a check asked about "the
  shell" and used `grep` before either was taught). A question or
  example uses only what the lesson has explained or the record shows,
  and each chunk ends with the facts its check relies on. The rule is
  in the teaching standard, the tutor style, mastery-coach, the examiner
  (vocabulary of the topic and what it builds on) and the checker
  (rejects an item that leans on an unexplained term).
- Objectives, coverage and the three strands. Syllabus objectives can be
  tagged `[T]` theory, `[P]` practice, `[I]` implementation or `[N]`
  numerical. `NEXT: new` lists every objective, numbered (it used to cut
  off after four). Items name the objectives they test (`objectives` in
  a draft, or `item tag`), and the NEED_ITEM block says which are not
  yet answered right on. Once items are tagged, `solid` needs 60% of a
  topic's objectives and `mastered` all of them, and consolidation needs
  another objective; untagged items count as before. `tree show` prints
  coverage per topic and the strand shares per skill. `syllabus check`
  flags unknown tags and objectives rewritten under tagged items.
- The daily quota of new topics adapts. It starts from the pace profile's
  maximum (6 mastery, 8 exam, 10 brush-up; `new_per_day_max` to set it,
  `new_per_day` still read) and shrinks while the next week's review
  forecast nears `review_budget_min` (60 minutes) or first tries on new
  topics go wrong. `today` and the brief print the reason in one line;
  `quota.adaptive false` keeps it fixed.
- Teaching telemetry. `ask --topic K --taught --parts model,example,...
  --minutes N` stores what was taught and for how long on the same event,
  `day` shows it, and a warning (never a block) names the parts a topic's
  level asks for that were left out. `feedback pace=slow depth=more
  clarity=low --topic K` records the learner's word on the teaching.
- Item families and nightly stocking. `item needs --days 2 --per-topic 3`
  simulates the next days' plan and lists, per topic, how many more items
  to write, the drafts waiting for the checker and the objectives no item
  tests yet. The examiner writes families of 3 to 5 across objectives and
  depths (at most 8 topics a run) and keeps a local memory of the
  checker's rejection patterns, never learner data. The `/stock` skill
  (never invoked by the model) runs examiner then checker; `stock render
  --at 23:45` writes an opt-in scheduler entry for a headless `claude -p
  "/stock"` with its tools limited to the engine, the agents' scratch and
  the web, started only when there is work, logging to `.calamity/logs/`.
- `source show <id>` reads a source in slices (its sections, or the
  lectures of a section, a topic or a skill, or those unmapped, at most
  `--limit`), and the curriculum-architect maps lectures with it instead
  of reading the whole file. Its new task deepens a shipped GATE syllabus
  subject by subject, keeping every topic id. `syllabus check` refuses a
  learner syllabus that drops an id that lectures, items or the record
  use, and warns when one leaves out a shipped topic.
- Practice sets, for questions from outside material: `practice add`,
  `map`, `log`, `due`, `status` and `stats`, and the `/practice` skill.
  Only metadata is kept (question numbers, topics, pages), never a
  question's text. Every question comes back: wrong, guessed or skipped
  after 2, 7 and 21 days, solved after 10 and 30, retiring after two
  right revisits in a row; `next` serves revisits after due reviews and
  before new material. A set with an official key (previous GATE papers)
  credits its topics as evidence; other sets only schedule them.
- GATE revision. `gate pass <subject> <n> --planned DATE | --done`, shown
  in `gate status`; the gate-strategist plans at least two passes for at
  least five subjects. `gate numericals` counts numerical questions solved
  per topic with `[N]` objectives against `numericals.target` (10), and
  the `numericals-low` pattern raises the one furthest behind, casually
  and at most once in three days. `source revise` lists watched lectures
  whose topics have faded below 85% recall. `log ... --at ISO` and `log
  <source> --file ticks.json` keep the real tick times, and the `log`
  skill syncs the course tracker with them. `gate pack <subject> [--pdf]`
  writes a revision pack: a formula sheet from the notes' `## Formulas`
  sections and an error book of recorded mistakes, with no item keys.
- Mock scouting. The `opportunity-scout` agent (web only,
  `omitClaudeMd`, 40 turns) has one beat, `gate-mocks`: the official mock
  test, all-India series and offline centres near `location.city`
  (asked once). It reads robots.txt and the terms before fetching and
  never fetches a disallowed site. Records go through `career add`, which
  refuses one without a source, fetch date and terms note; `career list`
  and `career show` read them, and the gate-strategist places them in the
  mock calendar.

### Development

- Continuous integration is green on every system again: the alias test no
  longer runs on Windows, where the WSL `bash.exe` launcher defeated its
  skip. One aggregate check, `ci-ok`, is what branch protection requires;
  a newer push cancels the older run; pull requests run once instead of
  twice; the actions are pinned to commit SHAs.
- Study records stay out of the framework repository: git hooks in
  `tools/git-hooks/` (`git config core.hooksPath tools/git-hooks`) refuse
  to commit `learner/` files in a clone of the framework and to push a
  study record to it from any clone; the self-test checks that the
  framework tracks only `learner/README.md`. `CONTRIBUTING.md` and the
  sync skill describe the two clones: a dev clone of the framework, and a
  study clone whose `origin` is the learner's private repository.
- One version: `framework/VERSION` is the source, and a test holds the
  plugin manifests to it (they said 0.1.0). The documents no longer quote
  counts of skills or agents that drift as the tree grows, and
  `tools/e2e.py` counts the shipped skills from the tree.
- The key seal holds beyond the Read tool: `guard tool`, a PreToolUse hook
  that `setup --hook` installs with the session brief, refuses
  `learner/items/` to everyone and each agent's scratch to everyone but
  its owner, in reads, searches and shell commands. The examiner works in
  `.calamity/tmp/examiner/<batch>/`, which `item import` deletes once
  stored; the checker in `.calamity/tmp/checker/<item>/`, deleted once its
  result is recorded. `doctor` checks the guard and warns about scratch
  older than a day; `clean tmp` empties it. Permissions: the coach,
  timetable, practice and career files can be edited without a prompt,
  and Claude can no longer edit `.claude/settings.json` or
  `.claude/settings.local.json` itself (deny rules hold in every mode).
- Token and behaviour baselines: `tools/tokens.py` reads Claude Code's
  transcripts (per session, per skill, per agent, the largest tool
  results; numbers only), `tools/baseline.py` runs three scripted
  sessions with pretend learners and measures them, and `evals/` holds
  three cases for `claude plugin eval` (routing, key secrecy, recall
  first). `docs/maintainers/token-baseline.md` records the results.
||||||| parent of 4f12bc4 (A slim CLAUDE.md and the Calamity Tutor output style)
- `CLAUDE.md` is down from 5,197 to about 2,200 characters. It keeps the
  session start and the rules that never bend, which agents load too. The
  tutor's teaching rules and the engine's command form moved to the
  output style `.claude/output-styles/calamity-tutor.md`, which
  `setup --hook` selects (a style the learner chose is kept). It replaces
  Claude Code's software-engineering instructions in study sessions.
  The skills and agents are registered in `framework/MAP.md`, and the
  self-test checks the registry: adding a skill no longer pushes
  `CLAUDE.md` over its size limit. `doctor` reports the output style.

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
- Skill-tree rules that keep routes short: a topic can wait for a single
  topic of another skill (`needs: [cp.trees/subtree-dp]`) instead of the
  whole skill depending on it; with a linked Codeforces handle, topics
  banded well above the learner's rating wait, and a skill's boss does not
  wait for them; Codeforces tags point to the skill that teaches them at
  the learner's rating; game theory and geometry are optional.
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

### Review fixes and additions before release

- Teaching starts from the basics: `NEXT: new` prints the topic's level,
  what it builds on, its objectives and where to start (from zero for a
  skill's first topic); `ask --taught` notes topics taught out of order;
  the method, the study skill and the syllabus rules say so.
- A suggested `/model` and `/effort` for the next block, one line from the
  engine at no model cost (brief, `today`, `next`, `item needs`, status
  line); judgement, not measured; `cfg.advice.*` overrides, `cfg.advice
  false` turns it off.
- Fewer tokens: `CLAUDE.md` no longer imports the method (the study,
  recall, boss, gate and cp skills read it); maintainer notes in
  `engine/CLAUDE.md`; `/today` makes one call; Codeforces sync once per
  session; the PDF is built once; `today` suggests a fresh session at the
  finish line; `answer --next` records a right answer and serves the next
  question in one call; the CP and GATE playbooks are split into
  onboarding, planning and daily files, each read only when needed.
- Engine: a torn character in a log line costs that line only; dispute and
  restore follow an item's history; renamed topics answer and rename back
  correctly; bad ids, offset-less times, damaged snapshots, non-UTF-8
  learner files and odd profile values give messages, not tracebacks; the
  snapshot key matches the bytes replayed; the write lock gives up after 15
  seconds on every system; the examiner never verifies.
- Reminders: `remind remove` (no times needed), a per-clone tag, Windows
  tasks that run on battery and catch up, PowerShell scripts with a BOM,
  ASCII-only `.cmd` files, `mkdir -p ~/Library/LaunchAgents` on macOS.
- Windows: the engine command is test-run before it is named; the status
  line uses short paths when a path has spaces.
- `setup --alias` (Linux and macOS, bash or zsh): typing `calamity` in a
  terminal goes to the framework's folder and starts
  `claude --dangerously-skip-permissions`; onboarding offers it, `doctor`
  checks it, `setup --remove-alias` takes it out.

### Development

- Unit tests (`selftest`), an end-to-end run of two laptops and a
  framework update (`tools/e2e.py`), a fuzzer (`tools/fuzz.py`), sample
  output from pretend learners (`tools/demo.py`), and continuous
  integration on Linux, macOS and Windows.
