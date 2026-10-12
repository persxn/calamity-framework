# Syncing, devices and your data

## What lives where

Everything about you is under `learner/`: your profile, your day shape, the
event log of everything you did, your practice questions (keys sealed),
your syllabi, your study sources, your notes and your work. It is all plain
text. The rest of the repository is the framework, the same for everyone.
`learner/README.md` describes each folder.

Some things stay on each computer and are never committed: the machine id,
the replay snapshot and other caches, the Codeforces cache, reminder files
(all under `.calamity/`), and the hook and status line in
`.claude/settings.local.json`.

## Your own repository

To keep your progress safe and use it on more than one computer, push it to
a git repository of your own, **private** unless you want your study log to
be public. Ask: "sync my progress", or `/sync`.

The first time, Claude sees that `origin` is the framework's public
repository and must not receive your study log. It helps you create your
own repository (on GitHub: `gh repo create <name> --private`), renames the
framework's remote to `upstream` (kept for updates) and points `origin` at
yours.

Every time after that:

1. `rebuild` refreshes `learner/PROGRESS.md` (a readable snapshot that
   shows on GitHub) and `doctor` checks the record;
2. your `learner/` folder is committed, after Claude shows you
   `git status`;
3. `git pull` brings in what you did on another computer;
4. `git push`.

Claude commits and pushes only when you ask. Every git command that changes
something asks for your approval.

## A second computer

Clone **your** repository (not the framework's), open Claude Code in it,
and run:

```
/onboard machine
```

Your profile and all your progress arrive with the clone; only the machine
setup (a machine id, the hook, reminders, the Codeforces cache) is done
again.

## Studying on two computers

Each computer writes its own log file
(`learner/events/<year>-<month>.<machine>.jsonl`), so two computers never
edit the same file and git merges them without conflicts. Every command
replays all events from every computer in the same order, so after a sync
both computers show the same schedule, the same progress and the same
`PROGRESS.md`. You can study on both without syncing in between; the next
sync brings the two histories together.

## On a phone

Claude Code's Remote Control lets you continue a session running on your
computer from the Claude app (iOS, Android) or from claude.ai/code in a
browser. Start it with `/remote-control` in a running session, or start a
session with `claude --remote-control`. Your computer must stay on, with
that `claude` process running: the session, and the engine, run there. It
needs a Pro, Max, Team or Enterprise plan (not an API key). Facts from
https://code.claude.com/docs/en/remote-control, read 2026-10-12.

On a narrow screen, dashboards fit better with `--width 60`: ask for
"the dashboard, narrow".

## If you downloaded the framework instead of cloning it

`/sync` sets up git for you. Updates still work: the first time
`/update-framework` runs, it connects your copy to the framework's history
at the version you downloaded (the version is in `framework/VERSION`),
keeping all your files as they are.

## Keeping it clean

Never commit passwords, cookies, tokens, `.env` files or course material.
The repository's `.gitignore` covers the usual ones, and Claude stops if
`git status` shows anything that looks like a secret.
