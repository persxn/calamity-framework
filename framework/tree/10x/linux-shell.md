---
id: linux-shell
title: "Linux & the shell"
track: 10x
group: foundations
prereqs: [dev-environment]
weaves_into: [10x, ai]
aliases: [linux, bash, terminal, command line, cli]
est_hours: 30
order: 20
summary: "Work a Linux machine from the terminal: files, permissions, processes, text tools, bash scripts, ssh."
---

# Scope

What the mastery standard covers. The learner's own syllabus is written from this list
and from current official documentation when they start the skill.

- filesystem layout, absolute and relative paths, navigating and managing files (cp, mv, rm, ln, find)
- permissions and ownership (chmod, chown), users and groups, sudo
- text tools and pipelines: cat, less, grep, sed, awk, sort, uniq, cut, wc, xargs, redirection
- processes and jobs: ps, top/htop, kill and signals, background jobs
- services and logs with systemd: systemctl, journalctl, timers
- bash scripting: variables, quoting, conditionals, loops, functions, exit codes, `set -euo pipefail`
- environment variables, PATH, shell startup files
- remote work: ssh keys and config, scp, rsync
- packages (apt or dnf), archives (tar, gzip), disk usage (df, du)
- first network tools: curl, ping, ss

# Boss

Write a backup-and-report script for a project directory: archive it with a dated name, keep the last N archives, write a one-line report to a log, and exit non-zero on any failure. Run it on a schedule with a systemd timer or cron.

Passes when:

- `shellcheck` reports nothing
- running it twice in a row leaves the same end state (idempotent)
- a forced failure (read-only target) produces a non-zero exit code and a log line
- the timer or cron entry is listed and has fired once

# Weave

Shell work belongs inside every later exercise: finding files, reading logs, wiring scripts, ssh to a server.
