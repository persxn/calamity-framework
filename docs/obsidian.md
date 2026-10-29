# Obsidian with Calamity

Open your study notes in [Obsidian](https://obsidian.md) — the mastery-textbook
books as a linked, subject-wise knowledge base, and a daily-goals dashboard that
shows the finish line — without giving up Calamity's single source of truth.

**The one rule that matters: one sync.** `learner/` is already a git working tree
that `/sync` moves between your machines. Do **not** turn on Obsidian Sync, iCloud,
Dropbox or any other sync over the same files — two sync systems over one folder
produce conflict markers the engine cannot read. Git stays the only sync; Obsidian
is just the editor and viewer.

## Setup (once, per machine)

1. In Obsidian, **Open folder as vault** → choose your Calamity checkout's
   `learner/` folder (not the repository root — that would pull `engine/`,
   `framework/` and `.claude/` into the vault).
2. Turn it on in the engine:

   ```
   calamity obsidian
   ```

   This writes the vault views and turns on the session-start refresh. From then
   on the dashboard rebuilds at the start of each session; run `calamity obsidian`
   any time to refresh on demand, and `calamity obsidian --off` to stop the
   refresh.
3. (Optional) Calamity Paper look: copy `framework/design/obsidian.css` into
   `learner/.obsidian/snippets/calamity.css` and enable it under
   **Settings → Appearance → CSS snippets**.

## What the engine writes (all under `learner/`)

| File | What it is |
|---|---|
| `Today.md` | The daily-goals dashboard: the `Now:` block, the finish line as checkboxes (reviews, new topics, consolidation, lectures), due reviews, tasks and the next action. **Machine-local and gitignored** — it is regenerated every session, never committed, never a source of truth. |
| `books/<topic>/_MOC.md` | A per-book Map of Content linking its chapters in order. |
| `books/_Index.md` | All books, grouped by track then skill. |
| chapter frontmatter | Stable `calamity: book-chapter` YAML (track/skill/topic/chapter), added only to a chapter that has none — your own edits are never overwritten. |

These are **engine-owned views**. Progress changes only through the engine;
Obsidian never writes back into your record. Live state (mastery, review dates)
is computed fresh into `Today.md`, never baked into chapter files.

## Your own notes

Put your own cross-links, annotations and synthesis notes in `learner/vault/`
(make the folder yourself). The engine never generates or touches anything there,
so it is yours to wikilink freely — link into the book chapters and MOCs as much
as you like.

## Optional plugins (none are required)

The dashboard is plain Markdown and needs nothing. If you want more:

- **Tasks** — the finish-line `- [ ]` lines become checkable.
- **Dataview** or **Bases** — navigation tables over the chapter frontmatter, e.g.

  ````
  ```dataview
  TABLE chapter FROM "books"
  WHERE skill = "compiler-design"
  SORT chapter ASC
  ```
  ````

  Use these for navigation only — never to compute goals or progress; that stays
  the engine's job.
- **Templater** — templates for new notes in `learner/vault/`.

## Committing `.obsidian/`

Commit the durable parts of `learner/.obsidian/` (enabled plugins, the snippet,
Dataview settings) so your setup travels between your machines. The churn is
already gitignored (`workspace*.json`, `cache`).

## Mobile

Desktop-first, but you can have the vault on your phone **without** breaking the
one-sync rule by using the community plugin **obsidian-git** — it syncs over the
*same* git repository, not a second system. Set it to pull on open and commit on a
delay, and always let it finish pulling before you edit. Only touch your own notes
in `learner/vault/` on mobile; leave the engine-owned views (`Today.md`, the MOCs)
to regenerate on the desktop. `Today.md` is gitignored, so it never conflicts.

Obsidian Sync, iCloud or Dropbox over `learner/` are still off-limits — those are a
*second* sync over the git tree and will corrupt it.

## PDF-edition learners (`book.format pdf`)

Nothing extra to do. Even with the PDF edition, mastery-textbook keeps the Markdown
chapter sources on disk (the PDF is built from them), so the vault, MOCs and
frontmatter work exactly the same; the `.pdf` is just an additional artifact.

## Keeping it fresh

`Today.md` rebuilds at the start of every session (the SessionStart hook). If you
run nightly stocking (`calamity stock render`), that scheduled job also refreshes
the views each night, so the dashboard is current even before you open a session.
Run `calamity obsidian` any time to refresh on demand.
