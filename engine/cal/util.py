"""Small shared helpers: time, ids, text formatting.

Standard library only. Python 3.9+.
"""
from __future__ import annotations

import math
import os
import re
import secrets
import sys
from datetime import datetime, timedelta, timezone

_B32 = "0123456789abcdefghjkmnpqrstvwxyz"  # Crockford, lower case


class CalError(Exception):
    """A user-facing error. The CLI prints the message and exits with code 2."""


# ---------------------------------------------------------------- time


def parse_ts(text: str) -> datetime:
    """Parse an ISO-8601 timestamp. Naive values are taken as local time."""
    s = str(text).strip()
    if s.endswith("Z") or s.endswith("z"):
        s = s[:-1] + "+00:00"
    if len(s) == 10:  # a bare date
        s += "T00:00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.astimezone()
    return dt


def now() -> datetime:
    """Current local time, timezone-aware. CALAMITY_NOW overrides it (tests)."""
    env = os.environ.get("CALAMITY_NOW")
    if env:
        return parse_ts(env)
    return datetime.now().astimezone()


def iso(dt: datetime) -> str:
    return dt.isoformat(timespec="milliseconds")


def utc(dt: datetime) -> datetime:
    return dt.astimezone(timezone.utc)


def daykey(dt: datetime, start_hour: int = 4) -> str:
    """The learner's 'day' a moment belongs to. Days roll over at start_hour,
    measured in the local offset the timestamp was recorded with."""
    return (dt - timedelta(hours=start_hour)).date().isoformat()


def day_bounds(dt: datetime, start_hour: int = 4):
    """(start, end) datetimes of the learner day containing dt."""
    shifted = dt - timedelta(hours=start_hour)
    start = shifted.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(hours=start_hour)
    return start, start + timedelta(days=1)


def parse_hhmm(text) -> int | None:
    """'23:30' -> minutes since midnight, or None."""
    m = re.match(r"^\s*(\d{1,2}):(\d{2})\s*$", str(text or ""))
    if not m:
        return None
    h, mi = int(m.group(1)), int(m.group(2))
    if h > 23 or mi > 59:
        return None
    return h * 60 + mi


def in_window(minute_of_day: int, start: int, end: int) -> bool:
    """Is a minute-of-day inside [start, end), where the window may wrap midnight?"""
    if start == end:
        return False
    if start < end:
        return start <= minute_of_day < end
    return minute_of_day >= start or minute_of_day < end


def minutes_until(minute_of_day: int, target: int) -> int:
    return (target - minute_of_day) % 1440


# ---------------------------------------------------------------- ids


def new_id(prefix: str = "") -> str:
    """Time-ordered unique id (48-bit ms time + 50 random bits, base32)."""
    ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    out = []
    for _ in range(10):
        out.append(_B32[ms & 31])
        ms >>= 5
    head = "".join(reversed(out))
    tail = "".join(_B32[secrets.randbelow(32)] for _ in range(10))
    return prefix + head + tail


def short_id(prefix: str = "") -> str:
    return prefix + "".join(_B32[secrets.randbelow(32)] for _ in range(10))


_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slug(text: str, max_len: int = 48) -> str:
    s = _SLUG_RE.sub("-", str(text).lower()).strip("-")
    return s[:max_len].strip("-") or "x"


SKILL_ID_RE = re.compile(r"^[a-z0-9][a-z0-9.+-]*$")
TOPIC_ID_RE = re.compile(r"^[a-z0-9][a-z0-9+-]*$")


def split_key(key: str):
    """'skill/topic' -> (skill, topic)."""
    if "/" not in key:
        raise CalError("topic keys look like <skill>/<topic>; got %r" % key)
    skill, topic = key.split("/", 1)
    return skill, topic


# ---------------------------------------------------------------- text


def csv_list(value) -> list:
    """'a, b,c' or ['a','b'] -> ['a','b','c'] (empty items dropped)."""
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        items = value
    else:
        items = str(value).split(",")
    return [str(x).strip() for x in items if str(x).strip()]


