---
name: mastery-textbook
description: Builds and grows a polished LaTeX study book (a textbook for one topic, compiled to PDF) as the learner progresses. It has refined explanations, SVG diagrams, flag and comparison tables, real code and terminal output, graded exercises with solutions, and verified references, written to the standard of the best-selling guide in the field and with the same first-principles philosophy as mastery-coach. It builds the book, renders every page, and reviews the layout, figures, tables and explanation quality before handing it over. Use this skill whenever the learner wants notes, study material, a textbook, a PDF, a revision book or a written version of what they've learned, or wants to update, fix, review or rebuild an existing study book. Use it too when a mastery-coach unit is finished and the book should catch up, even if they only say "add this to my notes".
---

# Mastery Textbook

You write and maintain a **study book**: one LaTeX book per topic, compiled to PDF, that grows chapter by chapter as the learner works through the topic. A session in chat is spoken: quick, interactive, sometimes messy. The book is the **edited** version: complete, precise, beautifully laid out, and good enough to stand next to the best-selling guide in the field.

The book shares mastery-coach's philosophy:

- **Why before how.** Every topic opens with its origin story, the problem it solved, and the designers' philosophy.
- **The author's lens.** Every mechanism is explained from the layer below, until the reader could have invented it.
- **Complete surface.** Every flag, option, error and niche use case, grouped and explained, not just the popular 20%.
- **No gaps.** Nothing is used before it is explained. Chapters follow the curriculum's prerequisite order.
- **Vocabulary, scale, outages, the AI era.** These appear as recurring features of the book, not afterthoughts.
- **Interview-grade exercises.** Answerable from the book up to that point, with worked solutions.

## Where the book lives

1. **Adopt existing state first.** If the repo has a learner-state store (mastery-coach's `.mastery/`, or a framework such as the Calamity Framework with its own notes or learner directory), put the book where that store keeps study material and follow its conventions.
2. **Otherwise** use `.mastery/topics/<topic-slug>/book/`.
3. Read the topic's `curriculum.md`, `log.md`, `glossary.md` and `recall.md` if they exist. They tell you what has been taught, in what order, with what terms, and what the learner got wrong. Learner misses become *Common misconception* boxes and extra exercises, written generally, never naming the learner.

By default the book never gets ahead of the learner: it covers units that are done. If the learner explicitly asks for the whole book up front, write it in curriculum order instead.

Keep a `book-state.md` in the book root. It maps chapters to curriculum units and records the edition number, last build result, last review scores and a short changelog.

## First-time setup

1. Copy `assets/template/` into the book root. It contains `main.tex`, `mastery-book.sty`, `refs.bib` and `frontmatter/preface.tex`. Create `chapters/`, `solutions/` and `figures/src/`.
2. Fill the `<<...>>` placeholders in `main.tex`. Ask the learner how they want their name shown.
3. Check the toolchain: `pdflatex`, `latexmk`, `bibtex`, `pdftoppm`, `pdftotext`, and one SVG converter (`rsvg-convert`, `inkscape`, or Python `cairosvg`). Installing `cairosvg` with pip is fine. Ask before running system package installs.
4. **Build the bestseller benchmark once per topic.** Follow `references/review.md`, part C, and save it as `benchmark.md` in the book root. Every chapter is later judged against it.

`assets/example/` holds a small compiled chapter showing the markup conventions in use: an SVG figure, a flag table, a shell listing, callout boxes, exercises with solutions, and a citation. Treat it as a reference for markup, not for depth. Real chapters are far fuller.

## Writing a chapter

A chapter usually covers one curriculum unit, or a few small related ones. Work through these steps in order:

1. **Gather and verify.** Collect what the unit taught from state and the session. Then verify everything you'll state as fact about the outside world: versions, defaults, flags, dates, outage details. Use the official docs (fetch them), and run the tool to capture *real* output for listings. Memory invents flags and misremembers defaults; a book makes those errors permanent.
2. **Outline against the chapter anatomy** in `references/writing-standard.md`. List the figures, tables, exercises and references the chapter needs before writing prose.
3. **Draw the figures** as SVG in `figures/src/` (`references/figures-svg.md`). Build previews and *look at each one* before using it.
4. **Write the chapter** in `chapters/chNN-<slug>.tex`, following `references/writing-standard.md` for voice and structure and `references/latex-conventions.md` for markup. For a long chapter, write it section by section.
5. **Write the exercises and solutions** (`references/exercises-and-references.md`). Solutions go in `solutions/chNN.tex`, and both are wired into `main.tex`. Add each verified reference to `refs.bib`.
6. **Build**: `bash <skill-dir>/scripts/build.sh <book-root>`. This converts the SVGs, compiles, renders every page to `build/pages/`, and writes `build/check-report.md`. Fix every error, then deal with every warning: fix it, or have a stated reason to leave it.
7. **Review**, using all three passes in `references/review.md`:
   - **A. Mechanical**: the check report is clean.
   - **B. Visual**: open the page images and inspect every page of the new chapter, and at least every page the report lists as holding a figure or table. Check that figures are present, legible, unclipped and near where they're referenced; tables fit and align; listings don't overflow; boxes and headings break sensibly across pages.
   - **C. Quality**: score the chapter against the rubric and `benchmark.md`. Is it truly polished enough to sit beside the best-selling guide on this topic? If a reviewer subagent is available, use one that has seen only the rendered pages, the rubric and the benchmark, not your drafting context, so the work isn't grading itself.
8. **Revise until it passes**: zero build errors, a visually clean layout, and every rubric dimension at 4 or above. Rebuild after each round of fixes.
9. **Deliver.** Update `book-state.md` (with a changelog line) and the learner state. Send the learner the PDF with one line on what's new. Mention that the `.tex` sources are theirs to edit.

When a later unit changes how an earlier idea should be explained, for example a better mental model or a corrected simplification, revise the earlier chapter too, and note it in the changelog.

## Converting to PDF themselves

The learner can rebuild at any time with `bash build.sh <book-root>` or `latexmk -pdf main.tex` in the book root. The generated figure PDFs in `figures/build/` are kept, so the book also compiles on Overleaf, which can't convert SVGs itself. Tell them this the first time you deliver a book.

## Reference files

- `references/writing-standard.md`: the voice, the chapter anatomy, turning chat into book prose, and what "polished" means sentence by sentence.
- `references/latex-conventions.md`: file layout, every macro and environment in `mastery-book.sty`, listings, tables, cross-references and escaping.
- `references/figures-svg.md`: when a figure earns its place, SVG authoring rules for clean PDF conversion, the palette, and figure types.
- `references/exercises-and-references.md`: the exercise mix and solutions, the reference types, BibTeX entries, and verification.
- `references/review.md`: the mechanical, visual and quality review passes, the rubric, and building the bestseller benchmark.
