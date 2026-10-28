---
name: bridge
description: "Connect a study source (course site, playlist, MOOC, book) by a route its terms allow, so its lectures enter the plan."
when_to_use: "When the learner names what they study from, wants a course's progress tracked, or a connected source needs updating."
argument-hint: "[source name or address | update <source> | status]"
effort: high
---

# Bridge a study source

Read `framework/rules/bridge-rulebook.md` in full before doing anything.
Its five rules are not negotiable: the site's terms decide the route; no
credentials in the repository; progress metadata only; never go around a
gate; the learner sees what will run.

`status`: `calamity source status` and stop.

## Connect a new source

1. **Ask** what the source is, its address, which track it serves, and what
   their account shows about progress. Ask whether the site offers an
   export or an API. They look; you never log in anywhere and never ask for
   a password, a cookie or a token.

2. **Read the terms.** Fetch the site's `robots.txt` first, on its own,
   with the normal web tools. If it disallows everything or the terms
   page's path, do not fetch the terms page: ask the learner to paste the
   terms. Otherwise fetch the terms page. If a fetch is refused, or the
   terms forbid automated access, that settles it: no tool touches the
   site, and the routes are `paste` and `manual-log`. Do not retry another
   way. Write down in one line what you found and today's date.

3. **Choose the route** with the ladder in the rule book and tell the
   learner which and why. For anything beyond `paste` and `manual-log`,
   delegate the build to the `bridge-engineer` agent, passing the source,
   the route and the terms note.

4. **Register** it:

       calamity source add <id> --title "..." --kind course --url <address> \
           --route <route> --tracks <tracks> --note "<terms note with date>"

5. **Build the catalogue.**
   - `paste`: ask the learner to open their curriculum or progress page,
     select all, copy, and paste it here (or save it under
     `.calamity/tmp/`). Turn it into the JSON list the rule book shows:
     ids, titles, sections, order, lengths. Titles and structure only.
   - Write the list to `.calamity/tmp/<id>.json` and import it:
     `calamity source import <id> --file .calamity/tmp/<id>.json`.

6. **Map lectures to topics.** Delegate to the `curriculum-architect`
   agent for a long catalogue: each lecture gets the syllabus topics it
   completes. Import again with the mapping, then
   `calamity source check` until there are no errors.
   Tell the learner how many lectures could not be placed.

7. **Catch up.** If they have already watched part of it:
   `calamity log <id> <last lecture> --upto`. Otherwise
   they start at the beginning.

8. **Show** `calamity source status <id>` and explain the
   daily habit: after each lecture, `/log <id> <lecture>`, and the test
   follows.

## Update or reconcile

The learner pastes the page again. Hand the paste to the `bridge-engineer`
agent ("update `<source>` from this paste": it parses it, runs
`source import <source> --file F --dry-run`, then the import, `source check`,
and logs what the page shows as done that the log does not), so the page
itself never sits in this conversation; pass on the counts it returns.

## When they ask for more

Automatic tracking of a site that disallows it, downloading lectures,
sharing an account, storing a login: refuse in one sentence, give the
reason (the site's terms, or their own account's safety), and offer the
allowed route. Logging a lecture takes five seconds.
