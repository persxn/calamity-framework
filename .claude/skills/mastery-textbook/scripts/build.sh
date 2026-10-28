#!/usr/bin/env bash
# Build a mastery study book: SVG -> PDF figures, compile LaTeX, render pages, run checks.
# Usage: bash build.sh <book-root>     (book-root contains main.tex)
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${1:-.}" && pwd)"
cd "$ROOT" || exit 2
[ -f main.tex ] || { echo "ERROR: no main.tex in $ROOT"; exit 2; }

mkdir -p figures/src figures/build build/pages build/figpreview
# \include writes .aux files into matching sub-directories of the output dir.
find . -name '*.tex' -not -path './build/*' -printf '%h\n' | sort -u | while read -r d; do mkdir -p "build/$d"; done

# ---------- 1. Figures: SVG -> PDF (+ PNG preview) ----------
convert_svg() { # $1 svg, $2 out, $3 format (pdf|png)
  if command -v rsvg-convert >/dev/null 2>&1; then
    rsvg-convert -f "$3" -o "$2" "$1"
  elif command -v inkscape >/dev/null 2>&1; then
    inkscape "$1" --export-type="$3" --export-filename="$2" >/dev/null 2>&1
  elif python3 -c 'import cairosvg' >/dev/null 2>&1; then
    python3 -c "import sys,cairosvg; f=getattr(cairosvg,'svg2'+sys.argv[3]); f(url=sys.argv[1], write_to=sys.argv[2], **({'output_width':1400} if sys.argv[3]=='png' else {}))" "$1" "$2" "$3"
  else
    echo "ERROR: no SVG converter. Install one of: librsvg (rsvg-convert), inkscape, or 'pip install cairosvg'"; return 3
  fi
}
fig_fail=0
shopt -s nullglob
for svg in figures/src/*.svg; do
  name="$(basename "$svg" .svg)"
  pdf="figures/build/$name.pdf"; png="build/figpreview/$name.png"
  if [ ! -f "$pdf" ] || [ "$svg" -nt "$pdf" ]; then
    if convert_svg "$svg" "$pdf" pdf; then echo "figure: $name"
    else echo "ERROR: figure $name failed to convert to PDF"; fig_fail=1; fi
  fi
  if [ ! -f "$png" ] || [ "$svg" -nt "$png" ]; then
    convert_svg "$svg" "$png" png || echo "WARN: no PNG preview for $name"
  fi
done

# ---------- 2. Compile ----------
[ -f calamity.sty ] || echo "WARN: calamity.sty is missing beside main.tex: copy framework/design/calamity.sty here"
if command -v latexmk >/dev/null 2>&1; then
  BIBINPUTS="$ROOT:" latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error \
    -outdir=build main.tex > build/latexmk.out 2>&1
  status=$?
elif command -v pdflatex >/dev/null 2>&1; then
  run() { pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -output-directory=build main.tex > build/pdflatex.out 2>&1; }
  run && { (cd build && BIBINPUTS="$ROOT:" bibtex main > bibtex.out 2>&1 || true); run && run; }
  status=$?
elif command -v tectonic >/dev/null 2>&1; then
  # Tectonic runs BibTeX and the reruns itself, and fetches the packages Calamity Paper needs
  tectonic -X compile --keep-logs --outdir build main.tex > build/tectonic.out 2>&1
  status=$?
else
  echo "ERROR: no TeX engine. Install TeX Live (latexmk, pdflatex, bibtex) or Tectonic"; status=2
fi
if [ $status -ne 0 ]; then
  echo "ERROR: LaTeX compile failed (exit $status). First errors:"
  grep -m 8 -E '^(.*:[0-9]+: |! )' build/main.log 2>/dev/null || tail -20 build/latexmk.out 2>/dev/null
fi

# ---------- 3. Render pages for visual review ----------
if [ -f build/main.pdf ]; then
  rm -f build/pages/*.png
  pdftoppm -r 80 -png build/main.pdf build/pages/page >/dev/null 2>&1 || echo "WARN: pdftoppm missing; cannot render pages"
  echo "pdf: $ROOT/build/main.pdf ($(pdfinfo build/main.pdf 2>/dev/null | awk '/^Pages/{print $2}') pages)"
fi

# ---------- 4. Checks ----------
python3 "$HERE/check_build.py" "$ROOT"
check=$?
[ $status -ne 0 ] || [ $fig_fail -ne 0 ] && exit 1
exit $check
