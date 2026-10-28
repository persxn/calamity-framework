---
name: remind
description: "Study reminders on this laptop that fire only when work is due: set, change or remove them."
when_to_use: "When the learner asks for reminders, notifications or nudges, or wants them gone."
argument-hint: "[times like 09:00,14:00,21:00 | off | check]"
---

# Reminders

Reminders are scheduled by the operating system, so they work when Claude
Code is closed. Each one runs the engine's check and shows a notification
only if something is due; it stays silent inside the learner's sleep
window and once the day's finish line is reached. They are per machine.

## Set or change

1. Agree the times with the learner (they are the learner's choice) and
   store them:

       calamity profile set reminders.times 09:00,14:00,21:00

2. Write the scheduler files:

       calamity remind render

   This creates files under `.calamity/reminders/` and prints two commands:
   one that installs the reminders and one that removes them (cron on
   Linux, a LaunchAgent on macOS, Task Scheduler on Windows). The engine
   installs nothing itself.

3. Show the learner the install command and say what it does: it adds
   entries to their own user's scheduler that run
   `calamity remind check` at those times. Run it only
   when they agree; it will ask for approval as any system command does.

4. Test it once:

       calamity remind check --always

   prints what a reminder would say right now.

Changing the times: repeat steps 1 to 3; installing again replaces the old
entries.

## Remove

    calamity remind remove

prints the command that removes this folder's reminders (no times needed;
other clones' reminders are left alone). Run it with the learner's
agreement.

## Notes

- Linux notifications use `notify-send`; if it is missing the reminder
  script falls back to printing, so say that the `libnotify` package is
  needed for pop-ups.
- On Windows the task runs a small PowerShell script from
  `.calamity/reminders/` with the execution policy bypassed for that script
  only. Tell the learner before installing.
- If the repository is moved to another folder, render and install again:
  the scheduler entries hold absolute paths and a tag of the folder.
- macOS: if the folder is under Documents, Desktop, Downloads or iCloud
  Drive, privacy protection may stop launchd from running the script; say
  so before installing.
- A second laptop needs its own setup.
