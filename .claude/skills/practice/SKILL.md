---
name: practice
description: "Track questions the learner works from outside material (a previous-paper book, a PDF of questions, a problem sheet): add and map a set, log what they did, and bring every question back for revisits. Use when the learner says they solved, got wrong or skipped questions from a book, a PDF or previous papers, or asks what to redo."
argument-hint: "[set id | due | log ...]"
---

# Practice sets

A practice set is outside material the learner works from their own copy.
The engine keeps **metadata only**: question numbers, which topics and
pages they belong to, and how each attempt went. Never copy a question's
text into a command, a file, a note or the chat log; the learner's own
note on a mistake is one line about the idea ("TLB: forgot the second
access"), never the question. Engine commands are written `python3
engine/calamity.py ...`; use the one the brief names.

## Add a set

Ask what it is, how many questions, and whether its answer key is
official (previous GATE papers with the official key) or not. Then:

    python3 engine/calamity.py practice add <id> --title "..." --items N --key official|unofficial|none --kind pyq|book|sheet|course|other --source "the learner's own printed copy"

Only an official key makes the set's answers evidence for a topic; any
other set schedules the topics for review but proves nothing (an
unofficial key can be wrong).

## Map it to topics

Ranges of questions to topics, type and pages, as a JSON list in
`.calamity/tmp/<id>-map.json`:

    [{"from": 1, "to": 12, "topics": ["gate.cs.os/scheduling"], "type": "nat", "pages": "41-44"}]

then `python3 engine/calamity.py practice map <id> --file .calamity/tmp/<id>-map.json`.
For a PDF, read **only** its contents and heading pages, with
`pdftotext -layout -f <first> -l <last> <file.pdf> -` on the pages the
learner names (a contents page usually says which questions are on
which topic). Never read the whole PDF, and never the question pages
while mapping. If the learner has no PDF, map from what they tell you
("Q1 to 20 are scheduling"). Topic keys come from
`python3 engine/calamity.py tree show <skill>`.

## Log what they did

From their own words ("did 1 to 20, got 4, 7 and 15 wrong, skipped 18"),
one command per result:

    python3 engine/calamity.py practice log <id> 1-3,5-6,8-14,16-17,19-20 solved
    python3 engine/calamity.py practice log <id> 4,7,15 wrong --err concept
    python3 engine/calamity.py practice log <id> 18 skipped

Ask for the error kind of a wrong one only when it is not obvious
(`concept`, `careless`, `misread`, `time`, `method`, ...). `guessed`
is for an answer that was right by luck. Read back what was logged, in
one line, and the topics it credited.

## Revisits

`python3 engine/calamity.py practice due` lists what to redo, with pages
("redo Q12, Q18 from OS previous papers (pp. 41, 47)"); `next` serves it
after due reviews and before new material. A wrong, guessed or skipped
question returns after 2 days, then 7, then 21; one solved the first time
after 10, then 30. It retires after two right revisits in a row, so every
question is seen at least twice more.

`practice status [<id>]` shows each set's attempted share, first-try
accuracy, skipped, retired and due; `practice stats` the first-try
accuracy per topic across sets.

## Help with one question

When the learner asks for help with one question, read only that page
(`pdftotext -f <page> -l <page>`), help, and do not store anything from
it. When a wrong question shows a real gap, ask the `examiner` agent for
an **original** engine item on the same idea with new numbers (give it
the topic and the idea in one line, never the question's text); the
`checker` verifies it, and it is asked like any other item.