def bar(fraction: float, width: int = 10, ascii_only: bool = False) -> str:
    fraction = 0.0 if fraction != fraction else max(0.0, min(1.0, fraction))
    filled = int(round(fraction * width))
    if ascii_only:
        return "#" * filled + "." * (width - filled)
    return "█" * filled + "░" * (width - filled)


def pct(fraction: float) -> str:
    return "%d%%" % int(round(100 * fraction))


def fmt_minutes(minutes: float) -> str:
    minutes = int(round(minutes))
    if minutes < 60:
        return "%dm" % minutes
    return "%dh%02dm" % (minutes // 60, minutes % 60)


def fmt_delta(delta: timedelta) -> str:
    """Human 'in 3d' / '2h ago' style distance for a signed timedelta."""
    secs = delta.total_seconds()
    ago = secs < 0
    secs = abs(secs)
    if secs < 90:
        body = "now" if secs < 45 else "1m"
    elif secs < 5400:
        body = "%dm" % round(secs / 60)
    elif secs < 36 * 3600:
        body = "%dh" % round(secs / 3600)
    else:
        body = "%dd" % round(secs / 86400)
    if body == "now":
        return "now"
    return body + " ago" if ago else "in " + body


def truncate(text: str, width: int) -> str:
    text = " ".join(str(text).split())
    if len(text) <= width:
        return text
    return text[: max(1, width - 1)].rstrip() + "…"


def table(rows, headers=None, aligns=None, max_width=None) -> str:
    """Render a simple padded text table. aligns: string of 'l'/'r' per column."""
    rows = [[("" if c is None else str(c)) for c in r] for r in rows]
    if headers:
        rows = [list(map(str, headers))] + rows
    if not rows:
        return ""
    ncol = max(len(r) for r in rows)
    for r in rows:
        r.extend([""] * (ncol - len(r)))
    widths = [max(len(r[i]) for r in rows) for i in range(ncol)]
    if max_width:
        over = sum(widths) + 2 * (ncol - 1) - max_width
        if over > 0:
            widest = max(range(ncol), key=lambda i: widths[i])
            widths[widest] = max(8, widths[widest] - over)
    aligns = aligns or "l" * ncol
    lines = []
    for n, r in enumerate(rows):
        cells = []
        for i, c in enumerate(r):
            c = truncate(c, widths[i]) if len(c) > widths[i] else c
            cells.append(c.rjust(widths[i]) if aligns[i : i + 1] == "r" else c.ljust(widths[i]))
        lines.append("  ".join(cells).rstrip())
        if headers and n == 0:
            lines.append("  ".join("-" * w for w in widths))
    return "\n".join(lines)


def wrap_cells(cells, width: int, indent: str = "  ", first: str | None = None) -> list:
    """Lay short cells out in lines no wider than `width`. `first` replaces the indent of line one."""
    lines, line = [], (indent if first is None else first)
    for cell in cells:
        if len(line) + len(cell) > width and line.strip() and line not in (indent, first):
            lines.append(line.rstrip())
            line = indent
        line += cell + "   "
    if line.strip():
        lines.append(line.rstrip())
    return lines


_ASCII = {"·": "|", "…": "...", "─": "-", "█": "#", "░": ".", "✓": "#", "◕": "+", "◐": "~", "○": "o",
          "‖": "=", "✗": "x", "—": "-", "–": "-"}


def to_ascii(text: str) -> str:
    """Plain-ASCII form of engine output, for terminals that cannot show anything else."""
    for src, dst in _ASCII.items():
        text = text.replace(src, dst)
    return text.encode("ascii", "replace").decode("ascii")


def term_width(default: int = 80) -> int:
    env = os.environ.get("COLUMNS")
    try:
        if env:
            return max(40, min(120, int(env)))
    except ValueError:
        pass
    try:
        import shutil

        return max(40, min(120, shutil.get_terminal_size((default, 24)).columns))
    except Exception:
        return default


def ceil_int(x: float) -> int:
    return int(math.ceil(x - 1e-9))


def utf8_stdio() -> None:
    """Make stdout/stderr UTF-8 everywhere (Windows consoles default to a legacy code page)."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
