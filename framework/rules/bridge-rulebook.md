# The bridge rulebook

A **study source** is wherever a learner's lectures or chapters live: a paid
course site, a YouTube playlist, a MOOC, a book. A **bridge** is how the
framework learns two things from it: the catalogue (which lectures exist, in
what order, covering which topics) and the progress (which ones are done).

Nothing about any particular site is built into the framework. Each bridge
is made for one learner and one source by following these rules. The result
is a source file, `learner/sources/<id>.md`, and sometimes a small tool in
`learner/bridges/<id>/`.

## Rules that are never broken

1. **The site's terms decide the route.** Read the site's robots.txt and
   terms of use before choosing how to connect. If they forbid automated
   access, no tool of any kind touches that site: not a fetch, not a script,
   not a headless browser, not a browser extension driving pages. A refused
   fetch is an answer, not an obstacle. Do not look for another way in.
2. **No credentials in the repository, ever.** No passwords, cookies,
   session tokens, API keys or HAR files in any file here, tracked or not.
   An official API key belongs in an environment variable on the learner's
   machine.
3. **Progress metadata only.** A bridge may store lecture ids, titles,
   section names, order, lengths, done marks and the learner's own scores.
   It never stores videos, slides, notes, transcripts, descriptions or
   question banks, and never copies course content into this repository.
4. **Never go around a gate.** No bypassing of logins, paywalls, DRM,
   CAPTCHAs or rate limits, and no use of anyone else's account.
5. **The learner sees what will run.** Any generated code is read out in
   plain words before its first run, and it runs only with their approval.

## The route ladder

Take the first rung that the terms allow and that actually exists.

| Route | What it is | Use it when |
|---|---|---|
| `api` | The provider's documented API, with the learner's own key | the API exposes what is needed and its terms cover personal use |
| `export` | A file the site lets the learner download (progress report, CSV, certificate list) | the site offers one |
| `browser-session` | A small script the learner runs themselves on a page they have opened while logged in, which copies what the page already shows | the terms allow tools in the learner's own session. If they forbid automated access in general, this rung is closed too |
| `paste` | The learner selects the text of their curriculum or progress page, copies it and pastes it here (or saves it to a file, or shares a screenshot) | always available: it is a person reading their own page |
| `manual-log` | The learner says what they finished: `/log <source> <lecture>` | always available; five seconds per lecture |

For most paid course sites the honest answer is `paste` for the catalogue
and `manual-log` day to day, with a fresh paste now and then to reconcile.
That is enough: the framework needs to know which lectures are done, not to
watch them being watched.

## Procedure

1. **Ask.** What is the source, its address, and what does the learner's
   account show about progress? Does the site offer an export or an API?
   (They look in their account; you do not log in anywhere.)
2. **Read the terms.** Fetch the site's robots.txt first, on its own, with
   the normal web tools. If it disallows everything or the terms page's
   path, do not fetch the terms page: ask the learner to paste it. Otherwise
   fetch the terms page. Record in one line what they allow and the date. If
   a fetch is refused, record that, and treat every automated route as
   closed.
3. **Choose the route** from the ladder and tell the learner why.
4. **Register the source:**

       calamity source add gate-course --title "GATE CS course" --kind course \
           --url https://example.com/course --route paste --tracks gate-cs \
           --note "robots.txt disallows automated access (read 2026-10-11): paste and manual log only"

5. **Build the catalogue.** Turn the pasted page, export file or API result
   into a JSON list and import it:

       calamity source import gate-course --file .calamity/tmp/gate-course.json

   Each entry: `{"id": "os-014", "title": "Semaphores", "section": "Operating Systems", "order": 214, "minutes": 55, "topics": ["gate.cs.operating-systems/concurrency-synchronization"]}`.
   Ids are short and stable (a section prefix and a number work well).
6. **Map lectures to topics** (below), then run
   `calamity source check` until it reports no errors.
7. **Catch up.** If the learner has already watched part of the source:

       calamity log gate-course os-014 --upto

   marks everything up to that lecture as watched earlier. Those topics
   become ready to be tested; they are not counted as known. Assume the
   learner is at the start unless the source shows otherwise.
8. **Show the result:** `calamity source status gate-course`.

## Mapping lectures to topics

- A lecture's `topics` are the syllabus topics it **completes**. If a topic
  takes three lectures, map it to the last of them, so it is not tested
  before it has been taught.
- A lecture may complete several topics, or none (an introduction, a
  doubt-clearing session): leave `topics` empty for those.
- Use the keys of the learner's syllabus exactly
  (`calamity tree show <skill>` lists them). Have the
  `curriculum-architect` agent do the mapping for a long catalogue and
  list the lectures it could not place.
- A course that covers something the syllabus lacks is a reason to look at
  the syllabus, not to invent a topic on the spot.
- A skill with mapped lectures becomes source-led: its topics are tested
  only after their lecture is logged.

## Generated code

Write code only when a route needs it: a parser for an export file, a
client for an official API, a formatter for pasted text that the learner
will reuse. It lives in `learner/bridges/<source>/` with a `README.md` that
states what it reads and from where, the terms it relies on (a short
quotation, the address and the date read), what it writes, and how to run
it.

- Standard library first; add a dependency only when there is no sane
  alternative, and pin it.
- Its output is the JSON for `source import`, and progress through
  `log <source> <item> --method <route>`. It never writes to
  `learner/events/` itself.
- Secrets come from environment variables. The code refuses to run if a
  secret is found in a file inside the repository.
- For an API: only documented endpoints, at least one second between
  requests, back off on errors, a User-Agent that says it is a personal
  study tool, and a `--dry-run` that prints what it would do.
- Running it twice changes nothing the second time.
- A `browser-session` script only reads the page the learner is looking at
  and puts a short JSON summary on the clipboard. It makes no requests of
  its own, clicks nothing and stores nothing.

## Common sources

| Source | Catalogue | Progress |
|---|---|---|
| Paid course site with a login | paste the curriculum page; an official export if one exists | manual log; paste the progress page to reconcile |
| YouTube playlist | paste the playlist page; or the official YouTube Data API with the learner's own key | manual log (tools cannot see a watch history) |
| MOOC with an official export or API | the export or API | the export or API |
| A book or PDF the learner owns | the table of contents, typed or pasted | manual log per chapter |
| Classroom coaching | the timetable, typed | manual log per class |

## Keeping it honest

- The source file records `terms_checked` and `terms_note`. Read the terms
  again when the route changes, when the site changes visibly, and once a
  year.
- If a site's terms change so that a route is no longer allowed, switch to a
  lower rung the same day and delete the tool that used the old route.
- If the learner asks for something these rules forbid (downloading
  lectures, scripting a site that disallows it, sharing an account), say no,
  say why in one sentence, and offer the allowed route.
