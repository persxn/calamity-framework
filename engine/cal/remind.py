"""Reminders that work when Claude Code is not open.

`check` answers "is anything due?" in one line, for an OS scheduler to show
as a notification. `render` writes the scheduler files for this machine
(cron on Linux, launchd on macOS, Task Scheduler on Windows) into
.calamity/reminders/ and prints the commands that install or remove them.
The engine never installs anything itself: installing is an explicit step
the learner approves.
"""
from __future__ import annotations

import hashlib
import os
import platform
import sys
from xml.sax.saxutils import escape as xml_escape

from . import gateinfo, plan
from .store import Repo, write_text
from .util import CalError, csv_list, parse_hhmm

TAG = "calamity-remind"


def check(repo: Repo, tree, state, when, always: bool = False):
    """Return (exit_code, message). 0 = something is due, 3 = stay quiet."""
    if not repo.onboarded():
        return (0, "Calamity: not set up yet; open Claude Code in the folder and run /onboard") if always else (3, "")
    t = plan.today(repo, tree, state, when)
    if t["sleep"]["inside"] and not always:
        return 3, ""
    if (t["finished"] or t["nothing_to_do"]) and not always:
        return 3, ""
    parts = []
    due = t["n"]["due_now"]
    if due:
        parts.append("%d review%s due" % (due, "" if due == 1 else "s"))
    if t["new_left"]:
        parts.append("%d new topic%s left today" % (t["new_left"], "" if t["new_left"] == 1 else "s"))
    if t["tests_left"]:
        parts.append("%d watched lecture%s to test" % (t["tests_left"], "" if t["tests_left"] == 1 else "s"))
    if t["lectures_left"]:
        parts.append("%d lecture%s left today" % (t["lectures_left"], "" if t["lectures_left"] == 1 else "s"))
    if not parts:
        if not always:
            return 3, ""
        parts.append("nothing due right now")
    days = [gateinfo.days_left(repo, p, when.date()) for p in gateinfo.papers(repo)]
    days = [d for d in days if d is not None and d >= 0]
    if days:
        parts.append("GATE in %d days" % min(days))
    return 0, "Calamity: " + ", ".join(parts)


