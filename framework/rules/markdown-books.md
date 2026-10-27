# Study books in Markdown

How a study book or long-form notes are written when the learner's
`book.format` is `markdown`, the default. It is read by the notes skill, the
`notes-writer` agent and the `mastery-textbook` skill. Markdown is the
primary format: it costs a fraction of the tokens of LaTeX, renders on
GitHub and in any editor, and stays easy to change. A PDF is made only
when the learner asks for one, by the engine, from the same files:

    python3 engine/calamity.py book pdf <file or folder>

No model writes or reviews LaTeX for it.

## The format question

The brief says `Study books: format not chosen` until the learner has
answered. Ask once, the first time study material would be written: "A
well-structured Markdown file as your main textbook (the default, cheaper
and quicker), or a PDF?". Record the answer:

    python3 engine/calamity.py profile set book.format markdown

`pdf` keeps the earlier LaTeX path (`framework/rules/notes-latex.md`). Never
ask again unless the learner raises it.

## Layout

- Notes: one section per topic, `learner/notes/<skill>/md/<topic>.md`,
  assembled by `notes assemble <skill>` into `<skill>-notes.md`.
- A study book: `learner/mastery/<topic>/book/`, with `README.md` (title,
  one paragraph on what the book covers, the contents as links) and one
  file per chapter, `01-<slug>.md`, `02-<slug>.md`, ... `book pdf` on the
  folder joins them in that order.
- Change one chapter at a time. Never rewrite a whole book to fix a
  section.

## Writing

The depth is the same as any teaching here (`framework/method-teaching.md`);
only the medium changes.

- One `#` title per book (in `README.md` or the notes file); `##` per
  chapter or topic, `###` per section. No skipped levels.
- A chapter's order: what it is and why it exists, the mental model, the
  mechanics, the simplest example then a realistic one, where it is used,
  flags or options (a table), trade-offs, then *Check yourself* and a
  short glossary.
- **Taught before tested.** A *Check yourself* question uses only words,
  commands and ideas the book has already explained. Answers go in a
  `<details>` block under each question, so the reader can try first.
- A new term is **bold** where it is defined, and nowhere before.
- Code in fenced blocks with a language (`bash`, `python`, `c`). A
  terminal session is a `console` block with a `$ ` prompt and real output
  that was run, never invented.
- Diagrams: box-drawing art in a `text` block (it renders everywhere,
  the PDF included), or a `mermaid` block where the diagram is clearer as a
  graph (it renders on GitHub; in the PDF its source is shown).
- Tables in GitHub's pipe form, at most four columns, short cells.
- Callouts as block quotes: `> **Note** —`, `> **Common misconception** —`,
  `> **Warning** —`.
- Links to the official source for facts that change, with the date read.
- Keep to what `book pdf` understands: headings, paragraphs, bold, italic,
  inline code, links, lists (nested by two spaces), fenced code, pipe
  tables, block quotes, rules, images that exist on disk, and
  `<details>`/`<summary>`. No other HTML, no footnotes, no nested tables.
