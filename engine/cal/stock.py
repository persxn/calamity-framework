"""Nightly bank stocking: a scheduled, headless Claude Code run of the /stock skill.

`render` writes the scheduler files for this machine into .calamity/stock/ (cron on Linux, launchd on
macOS, Task Scheduler on Windows) and prints the commands that install or remove them, as `remind`
does. The engine never installs anything itself. The script it schedules first asks the engine
whether anything needs stocking, and starts Claude Code only when something does, with its tools
limited to the engine, the agents' scratch folders and the web (for checking facts). Each run
logs to .calamity/logs/.
"""
from __future__ import annotations

import os
import shutil
import sys
from xml.sax.saxutils import escape as xml_escape

from . import machine
from .remind import _cmd_runs, _ps_quote, _sh_quote, _system, _write_ps1, clone_tag
from .store import Repo, write_text
from .util import CalError, parse_hhmm

TAG = "calamity-stock"
LOOK = "--days 2 --per-topic 3"       # tonight's work list: the rest of today and tomorrow, families of three


def allowed_tools(engine: str) -> list:
    """What the headless run may use, and nothing else (it runs with --permission-mode dontAsk): the engine as
    `calamity` and in its full form (the brief names one of them), and the Python interpreter, for the examiner's
    and checker's scripts in their own scratch folders."""
    full = machine.guess_cmd()                       # e.g. "python3 engine/calamity.py"
    py = full[:-len(" engine/calamity.py")] if full.endswith(" engine/calamity.py") else "python3"
    engines = []
    for form in ("calamity", engine, full):
        if form not in engines:
            engines.append(form)
    return (["Read", "Glob", "Grep", "Agent", "WebSearch", "WebFetch",
             "Write(/.calamity/tmp/**)", "Edit(/.calamity/tmp/**)"]
            + ["Bash(%s *)" % form for form in engines]
            + ["Bash(%s .calamity/tmp/examiner/*)" % py, "Bash(%s .calamity/tmp/checker/*)" % py])


def _time(repo: Repo, at) -> tuple:
    raw = at or repo.prof_text("stock.at")
    if not raw:
        raise CalError("give the time: stock render --at 23:45 (after the day's close block, outside study hours)")
    minutes = parse_hhmm(str(raw))
    if minutes is None:
        raise CalError("a time looks like 23:45; got %r" % raw)
    return minutes // 60, minutes % 60


def claude_path() -> str:
    """Claude Code's full path, so the scheduler's short PATH still finds it."""
    return shutil.which("claude") or "claude"


def claude_args(repo: Repo, model: str, effort: str) -> list:
    engine = machine.engine_cmd(repo)
    return ["-p", "/stock", "--permission-mode", "dontAsk", "--allowedTools", ",".join(allowed_tools(engine)),
            "--model", model, "--effort", effort]


def render(repo: Repo, at=None, model: str = "opus", effort: str = "high", os_name: str | None = None,
           python: str | None = None) -> str:
    hour, minute = _time(repo, at)
    system = _system(os_name)
    python = python or sys.executable
    engine = os.path.join(repo.root, "engine", "calamity.py")
    out_dir = os.path.join(repo.local, "stock")
    logs = os.path.join(repo.local, "logs")
    os.makedirs(out_dir, exist_ok=True)
    tag = clone_tag(repo)
    shown = "%02d:%02d" % (hour, minute)
    args = claude_args(repo, model, effort)
    note = ("Each night at %s it asks the engine for tomorrow's work list (item needs %s) and, only when "
            "something is missing, runs Claude Code headless on /stock (model %s, effort %s): the examiner "
            "writes item families, the checker verifies them blind. It uses your plan's usage while it runs; "
            "logs go to %s." % (shown, LOOK, model, effort, logs))
    if system == "windows":
        script = os.path.join(out_dir, "stock.ps1")
        _write_ps1(script, _STOCK_PS1 % {
            "root": repo.root.replace("'", "''"), "python": python.replace('"', ""), "engine": engine.replace('"', ""),
            "logs": logs.replace("'", "''"), "look": LOOK, "args": " ".join(_ps_quote(a) for a in args),
            "claude": claude_path().replace("'", "''"),
            "bin": os.path.join(machine.framework_root(), "bin").replace("'", "''")})
        argument = '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%s"' % script
        _write_ps1(os.path.join(out_dir, "install.ps1"), _INSTALL_PS1 % {
            "name": _ps_quote("Calamity Stock %s" % tag), "argument": _ps_quote(argument), "at": _ps_quote(shown)})
        write_text(os.path.join(out_dir, "install.cmd"), _cmd_runs("install.ps1"))
        _windows_remove_files(out_dir, tag)
        return "\n".join(["Stocking files written for Windows (%s): %s" % (shown, out_dir),
                          "install: run  %s" % os.path.join(out_dir, "install.cmd"),
                          "remove:  run  %s" % os.path.join(out_dir, "remove.cmd"), note])
    script = os.path.join(out_dir, "stock.sh")
    write_text(script, _STOCK_SH % {"root": _sh_quote(repo.root), "python": _sh_quote(python),
                                    "engine": _sh_quote(engine), "logs": _sh_quote(logs), "look": LOOK,
                                    "args": " ".join(_sh_quote(a) for a in args), "claude": _sh_quote(claude_path()),
                                    "bin": _sh_quote(os.path.join(machine.framework_root(), "bin"))})
    try:
        os.chmod(script, 0o755)
    except OSError:
        pass
    if system == "darwin":
        label = "com.calamity.stock.%s" % tag
        plist = os.path.join(out_dir, label + ".plist")
        write_text(plist, _PLIST % {"label": label, "script": xml_escape(script), "hour": hour, "minute": minute})
        target = "~/Library/LaunchAgents/%s.plist" % label
        return "\n".join([
            "Stocking files written for macOS (%s): %s" % (shown, out_dir),
            "install:",
            "  mkdir -p ~/Library/LaunchAgents && cp %s %s && launchctl unload %s 2>/dev/null; launchctl load %s"
            % (_sh_quote(plist), target, target, target),
            "remove:", "  " + _remove_line("darwin", tag), note])
    cron = os.path.join(out_dir, "crontab.txt")
    write_text(cron, "%d %d * * * /bin/sh %s # %s-%s\n" % (minute, hour, _sh_quote(script), TAG, tag))
    return "\n".join([
        "Stocking files written for Linux (%s): %s" % (shown, out_dir),
        "install:",
        "  (crontab -l 2>/dev/null | grep -v '%s-%s'; cat %s) | crontab -" % (TAG, tag, _sh_quote(cron)),
        "remove:", "  " + _remove_line("linux", tag),
        "cron runs it only while the computer is on and awake at that time.", note])


