# Frequently asked questions

## What does it cost?

The framework is free and open source (MIT). It runs inside Claude Code,
which needs a Pro, Max, Team, Enterprise or Console account (the free
claude.ai plan does not include Claude Code). Studying uses your Claude
usage like any other Claude Code work: agents writing and checking
questions, and long sessions, use more.

## Do I need to know how to program?

No. You talk to Claude in plain words, and Claude runs the engine. You need
to open a terminal and paste a few commands to install it ([Linux](setup-linux.md),
[macOS](setup-macos.md), [Windows](setup-windows.md)). The developer track
starts from how a program runs and how to use a terminal.

## Where do the practice questions come from?

They are written for you, for the topics coming up, by the `examiner`
agent, and solved blind by the `checker` agent before you see them. A
question whose independent answer does not match its key never reaches
you. No question bank ships with the framework; official GATE questions
enter only from papers you supply, with their reference.

## Can a question still be wrong?

Yes, rarely. The two agents are the same kind of model, so a blind spot
they share can pass both. The checker computes instead of reasoning
wherever it can to make that rarer, and if you think a key is wrong, say
so: the question is solved again from scratch, and if the key does not hold
it is withdrawn and your answer stops counting.

## Why no points or streaks?

Because they reward showing up rather than remembering, and a broken streak
makes people quit. Each day has a finish line you can count instead: the
reviews due, the day's new topics, the day's lectures. Reaching it is the
day done; what you have learnt shows in the roadmap and the dashboards.

## Can I study several things at once?

Yes. Enrolled skills take turns at new material, reviews come from every
skill, and earlier skills are woven into exercises of later ones. `focus`
in your profile puts one skill, track or GATE ahead of the rest.

## I already know some of this. Do I start from zero?

No. A placement test samples a skill's topics; what you get right enters
the review rotation as known, and only the gaps are taught. Brush-up mode
does this for a whole skill.

## What happens when I skip a few days?

Nothing breaks. Due reviews wait, most forgotten first, and the scheduler
takes the longer gap into account. `/coach` suggests clearing a backlog
before new material.

## Does it work offline?

The engine does: it needs no network except for Codeforces syncs. Claude
Code itself needs an internet connection.

## Is my data private?

It stays in your folder, as plain files. The framework has no telemetry and
no server of its own. To keep it across computers you push it to a
repository of your own, private unless you choose otherwise. Your
conversations with Claude go through Claude Code as any Claude Code
session does.

## Can I use it on my phone?

You can continue a session running on your computer from the Claude app or
a browser with Claude Code's Remote Control; see
[syncing and devices](syncing-and-devices.md#on-a-phone).

## Can I add my own skills, or change the order?

Yes, in plain words: "add Rust", "Fastify instead of Express", "skip
Terraform", "Docker now, Linux later". Your changes live in `learner/tree/`
and survive framework updates. See [the skill tree](skill-tree.md).

## Does it connect to my course website?

Only by a route the site's terms allow. For most paid course sites that is
pasting your curriculum page once and logging lectures as you finish them.
It never stores passwords or cookies and never copies course content. See
[study sources](study-sources.md).

## How do I update it?

`/update-framework`. It shows you what changed (including any change to
permissions or hooks) before merging, and never touches your `learner/`
folder.

## How do I remove it?

See "Updating and removing" in the [README](../README.md#updating-and-removing).

## Which systems are supported?

Linux, macOS and Windows, with Python 3.9 or newer; the tests run on all
three systems with Python 3.9 to 3.15 on every change. The Claude Code
sessions themselves were tried on Linux; see the known limits in the
[README](../README.md#known-limits).
