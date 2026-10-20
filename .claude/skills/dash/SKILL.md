---
name: dash
description: "Show progress as plain-text dashboards: overall progress, roadmap, revision queue, GATE board, Codeforces board, the week. Use when the learner asks to see progress, roadmap, dashboard, stats, revision queue or how the week went."
argument-hint: "[progress | roadmap | queue | gate | cp | week | all]"
---

# Dashboards

Pick the view from the argument or the question:

| They want | Run |
|---|---|
| overall progress (default) | `python3 engine/calamity.py dash` |
| the roadmap of their tracks | `python3 engine/calamity.py dash roadmap` (`--all-tracks` for everything, `--track cp` for one) |
| what is due and coming up | `python3 engine/calamity.py dash queue` |
| the GATE board | `python3 engine/calamity.py dash gate` |
| the Codeforces board | `python3 engine/calamity.py dash cp` |
| the last seven days | `python3 engine/calamity.py dash week` |
| everything at once | `python3 engine/calamity.py dash all` |
| one skill in detail | `python3 engine/calamity.py tree show <skill>` |
| the route to a goal | `python3 engine/calamity.py tree path <skill>` |

Rules:

- Print the engine's output unchanged inside a code block. Do not redraw
  it, reorder it or convert it to a table.
- On a narrow screen (a phone over Remote Control) add `--width 60`. If the
  glyphs do not display, add `--ascii`.
- After the block, at most two lines: the one thing that stands out and the
  next action. No commentary on every row.
- A printable snapshot lives in `learner/PROGRESS.md`; refresh it with
  `python3 engine/calamity.py rebuild`.
- If the Codeforces board says nothing is cached on this machine, run
  `python3 engine/calamity.py cf sync` first.
- The first time the learner uses this in a session, add one line: every
  view here runs in a terminal at no cost (the same command; see "Free
  views" in `docs/daily-use.md`).
