#!/usr/bin/env python3
"""Mechanical checks for a mastery study book.

Usage: python3 check_build.py <book-root>
Writes build/check-report.md and prints it. Exit 1 if any ERROR was found.

What it checks:
  - LaTeX log: errors, undefined references/citations, missing figures, overfull boxes,
    font substitutions, rerun warnings
  - BibTeX log: missing entries, warnings
  - PDF text: unresolved "??", MISSING FIGURE markers; which pages hold figures and tables
  - Figures: referenced but missing, SVG sources never used
  - SVG lint: viewBox, unsupported features, tiny text after scaling, text outside the canvas
  - Exercises without solutions, solutions for missing exercises
  - Citation keys missing from refs.bib, web entries without an access date
  - Tables with vertical rules or no caption; leftover TODO / <<placeholders>>
"""
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
BUILD = ROOT / "build"
errors, warns, infos = [], [], []

TEXT_WIDTH_PT = 411.0      # 0.92\linewidth on the template's A4 text block
MIN_FONT_PT = 7.0          # smallest legible figure text once scaled into the page
OVERFULL_LIMIT_PT = 1.0

tex_files = sorted(p for p in ROOT.rglob("*.tex") if BUILD not in p.parents)
tex_src = {p: p.read_text(errors="replace") for p in tex_files}


def rel(p):
    return str(Path(p).relative_to(ROOT)) if str(p).startswith(str(ROOT)) else str(p)


def strip_comments(s):
    return re.sub(r"(?<!\\)%.*", "", s)


# ---------------- LaTeX log ----------------
log_path = BUILD / "main.log"
if not log_path.exists():
    errors.append("No build/main.log — the document has not been compiled.")
    log = ""
else:
    log = log_path.read_text(errors="replace")
    for m in re.finditer(r"^(\./[^\n:]+:\d+: .+|! .+)$", log, re.M):
        errors.append(f"LaTeX: {m.group(1).strip()}")
    for m in re.finditer(r"(Reference|Citation) `([^']+)' on page (\d+) undefined", log):
        errors.append(f"Undefined {m.group(1).lower()} `{m.group(2)}` (page {m.group(3)})")
    for m in re.finditer(r"MISSING FIGURE (\S+)", log):
        errors.append(f"Missing figure file for `{m.group(1)}` (figures/build/{m.group(1)}.pdf)")
    for m in re.finditer(r"Overfull \\hbox \((\d+(?:\.\d+)?)pt too wide\) (?:in paragraph|detected) at lines? (\d+)(?:--(\d+))?", log):
        amt = float(m.group(1))
        if amt > OVERFULL_LIMIT_PT:
            snippet = log[m.end():m.end() + 160].strip().splitlines()
            snippet = snippet[0][:90] if snippet else ""
            (errors if amt > 15 else warns).append(
                f"Overfull hbox {amt:.1f}pt at line {m.group(2)} — text runs into the margin: `{snippet}`")
    for m in re.finditer(r"Overfull \\vbox \((\d+(?:\.\d+)?)pt too high\)", log):
        if float(m.group(1)) > 2:
            warns.append(f"Overfull vbox {m.group(1)}pt — something is taller than the page (big table/figure/box?)")
    for m in re.finditer(r"Float too large for page by ([\d.]+)pt", log):
        errors.append(f"Float too large for page by {m.group(1)}pt — shrink the figure or split the table")
    if re.search(r"Label\(s\) may have changed|Rerun to get", log):
        warns.append("LaTeX asks for a rerun; rebuild before reviewing.")
    subs = sorted(set(re.findall(r"Font shape `([^']+)' undefined", log)))
    if subs:
        infos.append("Font substitutions: " + ", ".join(subs))

blg = BUILD / "main.blg"
if blg.exists():
    for line in blg.read_text(errors="replace").splitlines():
        if re.search(r"error message|I was expecting|I'm skipping|missing a field|I couldn't open", line):
            errors.append(f"BibTeX: {line.strip()}  (see build/main.blg)")
        elif line.startswith("Warning--") or "I didn't find" in line:
            warns.append(f"BibTeX: {line.strip()}")

