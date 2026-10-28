---
name: practice
description: "Questions from outside material as metadata (map a set, log results, revisit each), and the developer track's session types: system-day, classic, outage, oss, vocab."
when_to_use: "When the learner logs questions from a book, a PDF or previous papers, asks what to redo, or wants a system-day, classic, outage, open-source or vocabulary session."
argument-hint: "[set id | due | log ... | system-day | classic | outage | oss | vocab]"
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

    [{"from": 1, "to": 12, "topics": ["gate.cs.operating-systems/cpu-scheduling"], "type": "nat", "pages": "41-44"}]

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

## Developer sessions

The developer track's own practice, run as one session each (`/practice <type>`):

| Type | The session | Ends with |
|---|---|---|
| `system-day` | a real system the learner did not choose (the tutor names it: Discord's message store, Stripe's idempotency, Netflix's CDN), taken apart from its constraints: what it must do, what breaks at its scale, the design, each trade-off | a one-page design sketch in the learner's words |
| `classic` | a classic read: a paper, an RFC or an engineering post (the tutor checks it exists and links the original) | at least three new ideas, each in a sentence of the learner's own |
| `outage` | a real, published post-mortem: the failure chain rebuilt link by link, the decision behind each, what the learner would have done | the chain written as trigger → causes → impact → fix |
| `oss` | open-source immersion: a repository cloned into `.calamity/scratch/` (never committed), built, run, traced, changed in one small way | the change, and a `path:symbol` map of what was read |
| `vocab` | about five terms of `eng-vocab` (enrol it once), each with its mental model, a real example, where it bites, and a check | the terms in the topic's notes fragment |

For every session:

1. Teach and discuss to the depth contract; nothing copied in from the source (summaries in the learner's words, links to the original).
2. Record it: `python3 engine/calamity.py practice session <type> --minutes N --topic <key> --ideas N --note "what it was about"`. Pick the closest tree topic (`find <words>`; for vocab, the `eng-vocab` family).
3. Save the notes fragment for that topic (notes skill, step 1).
4. Hand its testable ideas to the examiner as seeds for that topic, then the ids to the checker: the session itself is not evidence; the items that follow are.

`python3 engine/calamity.py practice sessions` shows what was done lately and which types have not come up.

