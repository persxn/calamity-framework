# Setting up on macOS

From nothing to your first session. Claude Code's requirements and install
commands below were read from its official setup page
(https://code.claude.com/docs/en/setup) on 2026-10-12; check there if
anything has changed.

## 1. What you need

| Need | Check it with | Notes |
|---|---|---|
| A Claude account with Claude Code | `claude --version` (after step 2) | Claude Code needs a Pro, Max, Team, Enterprise or Console account; the free claude.ai plan does not include it. |
| macOS 13 or newer | Apple menu, About This Mac | 4 GB RAM or more. |
| Python 3.9 or newer | `python3 --version` | Nothing else to install: the engine uses the standard library only. |
| git | `git --version` | To clone the framework, and later to keep your progress in a repository of your own. |
| Optional: a TeX engine | `tectonic --version` | Only for PDF notes. |

If `python3` or `git` is missing, macOS offers to install Apple's command
line developer tools the first time you type either command; accept, or
run:

```bash
xcode-select --install
```

They include both. With Homebrew you can use `brew install python git`
instead.

## 2. Install Claude Code

The recommended installer (it updates itself in the background):

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

Or with Homebrew (this cask does not update itself; run
`brew upgrade claude-code` from time to time):

```bash
brew install --cask claude-code
```

Open a new terminal, then check:

```bash
claude --version
claude doctor
```

The first time you run `claude`, it opens your browser to sign in.

## 3. Get the framework

```bash
git clone https://github.com/persxn/calamity-framework.git calamity
cd calamity
python3 engine/calamity.py doctor
```

`doctor` should end with `0 problem(s)`. Two warnings are normal on a new
clone: no learner profile yet, and no session-start hook yet. The engine's
own tests take about half a minute:

```bash
python3 engine/calamity.py selftest
```

## 4. Open it in Claude Code

From inside the `calamity` folder:

```bash
claude
```

Claude Code asks whether you trust this folder. Accept. Until a folder is
trusted, Claude Code ignores the permission rules it ships in
`.claude/settings.json`, and every engine command would stop to ask you.

Then type:

```
/onboard
```

Onboarding checks this machine, offers to install the session-start hook
(it asks first), asks who you are and what you want to learn, and enrols
your first skills. [The first session](first-session.md) walks through it.

## 5. Optional extras

- **PDF notes**: `brew install tectonic` is the smallest TeX engine; it
  fetches the LaTeX packages it needs on first use. MacTeX works too. See
  [notes and PDFs](notes-and-pdfs.md).
- **Reminders**: notifications through a LaunchAgent in your user account.
  Ask for them with `/remind`; see [daily use](daily-use.md#reminders).
- **The status line**: `python3 engine/calamity.py setup --statusline`
  shows the day's numbers at the bottom of Claude Code.

Next: [your first session](first-session.md).
