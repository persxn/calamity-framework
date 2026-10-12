"""Front matter and section parsing for the framework's markdown files.

The files are markdown with a small, strict YAML subset on top:

    ---
    id: docker
    prereqs: [linux-shell, git-gh]
    est_hours: 20
    optional: false
    gate.papers: [CS, DA]        # dotted keys are plain flat keys
    ---

Supported values: strings (bare or quoted), integers, floats, true/false,
null, inline lists `[a, b]`, and block lists (`key:` followed by `- item`
lines). Nested maps and multi-line strings are not supported on purpose:
every file must stay trivially machine-readable.

Entry sections use headings:

    # Topics
    ## multi-stage | Multi-stage builds
    needs: [images, dockerfile]
    level: 2
    Free markdown body ...
"""
from __future__ import annotations

import json
import re

from .util import CalError

_KEY_RE = re.compile(r"^([A-Za-z0-9_][A-Za-z0-9_.\-]*)\s*:(?:\s+(.*)|\s*)$")
_INT_RE = re.compile(r"^[+-]?\d+$")
_FLOAT_RE = re.compile(r"^[+-]?(\d+\.\d*|\.\d+|\d+)([eE][+-]?\d+)?$")
_BARE_OK = re.compile(r"^[A-Za-z0-9_./+@()%<>=~^$*-][A-Za-z0-9_./+@()%<>=~^$* -]*$")


class FrontMatterError(CalError):
    pass


def _strip_comment(value: str) -> str:
    """Remove a trailing ' # comment' that is outside quotes and brackets."""
    quote = None
    depth = 0
    for i, ch in enumerate(value):
        if quote:
            if ch == "\\" and quote == '"':
                continue
            if ch == quote and (i == 0 or value[i - 1] != "\\"):
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch == "[":
            depth += 1
        elif ch == "]":
            depth = max(0, depth - 1)
        elif ch == "#" and depth == 0 and (i == 0 or value[i - 1] in " \t"):
            return value[:i].rstrip()
    return value.rstrip()


def _scalar(text: str):
    s = text.strip()
    if s == "":
        return None
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        try:
            return json.loads(s)
        except ValueError:
            return s[1:-1]
    if len(s) >= 2 and s[0] == "'" and s[-1] == "'":
        return s[1:-1].replace("''", "'")
    low = s.lower()
    if low in ("true", "yes"):
        return True
    if low in ("false", "no"):
        return False
    if low in ("null", "~", "none"):
        return None
    if _INT_RE.match(s):
        try:
            return int(s)
        except ValueError:
            return s
    if _FLOAT_RE.match(s):
        try:
            return float(s)
        except ValueError:
            return s
    return s


def _split_list(inner: str):
    items, buf, quote = [], [], None
    for ch in inner:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            buf.append(ch)
        elif ch == ",":
            items.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    tail = "".join(buf)
    if tail.strip() or items:
        items.append(tail)
    return [x for x in (i.strip() for i in items) if x != ""]


def parse_value(text: str):
    s = _strip_comment(text).strip()
    if s.startswith("["):
        if not s.endswith("]"):
            raise FrontMatterError("unterminated list: %s" % text.strip())
        return [_scalar(x) for x in _split_list(s[1:-1])]
    if s.startswith("{"):
        raise FrontMatterError("nested maps are not supported: %s" % text.strip())
    if s in ("|", ">", "|-", ">-"):
        raise FrontMatterError("multi-line strings are not supported")
    return _scalar(s)


