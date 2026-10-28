# Figures in SVG

Every diagram is a hand-written SVG in `figures/src/`, converted to PDF by `build.sh`. The SVG is the source of truth: edit it, never the PDF.

## When a figure earns its place

Draw one when the reader needs to *see* structure, flow or change over time. Examples: a memory layout, a process tree, a request's path through layers, a state machine, a timeline of an outage, a before-and-after comparison, the data structure behind a command. Don't draw a figure that only restates a sentence. Aim for one strong figure per major mechanism; most chapters need two to five.

Each figure teaches **one idea**. Its caption says what to notice: "Notice that the name lives in the directory, not the inode."

## Authoring rules (these make the PDF conversion reliable)

- **Canvas**: `viewBox="0 0 800 H"`, with `width="800" height="H"`. 800 wide maps to the text width. Keep a 20-unit margin inside the edges, and make sure nothing sits outside the viewBox (it gets clipped, and the check flags it).
- **Text**: put `font-family="Fira Sans, Helvetica, Arial, sans-serif"` on the root `<svg>` (Fira Sans is the books' heading face; the others stand in where it is not installed). Labels are 14–16, titles 18, and **nothing below 14**: at 800 wide, 14 units is about 7pt on the page (the check warns below that). For code inside figures, use `font-family="Fira Mono, Courier New, monospace"` at 14 or more.
- **Supported features only**: basic shapes, `<path>`, `<text>`, `<g>`, `<defs>` with `<marker>` for arrowheads, `<linearGradient>` sparingly, and `transform`. **Not allowed**: `<foreignObject>`, CSS variables (`var(--x)`), `@import` or web fonts, external `href`s, embedded scripts, filters and blur (converters vary).
- **Explicit colours** on every element (`fill`, `stroke`). Give the root a white background `<rect>`.
- **Arrows**: define one `<marker id="arrow">` in `<defs>` and use `marker-end="url(#arrow)"`. Leave a 2–4 unit gap between an arrow's end and its target.
- **Alignment**: use `text-anchor="middle"` to centre labels in boxes. Use a 10-unit grid for positions, so boxes line up.
- **Name** it `chNN-<what>.svg`; the name becomes the `\svgfigure` argument.

## Palette (matches the book's callout colours)

| Role | Stroke | Fill |
|---|---|---|
| Primary structure (blue) | `#1F4E8C` | `#EFF3F7` |
| Mechanism or internals (teal) | `#0F766E` | `#EEF5F5` |
| Data or storage (amber) | `#A4511B` | `#F9F3EF` |
| Danger, failure, the key insight (red) | `#B42318` | `#FAF0EF` |
| Neutral, arrows, notes (slate) | `#475569` | `#F2F3F4` |
| Success, a result (green) | `#3B6E3B` | `#F1F5F1` |
| Text | `#1F2328` | — |

These are the Calamity Paper tokens (`framework/design/tokens.json`; `framework/design/palette.svg` shows them all), so a figure matches the callouts beside it.

Colour should carry meaning, used the same way in every figure. The figure must still read in greyscale, so use labels and shapes as well as colour.

## Figure types and tips

- **Memory and layout**: a vertical stack of cells with addresses on the left (monospace), low addresses at the bottom unless the text says otherwise, and brackets showing regions.
- **Layers (hardware → kernel → tool)**: horizontal bands, with a request drawn as a numbered path through them.
- **Sequence**: actors across the top, time going down, and numbered messages that match numbered steps in the prose.
- **State machine**: rounded states, labelled transitions, and the initial state marked.
- **Timeline (outages, history)**: a horizontal axis with dated ticks, and the decision point marked in red.
- **Before and after**: the same layout twice, side by side, with the difference highlighted.
- **Data structure**: boxes and pointers, with real values from the chapter's running example.

## Check every figure, every time

After `build.sh`, open `build/figpreview/<name>.png` and look at it. Check:

- Nothing is clipped at the edges, and no text overlaps a line, an arrow or other text.
- Arrows start and end where they should, and their heads are visible.
- Text is readable at the preview size. If it's hard to read there, it's too small in the PDF.
- Labels are spelled correctly, and values match the prose and listings exactly.
- It still makes sense in greyscale.

Then find it on its page in `build/pages/`. Check it sits near its first reference, is sized sensibly, and its caption is complete.
