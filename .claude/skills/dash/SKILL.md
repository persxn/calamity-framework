---
name: dash
description: "Plain-text dashboards: progress, roadmap, revision queue, GATE and Codeforces boards, the week, a past day."
when_to_use: "When the learner asks to see progress, a roadmap, a dashboard, stats, the revision queue, how the week went or what they did on a date."
argument-hint: "[progress | roadmap | queue | gate | cp | week | all]"
---

# Dashboards

Pick the view from the argument or the question:

| They want | Run |
|---|---|
| overall progress (default) | `calamity dash` |
| the roadmap of their tracks | `calamity dash roadmap` (`--all-tracks` for everything, `--track cp` for one) |
| what is due and coming up | `calamity dash queue` |
| the GATE board | `calamity dash gate` |
| the Codeforces board | `calamity dash cp` |
| the last seven days | `calamity dash week` |
| everything at once | `calamity dash all` |
| a past day, or what was done when ("what did I do in October?") | `calamity day 2026-10-12`, `calamity history --by month`, or read `learner/journal/<YYYY-MM>.md` (a month on one page) |
| one skill in detail | `calamity tree show <skill>` |
| the route to a goal | `calamity tree path <skill>` |

Rules:

- Add `--html` to the command: the engine writes the view to a page and
  prints two lines (its headline and the page's path). Pass on those two
  lines and nothing more; the learner opens the page. Print the view in the
  chat instead (without `--html`, unchanged, inside a code block, never
  redrawn) only when the learner asks to see it here or has no browser at
  hand (a phone over Remote Control).
- On a narrow screen (a phone over Remote Control) add `--width 60`. If the
  glyphs do not display, add `--ascii`.
- After the block, at most two lines: the one thing that stands out and the
  next action. No commentary on every row.
- A printable snapshot lives in `learner/PROGRESS.md`; refresh it with
  `calamity rebuild`.
- If the Codeforces board says nothing is cached on this machine, run
  `calamity cf sync` first.
- The first time the learner uses this in a session, add one line: every
  view here runs in a terminal at no cost (the same command; see "Free
  views" in `docs/daily-use.md`).