def parse_kv_lines(lines, where: str = "", first_line: int = 1):
    """Parse 'key: value' lines (with optional block lists) into a dict."""
    meta = {}
    key_for_block = None
    empty_blocks = set()  # keys written as 'key:' that never received a '- item'
    for offset, raw in enumerate(lines):
        line = raw.rstrip("\r\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        stripped = line.strip()
        if stripped.startswith("- ") or stripped == "-":
            if key_for_block is None:
                raise FrontMatterError(
                    "%s line %d: list item without a key" % (where, first_line + offset)
                )
            item = _scalar(_strip_comment(stripped[1:]))
            if item is not None:
                meta[key_for_block].append(item)
            empty_blocks.discard(key_for_block)
            continue
        m = _KEY_RE.match(stripped)
        if not m:
            raise FrontMatterError(
                "%s line %d: expected 'key: value', got %r" % (where, first_line + offset, stripped)
            )
        key, value = m.group(1), m.group(2)
        if value is None or _strip_comment(value).strip() == "":
            meta[key] = []
            key_for_block = key
            empty_blocks.add(key)
            continue
        key_for_block = None
        empty_blocks.discard(key)
        try:
            meta[key] = parse_value(value)
        except FrontMatterError as exc:
            raise FrontMatterError("%s line %d: %s" % (where, first_line + offset, exc))
    for key in empty_blocks:  # 'key:' with nothing under it means null
        meta[key] = None
    return meta


def split(text: str):
    """Return (front_matter_lines, body, body_start_line)."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if text.startswith("﻿"):
        text = text[1:]
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return [], text, 1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return lines[1:i], "\n".join(lines[i + 1 :]), i + 2
    raise FrontMatterError("front matter starts with '---' but never closes")


def parse(text: str, where: str = ""):
    """Parse a markdown file into (meta dict, body str)."""
    fm_lines, body, _ = split(text)
    meta = parse_kv_lines(fm_lines, where=where, first_line=2) if fm_lines else {}
    return meta, body


def load(path):
    with open(path, "r", encoding="utf-8") as fh:
        return parse(fh.read(), where=str(path))


# ------------------------------------------------------------------ dumping


def _dump_scalar(value) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    s = str(value)
    plain = (
        s != ""
        and _BARE_OK.match(s)
        and s == s.strip()
        and not _INT_RE.match(s)
        and not _FLOAT_RE.match(s)
        and s.lower() not in ("true", "false", "yes", "no", "null", "none", "~")
        and ": " not in s
        and " #" not in s
        and "," not in s
        and not s.endswith(":")
        and s[0] not in "-*"
    )
    return s if plain else json.dumps(s, ensure_ascii=False)


def dump_value(value) -> str:
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(_dump_scalar(v) for v in value) + "]"
    return _dump_scalar(value)


def dump(meta: dict, body: str = "") -> str:
    lines = ["---"]
    for key, value in meta.items():
        lines.append("%s: %s" % (key, dump_value(value)))
    lines.append("---")
    body = body.lstrip("\n")
    return "\n".join(lines) + "\n" + (("\n" + body) if body else "")


# ------------------------------------------------------------------ sections

_H1_RE = re.compile(r"^#\s+(.+?)\s*$")
_H2_RE = re.compile(r"^##\s+(.+?)\s*$")


def section(body: str, name: str):
    """Return (lines, first_line_index) of the '# <name>' section, or (None, 0)."""
    lines = body.split("\n")
    start = None
    in_fence = False
    for i, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        if in_fence:
            continue
        m = _H1_RE.match(line)
        if not m:
            continue
        if start is not None:
            return lines[start:i], start
        if m.group(1).strip().lower() == name.lower():
            start = i + 1
    if start is None:
        return None, 0
    return lines[start:], start


def section_text(body: str, name: str) -> str:
    lines, _ = section(body, name)
    return "\n".join(lines).strip() if lines else ""


def entries(body: str, name: str, allowed_keys, where: str = ""):
    """Parse '## id | Title' entries of a '# <name>' section.

    Returns a list of dicts: {id, title, meta, body, line}. Lines directly
    under the heading that look like 'key: value' with an allowed key are the
    entry's metadata; everything after the first other line is its body.
    """
    lines, _ = section(body, name)
    if lines is None:
        return []
    allowed = set(allowed_keys)
    out, current, in_meta, in_fence = [], None, False, False

    def close():
        if current is not None:
            current["body"] = "\n".join(current.pop("_body")).strip()
            try:
                current["meta"] = parse_kv_lines(current.pop("_meta"), where=where)
            except FrontMatterError as exc:
                raise FrontMatterError("%s entry '%s': %s" % (where, current["id"], exc))
            out.append(current)

    for n, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        m = None if in_fence else _H2_RE.match(line)
        if m:
            close()
            head = m.group(1)
            if "|" in head:
                ident, title = head.split("|", 1)
            else:
                ident, title = head, ""
            ident = ident.strip().strip("`")
            title = title.strip() or ident.replace("-", " ").capitalize()
            current = {"id": ident, "title": title, "_meta": [], "_body": [], "line": n + 1}
            in_meta = True
            continue
        if current is None:
            continue
        if in_meta:
            km = _KEY_RE.match(line.strip())
            if km and km.group(1) in allowed:
                current["_meta"].append(line)
                continue
            if not line.strip() and not current["_meta"] and not current["_body"]:
                continue
            in_meta = False
        current["_body"].append(line)
    close()
    return out


def render_entry(ident: str, title: str, meta: dict, body: str = "") -> str:
    lines = ["## %s | %s" % (ident, title)]
    for key, value in meta.items():
        if value is None or value == [] or value == "":
            continue
        lines.append("%s: %s" % (key, dump_value(value)))
    if body.strip():
        lines.append(body.strip())
    return "\n".join(lines) + "\n"
