---
name: sync
description: "Save the learner's progress to their own git repository and bring in another laptop's work: commit learner/, pull, rebuild, push. Use only when the learner asks to save, sync, back up, commit or push progress, or to set up their repository."
argument-hint: "[pull | push | setup]"
---

# Sync

Progress lives in `learner/`. Syncing it is plain git, done only when the
learner asks. Every git command that changes something will ask for their
approval; that is intended.

## First time: a repository of their own

Check what is there:

    git status --short --branch
    git remote -v

- **Not a git repository** (the framework was downloaded as an archive):
  `git init`, then commit the framework as it stands before any study log
  (`git add -A`, `git commit -m "Calamity framework <version>"`), then add
  the learner's repository as below.
- **`origin` is the framework's public repository**
  (`https://github.com/persxn/calamity-framework.git`): the learner's study
  log must not be pushed there. Help them create their own repository
  (private unless they want their progress public) and point `origin` at
  it, keeping the framework as `upstream` for updates:

      git remote rename origin upstream
      git remote add origin <address of their repository>
      git push -u origin HEAD

  With the GitHub CLI: `gh repo create <name> --private --source . --remote origin`
  after renaming the old remote.
- **No remote at all**: `git remote add origin <address of their repository>`
  and `git push -u origin HEAD`.

Never push to a repository the learner did not name.

## Every time

Commit first, pull second: git refuses to pull over uncommitted changes.

1. Make the snapshot current and check the record:

       python3 engine/calamity.py rebuild
       python3 engine/calamity.py doctor

   If `doctor` reports a failure, fix it before committing.

2. Commit the learner's files only:

       git add learner
       git status --short
       git commit -m "Study log <date>: <one line: what was studied>"

   Show `git status --short` to the learner before committing. Nothing
   under `.calamity/` or `.claude/settings.local.json` should appear; if it
   does, stop and fix `.gitignore`. Nothing to commit is fine: go on.

3. Bring in what was done on another laptop:

       git pull --no-rebase --no-edit

   Each machine writes its own event files, so the log itself does not
   conflict. If git does report a conflict in `learner/events/`, keep both
   sides (every line is one event). If the pull brought anything in, the
   merged `learner/PROGRESS.md` holds lines from both laptops until it is
   rebuilt:

       python3 engine/calamity.py rebuild
       python3 engine/calamity.py doctor
       git add learner
       git commit -m "Rebuild progress after merge"

   `rebuild` replays every event from both machines, so both laptops end
   up with the same schedule and the same file.

4. Push:

       git push

Confirm with one line: what was committed and where it went.

## What must never be committed

Passwords, cookies, tokens, API keys, `.env` files, course material. If
`git status` shows any such file, do not commit; tell the learner and
remove it from the index.

## On another laptop

Clone their repository, open Claude Code in it, and run
`/onboard machine` once. The profile and all progress arrive with the
clone; only the machine setup (hook, reminders, Codeforces cache) is local.
