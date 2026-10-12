# Troubleshooting

Start here, whatever the symptom:

```bash
python3 engine/calamity.py doctor
```

It checks Python, git, the framework files, the skill tree, your profile,
the event log, the practice questions, your study sources, the replay
snapshot, the hook, the status line, `.gitattributes` and `.gitignore`, and
which TeX engine it can use. `OK` lines are fine, `WARN` lines say what is
missing and how to add it, and a `FAIL` line names what must be fixed. On
Windows use `python engine/calamity.py doctor` or `py -3 engine/calamity.py doctor`.

## Setting up

| Symptom | Cause and fix |
|---|---|
| `claude: command not found` after installing Claude Code | Open a new terminal. If it persists, the install folder is not on your `PATH`; Claude Code's troubleshooting page has the fix for your shell. `claude doctor` diagnoses the installation. |
| `python3` opens the Microsoft Store, or is not found, on Windows | Use `python` or `py -3` instead. Onboarding records which works, and the brief names it after `engine:`. |
| `error: Calamity needs Python 3.9 or newer` | Install a newer Python (python.org, your package manager, or Homebrew) and use it. |
| Every engine command asks for permission | The folder is not trusted yet: Claude Code ignores the rules in `.claude/settings.json` until you accept the trust prompt. Quit, start `claude` in the folder again and accept. Commands in another form (with `cd`, pipes or a full path) also ask; Claude is told to use the plain form. |
| No brief at the start of a session | The hook is not installed on this computer. Run `/onboard machine` (or `python3 engine/calamity.py setup --hook`); until then Claude runs the brief by hand. |
| `doctor`: "hook points at a Python that no longer exists" or "at a different copy of the repository" | Python was upgraded, or the folder was moved or copied. Run `setup --hook` again in this folder. |

## Studying

| Symptom | Cause and fix |
|---|---|
| "NEED_ITEM" or "no verified item for that topic" | The question bank has nothing checked for that topic yet. Claude has the examiner and checker agents make one, which takes a minute; meanwhile it can take another topic or record a quick oral check. |
| A question's key looks wrong | Say so. The checker solves it again from scratch; if the key does not hold, the question is withdrawn and your answer stops counting. |
| `next` says `syllabus` | A developer or AI skill has no topic list yet. The curriculum-architect agent writes it the first time you study the skill. |
| "Nothing is due right now" but the finish line shows reviews | Those reviews come due later today; `dash queue` shows when. |
| The dashboard shows `?` or boxes instead of symbols | The terminal font or console cannot show them. Add `--ascii` to `dash` and `tree` commands, or ask Claude for "ASCII dashboards". On Windows, Windows Terminal shows them. |
| A setting you changed seems ignored | `doctor` reports a `cfg.` override it could not use (a wrong type or out of range) and uses the default instead. Fix it with `profile set cfg.<setting> <value>` or `profile unset cfg.<setting>`. |
| Commands feel slow | The first command after an update, a merge from another laptop, or a re-classified mistake replays the whole log; the next ones start from the snapshot. |

## Data and syncing

| Symptom | Cause and fix |
|---|---|
| `doctor` FAIL: event lines could not be read | A line in `learner/events/` is damaged (an editor, a merge conflict marker). The engine skips it and reports where it is. If it came from a merge, keep both sides of the conflict: every line is one event. |
| A merge conflict in `learner/PROGRESS.md` | It is a generated snapshot: take either side, then `python3 engine/calamity.py rebuild` rewrites it. |
| Two laptops disagree | Sync both (commit, pull, push), then `rebuild` on each: replay gives both the same state. |
| "another Calamity command is still writing" | Another engine command (often a background agent) held the write lock for over 15 seconds. Try again; if nothing else is running, delete `.calamity/write.lock`. |
| A file "in use" on Windows | An antivirus scan, a sync client or a viewer holds it. The engine retries for a few seconds, then names the file; close the program and run the command again. |

## Codeforces

| Symptom | Cause and fix |
|---|---|
| `could not reach Codeforces` | Check the connection. If Claude Code's sandbox is on, allow `codeforces.com`. |
| `Call limit exceeded` | Codeforces allows one API call every two seconds; the engine waits between calls and retries, so this is rare. Run `cf sync` again in a minute. |
| The coach says nothing is cached | The Codeforces data is cached per computer: run `cf sync` once on each. |

## Notes and PDFs

| Symptom | Cause and fix |
|---|---|
| "no TeX engine is installed" | Install one (see [notes and PDFs](notes-and-pdfs.md)); the `.tex` files are ready meanwhile. |
| "This TeX installation lacks a LaTeX package" | Install the recommended LaTeX collection (TeX Live), let MiKTeX install packages on demand, or use Tectonic. |
| "PDF build failed" with a file and line | A section has a LaTeX error. Ask Claude to fix that section; the notes writer rebuilds. |
| "the PDF was built but could not be copied" | The old PDF is open in a viewer (Windows locks it). Close it and build again. |

## Reminders

| Symptom | Cause and fix |
|---|---|
| No notification on Linux | Install `notify-send` (`libnotify-bin` on Debian or Ubuntu). Check the entry with `crontab -l`. |
| Reminders stopped after moving the folder | The scheduler holds absolute paths: run `/remind` again in the new place. |
| What would a reminder say now? | `python3 engine/calamity.py remind check --always` |

## Still stuck

Run the engine's own tests and include the result when you report a
problem:

```bash
python3 engine/calamity.py version
python3 engine/calamity.py selftest
```

Then open an issue on the repository with what you ran and what you saw.
Leave your `learner/` data out of it.
