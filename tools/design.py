"""Calamity Paper: write the design system's outputs from framework/design/tokens.json.

    python3 tools/design.py            write the outputs
    python3 tools/design.py --check    exit 1 when an output differs from what the tokens give (the tests run this)
    python3 tools/design.py --qa DIR   build qa/notebook.tex, qa/book.tex and qa/cheatsheet.tex with every TeX engine installed
                                       (Tectonic, pdfLaTeX, XeLaTeX, LuaLaTeX) into DIR, with a PNG of each page

Outputs, all in framework/design/ (generated: never edit them, edit tokens.json or src/):

    calamity.sty             the LaTeX package (notebook and book options), from src/calamity.sty.in
    calamity.css             custom properties for light and dark, fonts, type scale, callout classes
    palette.svg              every colour and callout, light and dark, labelled
    ../../.claude-plugin/icon.png   the plugin's icon, from the accent and amber of the light palette
    calamity-terminal.json   two terminal colour schemes (Windows Terminal's scheme format; the 16 ANSI
                             colours in order, which other terminals take as well)

Standard library only, deterministic (the date comes from the tokens), LF line endings.
"""
import argparse
import json
import shutil
import subprocess
import tempfile
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESIGN = os.path.join(ROOT, "framework", "design")
# Colour names the notes preamble and mastery-book.sty used: sections written for them keep building.
COMPAT = (("calrule", "calRule"), ("calidea", "calAccent!7!white"), ("calwarn", "calAmber!7!white"),
          ("calcode", "calSurface"), ("calkey", "calCodeKeyword"), ("calstr", "calCodeString"),
          ("calcom", "calCodeComment"), ("mbInk", "calInk"), ("mbAccent", "calAccent"), ("mbTeal", "calTeal"),
          ("mbAmber", "calAmber"), ("mbRed", "calRed"), ("mbViolet", "calViolet"), ("mbGreen", "calGreen"),
          ("mbSlate", "calSlate"), ("mbPaper", "calPaper"), ("mbCodeBg", "calSurface"))
ANSI = ("black", "red", "green", "yellow", "blue", "purple", "cyan", "white")


def load() -> dict:
    with open(os.path.join(DESIGN, "tokens.json"), "r", encoding="utf-8") as fh:
        return json.load(fh)


def camel(key: str) -> str:
    return "cal" + "".join(part.capitalize() for part in key.split("_"))


def tex_colour(key: str) -> str:
    return camel(key)


def sty(t: dict) -> str:
    with open(os.path.join(DESIGN, "src", "calamity.sty.in"), "r", encoding="utf-8") as fh:
        text = fh.read()
    f = t["fonts"]
    otf = []
    for role, cmd, extra in (("body", "setmainfont", ""), ("sans", "setsansfont", ",Scale=MatchLowercase"),
                             ("mono", "setmonofont", ",Scale=MatchLowercase")):
        family, up, bold, it, bi = f[role]["otf"]
        otf.append("  \\IfFontExistsTF{%s%s.otf}{\\%s{%s}[Extension=.otf,UprightFont=*%s,BoldFont=*%s,ItalicFont=*%s,"
                   "BoldItalicFont=*%s%s]}{}" % (family, up, cmd, family, up, bold, it, bi, extra))
    math_pkg, math_opt = f["math"]["pdflatex"].split(":")
    tokens = ["\\definecolor{%s}{HTML}{%s}" % (tex_colour(k), v) for k, v in t["palette"]["light"].items()]
    tokens += ["\\colorlet{%s}{%s}" % pair for pair in COMPAT]
    callouts = []
    for c in t["callouts"]:
        callouts.append("\\cal@callout{%s}{%s}{%s}" % (c["env"], c["label"], tex_colour(c["colour"])))
        for alias in c.get("aliases", []):
            callouts.append("\\cal@alias{%s}{%s}" % (alias, c["env"]))
    s = t["space"]
    fill = {
        "%%FONTNAMES%%": "%s body, %s headings, %s code, %s" % (f["body"]["name"], f["sans"]["name"],
                                                                f["mono"]["name"], f["math"]["name"]),
        "%%DATE%%": t["date"].replace("-", "/"), "%%VERSION%%": str(t["version"]),
        "%%PDF_BODY%%": f["body"]["pdflatex"], "%%PDF_SANS%%": f["sans"]["pdflatex"],
        "%%PDF_MONO%%": f["mono"]["pdflatex"], "%%PDF_MATH_PKG%%": math_pkg, "%%PDF_MATH_OPT%%": math_opt,
        "%%OTF_FONTS%%": "\n".join(otf), "%%OTF_MATH%%": f["math"]["otf"],
        "%%TOKENS%%": "\n".join(tokens), "%%CALLOUTS%%": "\n".join(callouts),
        "%%TINT%%": str(int(round(t["tint"] * 100))), "%%EDGE%%": str(s["box_edge"]),
        "%%PADX%%": str(s["box_pad_x"]), "%%PADY%%": str(s["box_pad_y"]), "%%GAP%%": str(s["box_gap"]),
    }
    for key, value in fill.items():
        if key not in text:
            raise SystemExit("src/calamity.sty.in has no %s" % key)
        text = text.replace(key, value)
    left = re.search(r"%%[A-Z_]+%%", text)
    if left:
        raise SystemExit("an unfilled marker is left: %s" % left.group(0))
    return text


