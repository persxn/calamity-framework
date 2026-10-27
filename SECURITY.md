# Security

## Reporting a problem

Please report anything that could harm a learner privately, through
GitHub's private vulnerability reporting: the **Security** tab of this
repository, then **Report a vulnerability**. Do not open a public issue for
it. You will get an answer, and a fix will be released and credited if you
wish.

## What this project does on a computer

Knowing the design makes it easier to see what would be a vulnerability.

- **The engine** (`engine/`) is a Python program that uses the standard
  library only. It reads and writes files inside the repository folder: the
  learner's record under `learner/`, and machine-local state under
  `.calamity/` (never committed). It runs no other program except a TeX
  engine when the learner asks for a PDF, and `python -m unittest` for
  `selftest`.
- **The network**: the engine contacts one service, the public Codeforces
  API (`codeforces.com/api`), and only when the learner links a handle and
  syncs. No password, key or cookie is involved. There is no telemetry.
- **Data files are data**: the replay snapshot in `.calamity/cache/` is
  JSON, validated against the log it was built from; nothing the engine
  reads is executed.
- **Practice items** are stored with their keys base64-encoded. That keeps a
  learner from reading a key by accident; it is not encryption, and is not
  meant to be.
- **Claude Code permissions**: `.claude/settings.json` pre-approves the
  engine commands and edits under `learner/` and `.calamity/tmp/`, asks
  before `setup` and before edits to `engine/`, `framework/` and
  `CLAUDE.md`, and denies reading item files, editing the event log,
  editing the two settings files themselves, and reading `.env` files,
  cookies and HAR files. Claude Code applies these rules only after the
  workspace trust prompt is accepted; deny rules hold even with permission
  prompts turned off.
- **The key guard** (`guard tool`, installed by `setup --hook` as a
  PreToolUse hook) also keeps item keys and the agents' worked answers out
  of searches and shell commands: `learner/items/` for everyone, the
  examiner's and the checker's scratch folders for everyone but their
  owner. It stops slips and instructions planted in a page or a file, not
  a determined person at the keyboard. `doctor` checks that it is
  installed and refuses what it must, and warns about scratch files older
  than a day; `clean tmp` removes them.
- **What runs without being asked**: nothing. The session-start hook and
  the key guard, the status line and the reminders are installed only by
  `setup --hook`, `setup --statusline` and a scheduler command the learner
  approves. The repository itself ships no hook.
- **The `calamity` alias** is written only by `setup --alias`, outside
  the repository: a marked block in
  `~/.zshrc` or `~/.bashrc` (`~/.bash_profile` on macOS), taken out again
  by `setup --remove-alias`. It starts Claude Code with
  `--dangerously-skip-permissions`, so sessions opened with it ask only
  where an `ask` rule above says to; `deny` rules and the key guard still
  refuse, and the `allow` rules no longer matter.
- **Study sources** are connected only by routes their terms allow. Tools
  generated for a source live in `learner/bridges/<source>/`, are explained
  before they first run, and never store credentials.

## In scope

For example: a way for data (a log line, a profile value, an item, a
pasted page, a Codeforces response) to make the engine or Claude run
something the learner did not approve; a key shown before an answer; the
engine contacting anything but the Codeforces API; credentials or learner
data ending up in a commit the learner did not ask for; a prompt in this
repository that tells Claude to bypass a site's terms or a permission.

## Out of scope

A learner reading their own item keys on purpose (they are encoded, not
encrypted); problems in Claude Code itself (report those to Anthropic);
anything that needs an attacker who can already write to the learner's
repository folder.
