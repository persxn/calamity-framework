# Setting up on Windows

From nothing to your first session, on Windows itself. (Inside WSL, follow
[the Linux guide](setup-linux.md) instead.) Claude Code's requirements and
install commands below were read from its official setup page
(https://code.claude.com/docs/en/setup) on 2026-10-12; check there if
anything has changed.

One difference runs through this guide: on Windows the engine is started
with `python` or `py -3`, not `python3`. Typing `python3` may open the
Microsoft Store instead of Python.

## 1. What you need

| Need | Check it with | Notes |
|---|---|---|
| A Claude account with Claude Code | `claude --version` (after step 2) | Claude Code needs a Pro, Max, Team, Enterprise or Console account; the free claude.ai plan does not include it. |
| Windows 10 1809 or newer | `winver` | 4 GB RAM or more. |
| Python 3.9 or newer | `py -3 --version` or `python --version` | Nothing else to install: the engine uses the standard library only. |
| Git for Windows | `git --version` | To clone the framework and keep your progress in a repository of your own. It also gives Claude Code its Bash tool; without it, Claude Code uses PowerShell, which works as well. |
| Optional: a TeX engine | `pdflatex --version` (MiKTeX) | Only for PDF notes. |

Install what is missing, in PowerShell:

```powershell
winget install Git.Git
winget install Python.Python.3.14
```

Or use the installers from git-scm.com and python.org; on python.org's
installer, tick **Add python.exe to PATH**. Open a new terminal afterwards.

## 2. Install Claude Code

In PowerShell (your prompt starts with `PS C:\`):

```powershell
irm https://claude.ai/install.ps1 | iex
```

In the classic Command Prompt (`C:\` without `PS`):

```batch
curl -fsSL https://claude.ai/install.cmd -o install.cmd && install.cmd && del install.cmd
```

Or with WinGet (this package does not update itself; run
`winget upgrade Anthropic.ClaudeCode` from time to time):

```powershell
winget install Anthropic.ClaudeCode
```

You do not need to run any of these as Administrator. Open a new terminal,
then check:

```powershell
claude --version
claude doctor
```

The first time you run `claude`, it opens your browser to sign in.

## 3. Get the framework

In PowerShell:

```powershell
git clone https://github.com/persxn/calamity-framework.git calamity
cd calamity
python engine/calamity.py doctor
```

If `python` is not found, use `py -3 engine/calamity.py doctor`.
`doctor` should end with `0 problem(s)`. Two warnings are normal on a new
clone: no learner profile yet, and no session-start hook yet. The engine's
own tests take about half a minute:

```powershell
python engine/calamity.py selftest
```

## 4. Open it in Claude Code

From inside the `calamity` folder:

```powershell
claude
```

Claude Code asks whether you trust this folder. Accept. Until a folder is
trusted, Claude Code ignores the permission rules it ships in
`.claude/settings.json`, and every engine command would stop to ask you.
The rules pre-approve the engine whether Claude uses Git Bash or
PowerShell, with `python3`, `python` or `py -3`.

Then type:

```
/onboard
```

Onboarding checks this machine, records which of `python` and `py -3`
works here (the session brief names it from then on), offers to install
the session-start hook (it asks first), asks who you are and what you want
to learn, and enrols your first skills. [The first session](first-session.md)
walks through it.

## 5. Optional extras

- **PDF notes**: `winget install MiKTeX.MiKTeX` installs MiKTeX, which
  fetches missing LaTeX packages when a document first needs them.
  Tectonic works too. See [notes and PDFs](notes-and-pdfs.md).
- **Reminders**: Windows notifications from Task Scheduler. `/remind` writes
  an `install.cmd` and a `remove.cmd` and shows you what they do before
  anything is installed; see [daily use](daily-use.md#reminders).
- **The status line**: `python engine/calamity.py setup --statusline`. It
  cannot be set up automatically when the path to Python or to this folder
  contains a space; the engine says so.

## Windows-specific notes

- **Glyphs**: Windows Terminal shows the dashboard symbols (`✓ ◕ ◐ ○ ·`). In
  an old console window that shows question marks instead, add `--ascii`
  to `dash` and `tree` commands, or ask Claude to.
- **Line endings**: the repository keeps LF line endings on every system
  (`.gitattributes`). Leave git's defaults as they are.
- **A file in use**: if Windows reports that a file is in use (an antivirus
  scan, a sync client, a PDF open in a viewer), the engine retries for a
  few seconds and then says which file; close the program holding it and
  run the command again.

Next: [your first session](first-session.md).