def mix(hex_colour: str, base: str, share: float) -> str:
    """`share` of hex_colour over base, as hex (what xcolor's c!N!white does)."""
    a = [int(hex_colour[i:i + 2], 16) for i in (0, 2, 4)]
    b = [int(base[i:i + 2], 16) for i in (0, 2, 4)]
    return "".join("%02X" % round(x * share + y * (1 - share)) for x, y in zip(a, b))


def css(t: dict) -> str:
    f, ty = t["fonts"], t["type"]
    lines = ["/* calamity.css: the Calamity Paper design system for HTML (dash --html, study pages, the portfolio).",
             "   GENERATED by tools/design.py from framework/design/tokens.json: edit that, never this file. */", ""]

    def block(selector, palette, share):
        """Custom properties for one palette; a callout's tint is `share` of its colour over the paper."""
        out = ["%s {" % selector]
        out += ["  --cal-%s: #%s;" % (k.replace("_", "-"), v) for k, v in palette.items()]
        for c in sorted({c["colour"] for c in t["callouts"]}):
            out.append("  --cal-%s-tint: #%s;" % (c, mix(palette[c], palette["paper"], share)))
        out.append("}")
        return out

    light, dark = t["palette"]["light"], t["palette"]["dark"]
    dark_tint = 2 * t["tint"]          # a dark page needs a stronger tint for the box to show
    lines += block(":root", light, t["tint"])
    lines += ["@media (prefers-color-scheme: dark) {"]
    lines += ["  " + l for l in block(":root:not([data-theme=\"light\"])", dark, dark_tint)]
    lines += ["}"]
    lines += block(":root[data-theme=\"dark\"]", dark, dark_tint)
    lines += ["", ":root {",
              "  --cal-font-body: %s;" % f["body"]["css"],
              "  --cal-font-sans: %s;" % f["sans"]["css"],
              "  --cal-font-mono: %s;" % f["mono"]["css"],
              "  --cal-size: %.4gpx;" % (ty["base_pt"] * 4 / 3 * 1.1),
              "  --cal-line: %s;" % ty["line"]]
    lines += ["  --cal-scale-%s: %s;" % (k, v) for k, v in ty["scale"].items()]
    lines += ["  --cal-space: %dpx;" % round(t["space"]["unit_pt"] * 4 / 3), "}", ""]
    lines += [
        "body { margin: 0; padding: 24px 16px; background: var(--cal-paper); color: var(--cal-ink);",
        "  font: var(--cal-size)/var(--cal-line) var(--cal-font-body); }",
        "main, .cal-page { max-width: 46rem; margin: 0 auto; }",
        "h1, h2, h3, h4 { font-family: var(--cal-font-sans); font-weight: 600; line-height: 1.2; margin: 1.2em 0 0.4em; }",
        "h1 { font-size: calc(var(--cal-scale-h1) * 1em); }",
        "h2 { font-size: calc(var(--cal-scale-h2) * 1em); }",
        "h3 { font-size: calc(var(--cal-scale-h3) * 1em); }",
        "small, .cal-muted { color: var(--cal-muted); font-size: calc(var(--cal-scale-small) * 1em); }",
        "a { color: var(--cal-accent); }",
        "code, kbd, pre { font-family: var(--cal-font-mono); font-size: 0.92em; }",
        "pre { background: var(--cal-surface); border-left: 2px solid var(--cal-rule); padding: 8px 10px;",
        "  overflow-x: auto; white-space: pre; }",
        "table { border-collapse: collapse; margin: 0.6em 0; }",
        "th { font-family: var(--cal-font-sans); text-align: left; border-bottom: 1px solid var(--cal-ink); }",
        "th, td { padding: 3px 10px 3px 0; } tr:last-child td { border-bottom: 1px solid var(--cal-ink); }",
        ".callout { background: var(--edge-tint); border-left: %spx solid var(--edge); padding: %spx %spx;"
        % (round(t["space"]["box_edge"] * 4 / 3, 1), round(t["space"]["box_pad_y"] * 4 / 3),
           round(t["space"]["box_pad_x"] * 4 / 3)),
        "  margin: %spx 0; }" % round(t["space"]["box_gap"] * 4 / 3),
        ".callout > .label { font-family: var(--cal-font-sans); font-weight: 600; color: var(--edge); }",
    ]
    for c in t["callouts"]:
        names = ", ".join(".callout.%s" % n for n in [c["env"], c["kind"]] + c.get("aliases", []) if n)
        lines.append("%s { --edge: var(--cal-%s); --edge-tint: var(--cal-%s-tint); }" % (names, c["colour"], c["colour"]))
    lines.append(".callout.definition { --edge: var(--cal-accent); --edge-tint: var(--cal-accent-tint); }")
    return "\n".join(lines) + "\n"