# ---------------- PDF text ----------------
pdf = BUILD / "main.pdf"
fig_pages, table_pages = {}, {}
if pdf.exists():
    try:
        txt = subprocess.run(["pdftotext", "-layout", str(pdf), "-"],
                             capture_output=True, text=True, check=True).stdout
        pages = txt.split("\f")
        for i, page in enumerate(pages, 1):
            if "??" in page:
                errors.append(f"`??` printed on page {i} — unresolved reference or citation")
            if "MISSING FIGURE" in page:
                errors.append(f"MISSING FIGURE placeholder printed on page {i}")
            for kind, num in re.findall(r"\b(Figure|Table) (\d+\.\d+):", page):
                (fig_pages if kind == "Figure" else table_pages)[num] = i
        infos.append(f"PDF has {len(pages) - (1 if pages and not pages[-1].strip() else 0)} pages")
        # Long flags must survive typesetting literally (no "--" -> dash ligature, no lost characters).
        flat = re.sub(r"\s+", "", txt)
        flags = set()
        for s in tex_src.values():
            for m in re.finditer(r"\\(?:cmd|flag)\{([^}]*)\}", strip_comments(s)):
                flags.update(re.findall(r"--[A-Za-z][\w=-]*", m.group(1)))
        mangled = sorted(f for f in flags if f not in flat)
        if mangled:
            errors.append("Long flags not printed literally in the PDF (dash ligature or lost text): "
                          + ", ".join(mangled[:12]))
    except (OSError, subprocess.CalledProcessError):
        warns.append("pdftotext unavailable — skipped PDF text checks")
else:
    errors.append("No build/main.pdf produced.")

