---
name: remind
description: "Set up, change or remove study reminders on this laptop: notifications that fire only when work is due. Use when the learner asks for reminders, notifications or nudges, or wants them gone."
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

       python3 engine/calamity.py profile set reminders.times 09:00,14:00,21:00

2. Write the scheduler files:

       python3 engine/calamity.py remind render

   This creates files under `.calamity/reminders/` and prints two commands:
   one that installs the reminders and one that removes them (cron on
   Linux, a LaunchAgent on macOS, Task Scheduler on Windows). The engine
   installs nothing itself.

3. Show the learner the install command and say what it does: it adds
   entries to their own user's scheduler that run
   `python3 engine/calamity.py remind check` at those times. Run it only
   when they agree; it will ask for approval as any system command does.

4. Test it once:

       python3 engine/calamity.py remind check --always

   prints what a reminder would say right now.

Changing the times: repeat steps 1 to 3; installing again replaces the old
entries.

## Remove

Run the remove command that `remind render` printed (run `remind render`
again to see it), with the learner's agreement.

## Notes

- Linux notifications use `notify-send`; if it is missing the reminder
  script falls back to printing, so say that the `libnotify` package is
  needed for pop-ups.
- On Windows the task runs a small PowerShell script from
  `.calamity/reminders/` with the execution policy bypassed for that script
  only. Tell the learner before installing.
- If the repository is moved to another folder, render and install again:
  the scheduler entries hold absolute paths.
- A second laptop needs its own setup.