def svg(t: dict) -> str:
    light, dark = t["palette"]["light"], t["palette"]["dark"]
    keys = list(light)
    w, sw, gap = 132, 120, 12
    cols = 5
    rows = (len(keys) + cols - 1) // cols
    height = 60 + 2 * (rows * 64 + 40) + 40 + len(t["callouts"]) * 0 + 70
    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" '
           'font-family="Fira Sans, sans-serif" font-size="11">' % (cols * w + 24, height, cols * w + 24, height),
           '<!-- GENERATED by tools/design.py from framework/design/tokens.json -->',
           '<rect width="100%%" height="100%%" fill="#%s"/>' % light["paper"],
           '<text x="12" y="28" font-size="16" font-weight="600" fill="#%s">%s · palette v%d</text>'
           % (light["ink"], t["name"], t["version"])]
    y0 = 50
    for title, pal, bg in (("light", light, light["paper"]), ("dark", dark, dark["paper"])):
        block_h = rows * 64 + 30
        out.append('<rect x="6" y="%d" width="%d" height="%d" rx="4" fill="#%s"/>' % (y0, cols * w + 12, block_h, bg))
        out.append('<text x="14" y="%d" font-weight="600" fill="#%s">%s</text>' % (y0 + 18, pal["ink"], title))
        for i, k in enumerate(keys):
            x, y = 14 + (i % cols) * w, y0 + 26 + (i // cols) * 64
            out.append('<rect x="%d" y="%d" width="%d" height="28" rx="3" fill="#%s" stroke="#%s" stroke-width="0.5"/>'
                       % (x, y, sw, pal[k], pal["rule"]))
            out.append('<text x="%d" y="%d" fill="#%s">%s #%s</text>' % (x, y + 42, pal["ink"], k, pal[k]))
        y0 += block_h + 10
    out.append('<text x="12" y="%d" font-weight="600" fill="#%s">callouts</text>' % (y0 + 14, light["ink"]))
    x = 12
    y = y0 + 24
    for c in t["callouts"]:
        label = c["label"]
        width = 8 * len(label) // 1 + 16
        if x + width > cols * w + 12:
            x, y = 12, y + 26
        out.append('<rect x="%d" y="%d" width="%d" height="20" fill="#%s"/><rect x="%d" y="%d" width="3" height="20" '
                   'fill="#%s"/><text x="%d" y="%d" fill="#%s" font-weight="600">%s</text>'
                   % (x, y, width, mix(light[c["colour"]], light["paper"], t["tint"]), x, y, light[c["colour"]],
                      x + 8, y + 14, light[c["colour"]], label.replace("'", "&#8217;")))
        x += width + 8
    out.append("</svg>")
    text = "\n".join(out) + "\n"
    last = y + 30
    return text.replace('height="%d" viewBox="0 0 %d %d"' % (height, cols * w + 24, height),
                        'height="%d" viewBox="0 0 %d %d"' % (last, cols * w + 24, last))


def terminal(t: dict) -> str:
    schemes = []
    for mode in ("light", "dark"):
        pal, colours = t["palette"][mode], t["terminal"][mode]
        scheme = {"name": "Calamity Paper %s" % mode.capitalize(), "background": "#" + pal["paper"],
                  "foreground": "#" + pal["ink"], "cursorColor": "#" + pal["accent"],
                  "selectionBackground": "#" + mix(pal["accent"], pal["paper"], 0.25)}
        for i, name in enumerate(ANSI):
            scheme[name] = "#" + colours[i]
            scheme["bright" + name.capitalize()] = "#" + colours[8 + i]
        schemes.append(scheme)
    return json.dumps({"note": "GENERATED by tools/design.py from framework/design/tokens.json. Windows Terminal: "
                               "add these to \"schemes\" in settings.json. Other terminals: the 16 ANSI colours "
                               "are black, red, green, yellow, blue, purple (magenta), cyan, white, then the bright "
                               "ones in the same order.", "schemes": schemes}, indent=2, ensure_ascii=False) + "\n"


def icon(t: dict, size: int = 512) -> bytes:
    """The plugin's icon (.claude-plugin/icon.png): a ring open to the right, a C, in the accent on the paper of the
    light palette, with a small amber dot in the opening. A PNG written with zlib, antialiased by supersampling."""
    import struct
    import zlib

    pal = t["palette"]["light"]
    rgb = lambda h: tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))      # noqa: E731
    paper, accent, dot = rgb(pal["paper"]), rgb(pal["accent"]), rgb(pal["amber"])
    c, outer, inner, dot_r = size / 2.0, size * 0.36, size * 0.24, size * 0.06
    dot_c = (c + (outer + inner) / 2.0 * 0.92, c)
    rows = []
    for y in range(size):
        row = bytearray([0])
        for x in range(size):
            acc = [0, 0, 0]
            for sy in (0.25, 0.75):
                for sx in (0.25, 0.75):
                    px, py = x + sx - c, y + sy - c
                    r = (px * px + py * py) ** 0.5
                    colour = paper
                    if inner <= r <= outer and not (px > 0 and abs(py) < size * 0.11):
                        colour = accent
                    dx, dy = x + sx - dot_c[0], y + sy - dot_c[1]
                    if dx * dx + dy * dy <= dot_r * dot_r:
                        colour = dot
                    acc = [a + b for a, b in zip(acc, colour)]
            row += bytes(round(v / 4) for v in acc)
        rows.append(bytes(row))

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(b"".join(rows), 9)) + chunk(b"IEND", b""))


