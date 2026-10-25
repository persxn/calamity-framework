# Review

No chapter reaches the learner without three passes. Each round of fixes is followed by a rebuild and a recheck.

## A. Mechanical: the build report

Run `bash <skill-dir>/scripts/build.sh <book-root>` and read `build/check-report.md`.

- **Errors must be zero.** These include LaTeX errors, undefined references and citations, printed `??`, missing or failed figures, text outside a figure's canvas, long flags mangled in print, floats too large for the page, solutions for missing exercises, cited keys not in `refs.bib`, BibTeX errors, and overfull lines over 15pt.
- **Warnings** must each be fixed, or left with a reason you could state. These include smaller overfull lines, exercises without solutions, unused figures, tiny figure text, tables with vertical rules or no caption, web sources without an access date, and leftover TODOs or `<<placeholders>>`.

For overfull lines, the usual fixes are: rephrase the sentence, move a long `\cmd{}` to a listing, shorten a table cell, or reduce a figure's width.

## B. Visual: look at the pages

The report lists the pages that hold figures and tables, and `build/pages/page-N.png` holds every page. Open (Read) **every page of the new or changed chapter**, plus any page the report lists. For each page, check:

**Figures**
- The figure is present (no red MISSING placeholder), sharp, not clipped, and not overlapping the caption.
- Its text is legible at page size, and nothing overlaps.
- It is placed near its first reference, not pages later, and not before the section that introduces it.
- Its caption is complete and says what to notice.

**Tables**
- The table fits the text width, with no text in the margin. Columns are aligned, and rules are booktabs-style.
- The caption is above the table. Multi-page `longtable`s repeat their header.
- Cells aren't crammed. If a cell wraps more than about three lines, rethink the table.

**Listings and inline code**
- No lines run into the margin, and no breaks fall mid-token where it hurts.
- Flags print literally: `--si`, not a dash.
- The prompt and output styling are consistent.

**Boxes and flow**
- Callout boxes aren't split awkwardly (a heading alone at the bottom of a page, or one line alone at the top).
- No headings are stranded at the bottom of a page. No half-empty pages appear before a float (move or resize the float).
- There is no visual clutter: no more than about three boxes on one page, and prose carries the explanation.
- Headers and footers are correct, chapter openings look clean, and there are no stray characters.

Write down each problem with its page number, fix it at the source, rebuild, and look again.

## C. Quality: would this hold up next to the best-selling guide?

### Building the bestseller benchmark (once per topic, saved as `benchmark.md`)

1. Search for the best-regarded books and guides on this topic. Use publisher bestseller lists, curated reading lists from respected engineers, highly rated titles on review sites and forums, and university course reading lists. Pick 2–4.
2. For each, find out *why* readers rate it so highly and what they complain about. Look at reviews, the table of contents, publisher sample chapters and the author's stated approach. Note structure, voice, running example, figure style, exercise style, and how it handles depth.
3. Write `benchmark.md`: the books (verified titles, authors, editions), what makes each excellent, recurring reader complaints to avoid, and a short list of **qualities to match**. Learn from these books' *qualities*. Never copy their text, figures, examples or chapter structure.

### Rubric (score 1–5 with evidence; every dimension must reach 4 or above)

| Dimension | A 5 looks like |
|---|---|
| Accuracy | Every fact, flag, default and output is verified; simplifications are labelled |
| Why before how | The origin and motivation make the mechanism feel inevitable |
| Depth (author's lens) | It descends to the layer where the topic makes sense; the reader could reinvent it |
| Clarity | Plain words before precise terms; each term defined before use; no paragraph needs rereading |
| Flow and structure | Follows the chapter anatomy; signposted; no forward dependency without a pointer |
| Completeness of surface | Every flag or option in scope is covered, grouped, with when-to-use |
| Figures and tables | Each one teaches one idea, is legible, and is referenced from the text |
| Case studies and real world | Realistic scenarios; scale, outage and AI-era features are cited and relevant |
| Exercises | The full mix of levels; answerable from the book so far; worked solutions |
| References | Primary sources first, verified, annotated further reading |
| Voice and engagement | Reads like the best books in `benchmark.md`; you want to keep turning pages |
| Consistency | The same terms, notation, box meanings and figure style as earlier chapters |

Then answer directly, in writing: **"Put this chapter beside the matching chapter of the top book in `benchmark.md`. Where is ours weaker?"** Fix those places, even when every score is already 4 or above.

### Who reviews

If you can spawn a subagent, have a **fresh reviewer** do pass C. Give it only the rendered pages of the chapter (`build/pages/`), this rubric, and `benchmark.md`, not your drafting context. Ask for scores with page-cited evidence and the three most important fixes. If you can't spawn a subagent, wait until you've finished drafting, then review only the page images, reading as a stranger would.

Record the scores and the date in `book-state.md`.