def _times(repo: Repo, times) -> list:
    raw = csv_list(times) or csv_list(repo.prof("reminders.times"))
    if not raw:
        raise CalError("give the times: remind render --times 09:00,14:00,20:30")
    out = []
    for t in raw:
        minutes = parse_hhmm(t)
        if minutes is None:
            raise CalError("times look like 09:00; got %r" % t)
        out.append((minutes // 60, minutes % 60))
    return sorted(set(out))


def _sh_quote(path: str) -> str:
    return "'" + path.replace("'", "'\\''") + "'"


def _ps_quote(text: str) -> str:
    return "'" + text.replace("'", "''") + "'"


def clone_tag(repo: Repo) -> str:
    """A short tag for this clone, so two clones on one machine never touch each other's reminders."""
    return hashlib.sha1(os.path.normcase(os.path.abspath(repo.root)).encode("utf-8")).hexdigest()[:8]


def _system(os_name: str | None) -> str:
    system = (os_name or platform.system()).lower()
    if system.startswith("win"):
        return "windows"
    return "darwin" if (system == "darwin" or system.startswith("mac")) else "linux"


def render(repo: Repo, times=None, os_name: str | None = None, python: str | None = None) -> str:
    slots = _times(repo, times)
    system = _system(os_name)
    python = python or sys.executable
    engine = os.path.join(repo.root, "engine", "calamity.py")
    out_dir = os.path.join(repo.local, "reminders")
    os.makedirs(out_dir, exist_ok=True)
    shown = ", ".join("%02d:%02d" % s for s in slots)
    tag = clone_tag(repo)
    if system == "windows":
        return _windows(out_dir, slots, python, engine, shown, tag)
    script = os.path.join(out_dir, "notify.sh")
    write_text(script, _NOTIFY_SH % {"python": _sh_quote(python), "engine": _sh_quote(engine)})
    try:
        os.chmod(script, 0o755)
    except OSError:
        pass
    if system == "darwin":
        label = "com.calamity.remind.%s" % tag
        plist = os.path.join(out_dir, label + ".plist")
        entries = "\n".join(
            "    <dict><key>Hour</key><integer>%d</integer><key>Minute</key><integer>%d</integer></dict>" % s
            for s in slots)
        write_text(plist, _PLIST % {"label": label, "script": xml_escape(script), "entries": entries})
        target = "~/Library/LaunchAgents/%s.plist" % label
        return "\n".join([
            "Reminder files written for macOS (%s): %s" % (shown, out_dir),
            "install:",
            "  mkdir -p ~/Library/LaunchAgents && cp %s %s && launchctl unload %s 2>/dev/null; launchctl load %s"
            % (_sh_quote(plist), target, target, target),
            "remove:",
            "  " + _remove_line("darwin", tag),
            "A notification appears only when something is due and never inside the sleep window.",
            "If this folder is under Documents, Desktop, Downloads or iCloud Drive, macOS privacy protection may "
            "stop launchd from running the script; a clone elsewhere (for example ~/calamity) avoids that.",
        ])
    cron = os.path.join(out_dir, "crontab.txt")
    lines = ["%d %d * * * /bin/sh %s # %s-%s" % (m, h, _sh_quote(script), TAG, tag) for h, m in slots]
    write_text(cron, "\n".join(lines) + "\n")
    return "\n".join([
        "Reminder files written for Linux (%s): %s" % (shown, out_dir),
        "install:",
        "  (crontab -l 2>/dev/null | grep -v -e '%s-%s' -e '# %s$'; cat %s) | crontab -" % (TAG, tag, TAG, _sh_quote(cron)),
        "remove:",
        "  " + _remove_line("linux", tag),
        "Notifications use notify-send (package libnotify-bin on Debian/Ubuntu).",
        "A notification appears only when something is due and never inside the sleep window.",
    ])


def _remove_line(system: str, tag: str) -> str:
    if system == "darwin":
        target = "~/Library/LaunchAgents/com.calamity.remind.%s.plist" % tag
        return "launchctl unload %s; rm %s" % (target, target)
    return "crontab -l | grep -v '%s-%s' | crontab -" % (TAG, tag)


def remove(repo: Repo, os_name: str | None = None) -> str:
    """How to take this clone's reminders out again. Needs no times: it removes whatever was installed."""
    system = _system(os_name)
    tag = clone_tag(repo)
    if system == "windows":
        out_dir = os.path.join(repo.local, "reminders")
        _windows_remove_files(out_dir, tag)
        return "remove: run  %s" % os.path.join(out_dir, "remove.cmd")
    return "remove:\n  " + _remove_line(system, tag)


def _cmd_runs(script_name: str) -> str:
    # cmd.exe reads a batch file in the OEM code page, so it stays ASCII and hands over to PowerShell.
    return ('@echo off\r\npowershell.exe -NoProfile -ExecutionPolicy Bypass -File "%%~dp0%s"\r\n' % script_name)


def _write_ps1(path: str, text: str) -> None:
    # Windows PowerShell 5.1 reads a script without a byte-order mark in the ANSI code page, which
    # garbles a path such as C:\\Users\\José: write it as UTF-8 with a BOM and Windows line ends.
    write_text(path, "\ufeff" + text.replace("\n", "\r\n"))


def _windows_remove_files(out_dir: str, tag: str) -> None:
    os.makedirs(out_dir, exist_ok=True)
    _write_ps1(os.path.join(out_dir, "remove.ps1"), _REMOVE_PS1 % {"prefix": _ps_quote("Calamity Remind %s" % tag)})
    write_text(os.path.join(out_dir, "remove.cmd"), _cmd_runs("remove.ps1"))


def _windows(out_dir: str, slots, python: str, engine: str, shown: str, tag: str) -> str:
    script = os.path.join(out_dir, "notify.ps1")
    _write_ps1(script, _NOTIFY_PS1 % {"python": python.replace('"', ""), "engine": engine.replace('"', "")})
    argument = '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%s"' % script
    _write_ps1(os.path.join(out_dir, "install.ps1"), _INSTALL_PS1 % {
        "prefix": _ps_quote("Calamity Remind %s" % tag), "argument": _ps_quote(argument),
        "times": ", ".join(_ps_quote("%02d:%02d" % s) for s in slots)})
    write_text(os.path.join(out_dir, "install.cmd"), _cmd_runs("install.ps1"))
    _windows_remove_files(out_dir, tag)
    return "\n".join([
        "Reminder files written for Windows (%s): %s" % (shown, out_dir),
        "install: run  %s" % os.path.join(out_dir, "install.cmd"),
        "remove:  run  %s" % os.path.join(out_dir, "remove.cmd"),
        "The tasks run on battery too, and a time missed while the computer was off runs when it is back on.",
        "A notification appears only when something is due and never inside the sleep window.",
    ])


_INSTALL_PS1 = """# Generated by Calamity (remind render). Installs this folder's reminders in Task Scheduler.
$ErrorActionPreference = 'Stop'
$prefix = %(prefix)s
Get-ScheduledTask -TaskPath '\\' -ErrorAction SilentlyContinue | Where-Object { $_.TaskName -like "$prefix *" } | Unregister-ScheduledTask -Confirm:$false
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument %(argument)s
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
foreach ($t in @(%(times)s)) {
  $trigger = New-ScheduledTaskTrigger -Daily -At $t
  Register-ScheduledTask -TaskName ("$prefix " + $t.Replace(':', '')) -Action $action -Trigger $trigger -Settings $settings -Force | Out-Null
}
Write-Output 'Calamity reminders installed.'
"""

_REMOVE_PS1 = """# Generated by Calamity (remind render). Removes this folder's reminders from Task Scheduler.
$prefix = %(prefix)s
Get-ScheduledTask -TaskPath '\\' -ErrorAction SilentlyContinue | Where-Object { $_.TaskName -like "$prefix *" } | Unregister-ScheduledTask -Confirm:$false
Write-Output 'Calamity reminders removed.'
"""


_NOTIFY_SH = """#!/bin/sh
# Generated by Calamity (remind render). Shows a desktop notification when study is due.
MSG=$(%(python)s %(engine)s remind check 2>/dev/null) || exit 0
[ -n "$MSG" ] || exit 0
MSG=$(printf '%%s' "$MSG" | tr -d '"\\\\`$')
if command -v notify-send >/dev/null 2>&1; then
  export DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/$(id -u)/bus}"
  export DISPLAY="${DISPLAY:-:0}"
  notify-send "Calamity" "$MSG"
elif command -v osascript >/dev/null 2>&1; then
  osascript -e "display notification \\"$MSG\\" with title \\"Calamity\\""
else
  printf '%%s\\n' "$MSG"
fi
"""

_PLIST = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>%(label)s</string>
  <key>ProgramArguments</key>
  <array><string>/bin/sh</string><string>%(script)s</string></array>
  <key>StartCalendarInterval</key>
  <array>
%(entries)s
  </array>
</dict>
</plist>
"""

_NOTIFY_PS1 = """# Generated by Calamity (remind render). Shows a notification when study is due.
$msg = & "%(python)s" "%(engine)s" remind check 2>$null
if ($LASTEXITCODE -ne 0 -or -not $msg) { exit 0 }
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$icon = New-Object System.Windows.Forms.NotifyIcon
$icon.Icon = [System.Drawing.SystemIcons]::Information
$icon.Visible = $true
$icon.ShowBalloonTip(10000, "Calamity", ($msg -join " "), [System.Windows.Forms.ToolTipIcon]::Info)
Start-Sleep -Seconds 11
$icon.Dispose()
"""