ICON = os.path.join(ROOT, ".claude-plugin", "icon.png")


def png_pixels(data: bytes):
    """(header, decompressed image data) of a PNG: compared instead of the bytes, which differ between zlib builds
    (Python 3.14 on Windows ships zlib-ng) for the same pixels."""
    import struct
    import zlib

    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("not a PNG")
    pos, header, idat = 8, None, b""
    while pos < len(data):
        length, kind = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + length]
        if kind == b"IHDR":
            header = body
        elif kind == b"IDAT":
            idat += body
        pos += 12 + length
    return header, zlib.decompress(idat)


def outputs(t: dict) -> dict:
    return {"calamity.sty": sty(t), "calamity.css": css(t), "palette.svg": svg(t), "calamity-terminal.json": terminal(t)}


def stale() -> list:
    """Outputs that differ from what the tokens give (missing ones included)."""
    out = []
    for name, text in outputs(load()).items():
        path = os.path.join(DESIGN, name)
        try:
            with open(path, "r", encoding="utf-8", newline="") as fh:
                if fh.read() == text:
                    continue
        except OSError:
            pass
        out.append(name)
    try:
        with open(ICON, "rb") as fh:
            if png_pixels(fh.read()) != png_pixels(icon(load())):
                out.append(".claude-plugin/icon.png")
    except (OSError, ValueError):
        out.append(".claude-plugin/icon.png")
    return out