# ---------------- Figures ----------------
src_dir, out_dir = ROOT / "figures/src", ROOT / "figures/build"
used = set()
for p, s in tex_src.items():
    s = strip_comments(s)
    for m in re.finditer(r"\\svgfigure(?:\[[^\]]*\])?\{([^}]+)\}", s):
        used.add(m.group(1))
        if not (src_dir / f"{m.group(1)}.svg").exists():
            errors.append(f"{rel(p)}: figure `{m.group(1)}` has no SVG source in figures/src/")
    for m in re.finditer(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", s):
        if "#" in m.group(1):
            continue
        target = ROOT / m.group(1)
        if not target.exists() and not target.with_suffix(".pdf").exists():
            errors.append(f"{rel(p)}: \\includegraphics target `{m.group(1)}` not found")
for svg in sorted(src_dir.glob("*.svg")):
    if svg.stem not in used:
        warns.append(f"figures/src/{svg.name} is never used in the book")

# ---------------- SVG lint ----------------
NS = "{http://www.w3.org/2000/svg}"


def num(v, default=None):
    try:
        return float(re.match(r"-?[\d.]+", str(v)).group(0))
    except (AttributeError, ValueError, TypeError):
        return default


for svg in sorted(src_dir.glob("*.svg")):
    name = f"figures/src/{svg.name}"
    raw = svg.read_text(errors="replace")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as e:
        errors.append(f"{name}: not valid XML ({e})")
        continue
    vb = root.get("viewBox")
    if not vb:
        errors.append(f"{name}: no viewBox — it will not scale cleanly")
        continue
    vx, vy, vw, vh = (float(x) for x in re.split(r"[ ,]+", vb.strip()))
    scale = TEXT_WIDTH_PT / vw
    if "foreignObject" in raw:
        errors.append(f"{name}: <foreignObject> does not render in PDF converters — use <text>")
    if "var(--" in raw:
        errors.append(f"{name}: CSS variables do not render in PDF converters — use literal colours")
    if re.search(r'href="https?://', raw):
        errors.append(f"{name}: links to an external resource — embed or redraw it")
    if "@import" in raw or "@font-face" in raw:
        warns.append(f"{name}: web fonts/imports are ignored by converters; use generic font families")
    parent_font = {}
    for el in root.iter():
        for child in el:
            parent_font[child] = el
    def inherited(el, attr):
        while el is not None:
            v = el.get(attr)
            if v is None:
                m = re.search(attr + r"\s*:\s*([^;]+)", el.get("style", ""))
                v = m.group(1) if m else None
            if v is not None:
                return v
            el = parent_font.get(el)
        return None
    small, outside = 0, 0
    for t in root.iter(f"{NS}text"):
        fs = num(inherited(t, "font-size"), 16.0)
        if fs * scale < MIN_FONT_PT:
            small += 1
        x, y = num(t.get("x")), num(t.get("y"))
        has_transform = any(a.get("transform") for a in [t, parent_font.get(t)] if a is not None)
        if x is not None and y is not None and not has_transform:
            if x < vx - 1 or x > vx + vw + 1 or y < vy - 1 or y > vy + vh + 1:
                outside += 1
    if small:
        warns.append(f"{name}: {small} text element(s) smaller than {MIN_FONT_PT}pt once scaled to the page "
                     f"(viewBox width {vw:g}; raise font-size or shrink the viewBox)")
    if outside:
        errors.append(f"{name}: {outside} text element(s) positioned outside the viewBox — they will be clipped")

# ---------------- Exercises and solutions ----------------
ex_labels, sol_labels = {}, {}
for p, s in tex_src.items():
    s = strip_comments(s)
    for m in re.finditer(r"\\begin\{exercise\}(?:\[[^\]]*\])?\s*(\{([^}]+)\})?", s):
        if m.group(2):
            ex_labels[m.group(2)] = rel(p)
        else:
            line = s[:m.start()].count("\n") + 1
            errors.append(f"{rel(p)}:{line}: exercise without its label argument — write \\begin{{exercise}}[n]{{ex:...}}")
    for m in re.finditer(r"\\begin\{solution\}\{([^}]+)\}", s):
        sol_labels[m.group(1)] = rel(p)
for lab, where in ex_labels.items():
    if lab not in sol_labels:
        warns.append(f"{where}: exercise `{lab}` has no solution")
for lab, where in sol_labels.items():
    if lab not in ex_labels:
        errors.append(f"{where}: solution for `{lab}`, but no exercise has that label")

# ---------------- Citations ----------------
bib = ROOT / "refs.bib"
bib_text = bib.read_text(errors="replace") if bib.exists() else ""
bib_keys = set(re.findall(r"^\s*@\w+\s*\{\s*([^,\s]+)\s*,", strip_comments(bib_text), re.M))
cited = set()
for s in tex_src.values():
    for m in re.finditer(r"\\cite[pt]?\*?(?:\[[^\]]*\])*\{([^}]+)\}", strip_comments(s)):
        cited.update(k.strip() for k in m.group(1).split(","))
for k in sorted(cited - bib_keys):
    errors.append(f"Cited key `{k}` is not in refs.bib")
for m in re.finditer(r"@misc\s*\{\s*([^,\s]+)\s*,(.*?)\n\}", strip_comments(bib_text), re.S | re.I):
    if "url" in m.group(2).lower() and "accessed" not in m.group(2).lower():
        warns.append(f"refs.bib `{m.group(1)}`: web source without an access date (note = {{Accessed YYYY-MM-DD}})")

# ---------------- Tables, leftovers ----------------
for p, s in tex_src.items():
    s_nc = strip_comments(s)
    for m in re.finditer(r"\\begin\{(tabular|tabularx|longtable)\}(?:\{[^}]*\})?\{([^}]*)\}", s_nc):
        if "|" in m.group(2):
            line = s_nc[:m.start()].count("\n") + 1
            warns.append(f"{rel(p)}:{line}: table uses vertical rules — house style is booktabs, no verticals")
    for m in re.finditer(r"\\begin\{table\}(.*?)\\end\{table\}", s_nc, re.S):
        if "\\caption" not in m.group(1):
            line = s_nc[:m.start()].count("\n") + 1
            warns.append(f"{rel(p)}:{line}: table without a caption")
    for m in re.finditer(r"TODO|FIXME|XXX|<<[^>]+>>", s_nc):
        line = s_nc[:m.start()].count("\n") + 1
        warns.append(f"{rel(p)}:{line}: leftover `{m.group(0)}`")

# ---------------- Report ----------------
def section(title, items):
    if not items:
        return f"## {title}\nnone\n"
    seen, out = set(), []
    for i in items:
        if i not in seen:
            seen.add(i)
            out.append(f"- {i}")
    return f"## {title} ({len(out)})\n" + "\n".join(out) + "\n"

inspect = sorted(set(fig_pages.values()) | set(table_pages.values()))
lines = [f"# Build check — {ROOT.name}\n",
         section("Errors", errors), section("Warnings", warns), section("Info", infos),
         "## Pages to inspect visually",
         ("Figures: " + ", ".join(f"{k}→p{v}" for k, v in sorted(fig_pages.items(), key=lambda kv: kv[1]))) if fig_pages else "Figures: none found in PDF",
         ("Tables: " + ", ".join(f"{k}→p{v}" for k, v in sorted(table_pages.items(), key=lambda kv: kv[1]))) if table_pages else "Tables: none found in PDF",
         f"Page images: build/pages/page-NN.png  (pages {', '.join(map(str, inspect)) or '—'})",
         "Figure previews: build/figpreview/<name>.png\n"]
report = "\n".join(lines)
BUILD.mkdir(exist_ok=True)
(BUILD / "check-report.md").write_text(report)
print(report)
sys.exit(1 if errors else 0)
