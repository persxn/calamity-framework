# Study sources: courses, playlists and books

Many learners study from something outside Claude: a paid course site, a
YouTube playlist, a MOOC, a book, classes. Connect it once and its lectures
become part of the plan: you watch a lecture there, log it here, and its
test follows straight away. A topic covered by a lecture is tested only
after you have logged that lecture.

Start with `/bridge` and name the source.

## The rules, which do not bend

1. **The site's terms decide how it is connected.** Claude reads the site's
   `robots.txt` and terms of use before choosing a route. If they forbid
   automated access, nothing touches that site: no fetching, no scripts, no
   browser automation. A refused fetch is an answer, not an obstacle.
2. **No credentials, ever.** No passwords, cookies, session tokens, API keys
   or HAR files in the repository, tracked or not. An official API key you
   choose to use belongs in an environment variable on your computer.
3. **Progress metadata only.** Lecture ids, titles, sections, order,
   lengths, what is done, your own scores. Never videos, slides,
   transcripts, notes or question banks from the course.
4. **No getting around a gate**: logins, paywalls, DRM, CAPTCHAs or rate
   limits, or anyone else's account.
5. **You see what will run.** Any generated tool is explained in plain words
   before it first runs, and runs only with your approval.

## The routes

Claude takes the first route that the terms allow and that exists:

| Route | What it is |
|---|---|
| `api` | The provider's documented API, with your own key |
| `export` | A file the site lets you download (a progress report, a CSV) |
| `browser-session` | A small script you run yourself on a page you have open, which copies what the page already shows (only where the terms allow tools in your own session) |
| `paste` | You select the text of your curriculum or progress page, copy it and paste it into the conversation |
| `manual-log` | You say what you finished: `/log <source> <lecture>` |

For most paid course sites the honest answer is `paste` for the catalogue
and `manual-log` day to day, with a fresh paste now and then to reconcile.
The framework needs to know which lectures are done, not to watch you
watching them.

## What connecting looks like

1. You name the source and its address. Claude reads its terms and tells you
   the route and why.
2. The source is registered: `learner/sources/<id>.md` records the route, a
   one-line note of what the terms allow, and the date they were read.
3. For `paste`, you paste your curriculum page; Claude turns it into a list
   of lectures (titles and structure only) and imports it.
4. Each lecture is mapped to the syllabus topics it **completes** (a topic
   spread over three lectures is mapped to the last one). The
   `curriculum-architect` agent does this for a long catalogue and tells
   you what it could not place.
5. If you are already part-way through, everything up to where you are is
   logged as watched earlier: those topics become ready to be tested, not
   known.

## Day to day

```bash
python3 engine/calamity.py log gate-course os-14          # by id
python3 engine/calamity.py log gate-course 14             # by its number
python3 engine/calamity.py log gate-course semaphores     # by a unique piece of its title
python3 engine/calamity.py log gate-course os-30 --upto   # everything up to os-30, watched earlier
python3 engine/calamity.py source status gate-course      # how far you are, what is next
```

Or just tell Claude: "I finished lecture 14". It logs the lecture and
offers the test at once: the minutes after a lecture are when testing pays
most. A lecture quota (`lectures_per_day`) adds lectures to the day's finish
line.

If you ask for something these rules forbid (downloading lectures,
scripting a site that disallows it, sharing an account), Claude says no,
says why in one sentence, and offers the allowed route. Logging a lecture
takes five seconds.

The full rules are in `framework/rules/bridge-rulebook.md`.
