"""Reminders that work when Claude Code is not open.

`check` answers "is anything due?" in one line, for an OS scheduler to show
as a notification. `render` writes the scheduler files for this machine
(cron on Linux, launchd on macOS, Task Scheduler on Windows) into
.calamity/reminders/ and prints the commands that install or remove them.
The engine never installs anything itself: installing is an explicit step
the learner approves.
"""
from __future__ import annotations

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
        return 3, ""
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


def render(repo: Repo, times=None, os_name: str | None = None, python: str | None = None) -> str:
    slots = _times(repo, times)
    system = (os_name or platform.system()).lower()
    python = python or sys.executable
    engine = os.path.join(repo.root, "engine", "calamity.py")
    out_dir = os.path.join(repo.local, "reminders")
    os.makedirs(out_dir, exist_ok=True)
    shown = ", ".join("%02d:%02d" % s for s in slots)
    if system.startswith("win"):
        return _windows(out_dir, slots, python, engine, shown)
    script = os.path.join(out_dir, "notify.sh")
    write_text(script, _NOTIFY_SH % {"python": _sh_quote(python), "engine": _sh_quote(engine)})
    try:
        os.chmod(script, 0o755)
    except OSError:
        pass
    if system == "darwin" or system.startswith("mac"):
        plist = os.path.join(out_dir, "com.calamity.remind.plist")
        entries = "\n".join(
            "    <dict><key>Hour</key><integer>%d</integer><key>Minute</key><integer>%d</integer></dict>" % s
            for s in slots)
        write_text(plist, _PLIST % {"script": xml_escape(script), "entries": entries})
        target = "~/Library/LaunchAgents/com.calamity.remind.plist"
        return "\n".join([
            "Reminder files written for macOS (%s): %s" % (shown, out_dir),
            "install:",
            "  cp %s %s && launchctl unload %s 2>/dev/null; launchctl load %s" % (_sh_quote(plist), target, target, target),
            "remove:",
            "  launchctl unload %s; rm %s" % (target, target),
            "A notification appears only when something is due and never inside the sleep window.",
        ])
    cron = os.path.join(out_dir, "crontab.txt")
    lines = ["%d %d * * * /bin/sh %s # %s" % (m, h, _sh_quote(script), TAG) for h, m in slots]
    write_text(cron, "\n".join(lines) + "\n")
    return "\n".join([
        "Reminder files written for Linux (%s): %s" % (shown, out_dir),
        "install:",
        "  (crontab -l 2>/dev/null | grep -v '%s'; cat %s) | crontab -" % (TAG, _sh_quote(cron)),
        "remove:",
        "  crontab -l | grep -v '%s' | crontab -" % TAG,
        "Notifications use notify-send (package libnotify-bin on Debian/Ubuntu).",
        "A notification appears only when something is due and never inside the sleep window.",
    ])


def _windows(out_dir: str, slots, python: str, engine: str, shown: str) -> str:
    script = os.path.join(out_dir, "notify.ps1")
    write_text(script, _NOTIFY_PS1 % {"python": python.replace('"', ""), "engine": engine.replace('"', "")})
    install, remove = [], []
    for h, m in slots:
        name = "Calamity\\Remind-%02d%02d" % (h, m)
        install.append(
            'schtasks /Create /F /SC DAILY /ST %02d:%02d /TN "%s" /TR "powershell.exe -NoProfile -ExecutionPolicy Bypass '
            '-WindowStyle Hidden -File \\"%s\\""' % (h, m, name, script))
        remove.append('schtasks /Delete /F /TN "%s"' % name)
    write_text(os.path.join(out_dir, "install.cmd"), "@echo off\r\n" + "\r\n".join(install) + "\r\n")
    write_text(os.path.join(out_dir, "remove.cmd"), "@echo off\r\n" + "\r\n".join(remove) + "\r\n")
    return "\n".join([
        "Reminder files written for Windows (%s): %s" % (shown, out_dir),
        "install: run  %s" % os.path.join(out_dir, "install.cmd"),
        "remove:  run  %s" % os.path.join(out_dir, "remove.cmd"),
        "A notification appears only when something is due and never inside the sleep window.",
    ])


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
  <key>Label</key><string>com.calamity.remind</string>
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
