# Setting up on Linux

From nothing to your first session. Every step can be checked before you go
on. Claude Code's requirements and install commands below were read from
its official setup page (https://code.claude.com/docs/en/setup) on
2026-10-12; check there if anything has changed.

## 1. What you need

| Need | Check it with | Notes |
|---|---|---|
| A Claude account with Claude Code | `claude --version` (after step 2) | Claude Code needs a Pro, Max, Team, Enterprise or Console account; the free claude.ai plan does not include it. |
| A supported system | `cat /etc/os-release` | For the framework: Ubuntu 22.04+ or Debian 11+, whose `python3` is 3.9 or newer. Claude Code itself lists Ubuntu 20.04+, Debian 10+ and Alpine 3.19+, with apt, dnf (Fedora, RHEL) and apk packages (read 2026-10-20). 4 GB RAM or more. |
| Python 3.9 or newer | `python3 --version` | Nothing else to install: the engine uses the standard library only. A separately installed `python3.9` is not covered by the pre-approved commands, which use `python3`. |
| git | `git --version` | To clone the framework, and later to keep your progress in a repository of your own. |
| Optional: a TeX engine | `tectonic --version`, `pdflatex --version` | Only for PDF notes. |
| Optional: `notify-send` | `command -v notify-send` | Only for desktop reminders. |

Missing Python or git on Debian or Ubuntu:

```bash
sudo apt update
sudo apt install python3 git
```

On Fedora: `sudo dnf install python3 git`.

## 2. Install Claude Code

The recommended installer (it updates itself in the background):

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

Open a new terminal, then check:

```bash
claude --version
claude doctor
```

If your shell says `claude` is not found, the install folder is not on your
`PATH` yet; Claude Code's troubleshooting page explains the fix. Signed apt,
dnf and apk repositories, and an npm package (Node.js 22 or later), are
described on the official setup page.

The first time you run `claude`, it opens your browser to sign in.

## 3. Get the framework

```bash
git clone https://github.com/persxn/calamity-framework.git calamity
cd calamity
python3 engine/calamity.py doctor
```

`doctor` should end with `0 problem(s)`. Two warnings are normal on a new
clone: no learner profile yet, and no session-start hook yet. You can also
run the engine's own tests (about half a minute):

```bash
python3 engine/calamity.py selftest
```

## 4. Open it in Claude Code

From inside the `calamity` folder:

```bash
claude
```

Claude Code asks whether you trust this folder. Accept. This matters: until
a folder is trusted, Claude Code ignores the permission rules the folder
ships in `.claude/settings.json`, and every engine command would stop to ask
you.

Then type:

```
/onboard
```

Onboarding checks this machine, offers to install the session-start hook
(it asks first), asks who you are and what you want to learn, and enrols
your first skills. [The first session](first-session.md) walks through it.

## 5. Optional extras

- **PDF notes**: install a TeX engine. Tectonic is the smallest and fetches
  the LaTeX packages it needs on first use (from its website or your
  distribution). On Debian or Ubuntu, TeX Live works too:
  `sudo apt install texlive-latex-recommended latexmk`.
  See [notes and PDFs](notes-and-pdfs.md).
- **Desktop reminders**: they use `notify-send`
  (`sudo apt install libnotify-bin` on Debian or Ubuntu) and your user's
  crontab. Ask for them with `/remind`; see [daily use](daily-use.md#reminders).
- **The status line**: `calamity setup --statusline`
  shows the day's numbers at the bottom of Claude Code.
- **A `calamity` command**: `python3 engine/calamity.py setup --alias --shim`
  adds an alias to your shell's start-up file, so that typing `calamity`
  in a new terminal goes to this folder and starts
  `claude --dangerously-skip-permissions`. That session asks no
  permission questions at all, including the ones this folder's
  settings would ask; leave it out if you want them. `setup --remove-alias`
  takes it out.

Next: [your first session](first-session.md).