ENGINES = (("tectonic", ["tectonic", "-X", "compile"]),
           ("pdflatex", ["pdflatex", "-interaction=nonstopmode", "-halt-on-error"]),
           ("xelatex", ["xelatex", "-interaction=nonstopmode", "-halt-on-error"]),
           ("lualatex", ["lualatex", "-interaction=nonstopmode", "-halt-on-error"]))


def qa(out: str) -> int:
    """Build the QA documents with each engine found; 1 when one fails, 2 when no engine is installed."""
    found = [(n, argv) for n, argv in ENGINES if shutil.which(argv[0])]
    if not found:
        print("no TeX engine found (Tectonic, pdfLaTeX, XeLaTeX or LuaLaTeX)")
        return 2
    os.makedirs(out, exist_ok=True)
    failed = 0
    for doc in ("notebook", "book", "cheatsheet"):
        for name, argv in found:
            work = tempfile.mkdtemp(prefix="calamity-qa-")
            try:
                shutil.copyfile(os.path.join(DESIGN, "calamity.sty"), os.path.join(work, "calamity.sty"))
                shutil.copyfile(os.path.join(DESIGN, "qa", doc + ".tex"), os.path.join(work, doc + ".tex"))
                for _ in range(1 if name == "tectonic" else 2):          # a second pass resolves references
                    proc = subprocess.run(argv + [doc + ".tex"], cwd=work, stdout=subprocess.PIPE,
                                          stderr=subprocess.STDOUT)
                pdf = os.path.join(work, doc + ".pdf")
                if proc.returncode != 0 or not os.path.isfile(pdf):
                    failed += 1
                    errors = [l for l in proc.stdout.decode("utf-8", "replace").splitlines()
                              if l.startswith(("!", "error"))][:3]
                    print("FAILED %s on %s: %s" % (doc, name, " | ".join(errors)))
                    continue
                target = os.path.join(out, "%s.%s.pdf" % (doc, name))
                shutil.copyfile(pdf, target)
                if shutil.which("pdftoppm"):
                    subprocess.run(["pdftoppm", "-png", "-r", "80", target, target[:-4]], check=False)
                print("built %s" % target)
            finally:
                shutil.rmtree(work, ignore_errors=True)
    return 1 if failed else 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--check", action="store_true", help="exit 1 when an output differs from the tokens")
    p.add_argument("--qa", metavar="DIR", help="build the QA documents with every TeX engine installed into DIR")
    a = p.parse_args(argv)
    if a.qa:
        return qa(os.path.abspath(a.qa))
    if a.check:
        bad = stale()
        if bad:
            print("out of date (run python3 tools/design.py): %s" % ", ".join(bad))
            return 1
        print("design outputs match the tokens")
        return 0
    for name, text in outputs(load()).items():
        with open(os.path.join(DESIGN, name), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print("wrote framework/design/%s" % name)
    with open(ICON, "wb") as fh:
        fh.write(icon(load()))
    print("wrote .claude-plugin/icon.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