def _remove_line(system: str, tag: str) -> str:
    if system == "darwin":
        target = "~/Library/LaunchAgents/com.calamity.stock.%s.plist" % tag
        return "launchctl unload %s; rm %s" % (target, target)
    return "crontab -l | grep -v '%s-%s' | crontab -" % (TAG, tag)


def _windows_remove_files(out_dir: str, tag: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    _write_ps1(os.path.join(out_dir, "remove.ps1"), _REMOVE_PS1 % {"name": _ps_quote("Calamity Stock %s" % tag)})
    write_text(os.path.join(out_dir, "remove.cmd"), _cmd_runs("remove.ps1"))


def remove(repo: Repo, os_name: str | None = None) -> str:
    """How to take this clone's nightly stocking out again."""
    system = _system(os_name)
    tag = clone_tag(repo)
    if system == "windows":
        out_dir = os.path.join(repo.local, "stock")
        _windows_remove_files(out_dir, tag)
        return "remove: run  %s" % os.path.join(out_dir, "remove.cmd")
    return "remove:\n  " + _remove_line(system, tag)


_STOCK_SH = """#!/bin/sh
# Generated by Calamity (stock render). Stocks the item bank for tomorrow with a headless Claude Code run.
cd %(root)s || exit 0
# a scheduler's PATH is short: the framework's own bin/ makes `calamity` this learner's engine
CALAMITY_ROOT=%(root)s; export CALAMITY_ROOT
PATH=%(bin)s:"$HOME/.local/bin":$PATH; export PATH
mkdir -p %(logs)s
LOG=%(logs)s/stock-$(date +%%Y-%%m-%%d).log
NEED=$(%(python)s %(engine)s item needs %(look)s 2>&1)
case "$NEED" in
  "ITEMS NEEDED"*) ;;
  *) printf '%%s nothing to stock: %%s\\n' "$(date +%%H:%%M)" "$(printf '%%s' "$NEED" | head -n 1)" >> "$LOG"; exit 0 ;;
esac
command -v %(claude)s >/dev/null 2>&1 || { printf 'Claude Code was not found: render again\\n' >> "$LOG"; exit 0; }
printf '%%s stocking\\n' "$(date +%%H:%%M)" >> "$LOG"
%(claude)s %(args)s >> "$LOG" 2>&1
%(python)s %(engine)s item needs %(look)s >> "$LOG" 2>&1
"""

_STOCK_PS1 = """# Generated by Calamity (stock render). Stocks the item bank for tomorrow with a headless Claude Code run.
Set-Location -LiteralPath '%(root)s'
$env:CALAMITY_ROOT = '%(root)s'
$env:PATH = '%(bin)s;' + $env:PATH
New-Item -ItemType Directory -Force -Path '%(logs)s' | Out-Null
$log = Join-Path '%(logs)s' ("stock-" + (Get-Date -Format 'yyyy-MM-dd') + ".log")
$need = & "%(python)s" "%(engine)s" item needs %(look)s 2>&1 | Out-String
if (-not $need.StartsWith('ITEMS NEEDED')) { Add-Content $log ((Get-Date -Format 'HH:mm') + ' nothing to stock: ' + ($need -split "`n")[0]); exit 0 }
if (-not (Get-Command '%(claude)s' -ErrorAction SilentlyContinue)) { Add-Content $log 'Claude Code was not found: render again'; exit 0 }
Add-Content $log ((Get-Date -Format 'HH:mm') + ' stocking')
& '%(claude)s' %(args)s *>> $log
& "%(python)s" "%(engine)s" item needs %(look)s *>> $log
"""

_INSTALL_PS1 = """# Generated by Calamity (stock render). Installs this folder's nightly stocking in Task Scheduler.
$ErrorActionPreference = 'Stop'
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument %(argument)s
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$trigger = New-ScheduledTaskTrigger -Daily -At %(at)s
Register-ScheduledTask -TaskName %(name)s -Action $action -Trigger $trigger -Settings $settings -Force | Out-Null
Write-Output 'Calamity nightly stocking installed.'
"""

_REMOVE_PS1 = """# Generated by Calamity (stock render). Removes this folder's nightly stocking from Task Scheduler.
Unregister-ScheduledTask -TaskName %(name)s -Confirm:$false -ErrorAction SilentlyContinue
Write-Output 'Calamity nightly stocking removed.'
"""

_PLIST = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>%(label)s</string>
  <key>ProgramArguments</key>
  <array><string>/bin/sh</string><string>%(script)s</string></array>
  <key>StartCalendarInterval</key>
  <dict><key>Hour</key><integer>%(hour)d</integer><key>Minute</key><integer>%(minute)d</integer></dict>
</dict>
</plist>
"""
