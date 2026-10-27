"""What a profile value may be: the profile keys the engine reads, and overrides of config.md.

`profile set` turns the words it is given into a value through `parse`, which refuses what
the engine could not use later. `coerce_cfg` is the same check for a `cfg.<key>` override
that is already stored (written by hand, or by an older version): `Repo.config` uses the
default for a bad one and reports it, so that a typo never takes every command down.
"""
from __future__ import annotations

import re
from datetime import date

from . import fm
from .util import CalError, csv_list, parse_hhmm

# Lists: comma-separated words become a list.
LIST_KEYS = ("tracks", "goals", "focus", "gate.papers", "reminders.times")
# Free text: stored exactly as given, commas and all.
TEXT_KEYS = ("name", "teach.style", "gate.target_source", "cp.language", "cp.handle")

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# Ranges for configuration overrides: (lowest, highest), either end may be None.
CFG_RANGES = {
    "day_start_hour": (0, 12), "new_per_day": (0, 200), "new_per_day_max": (0, 200),
    "review_budget_min": (1, 1440), "review_secs": (5, 3600), "lectures_per_day": (0, 100),
    "sleep_guard_minutes": (0, 600), "session_gap_minutes": (1, 600),
    "retention.mastery": (0.5, 0.99), "retention.brushup": (0.5, 0.99), "gate.final_retention": (0.5, 0.99),
    "max_interval_days": (1, 36500), "relearn_minutes": (1, 1440),
    "time.hard_factor": (1.0, 20.0), "time.easy_factor": (0.0, 1.0),
    "solid.min_correct": (1, 50), "solid.min_days": (1, 30), "solid.window": (1, 12), "solid.min_accuracy": (0.0, 1.0),
    "solid.objective_coverage": (0.0, 1.0), "mastered.objective_coverage": (0.0, 1.0),
    "solid.min_stability": (0.0, 3650.0), "mastered.min_stability": (0.0, 3650.0), "mastered.min_items": (1, 50),
    "ready_share": (0.0, 1.0), "brushup.ready_share": (0.0, 1.0), "recall_n": (0, 30), "weave_n": (0, 6),
    "gate.daily_hours": (0.5, 24.0), "gate.exam_clamp_days": (0, 60), "gate.final_phase_days": (0, 180),
    "cp.band_low": (-1000, 2000), "cp.band_high": (-1000, 2000), "cp.resolve_days": (1, 365),
    "cp.credit_days": (1, 365), "cp.band_lookahead": (0, 3000), "coach.cooldown_days": (0, 60),
    "pace.mastery.wip": (1, 50), "pace.exam.wip": (1, 50), "pace.brushup.wip": (1, 50),
    "pace.mastery.consolidate_minutes": (0, 1440), "pace.exam.consolidate_minutes": (0, 1440),
    "pace.brushup.consolidate_minutes": (0, 1440),
    "numericals.target": (1, 200),
    "pace.mastery.new_max": (0, 200), "pace.exam.new_max": (0, 200), "pace.brushup.new_max": (0, 200),
}
FIXED_CFG = ("schema",)
PACES = ("mastery", "exam", "brushup")       # the pace profiles in config.md (pace.<name>.*)


def coerce_cfg(key: str, value, defaults: dict):
    """The override for config key `key` converted to the type of its default. Raises CalError."""
    if key in FIXED_CFG:
        raise CalError("cfg.%s cannot be overridden" % key)
    if key.startswith("pace.track.") and len(key) > len("pace.track."):   # any track, a learner's own included
        if str(value).strip() not in PACES:
            raise CalError("cfg.%s is one of %s, got %r" % (key, ", ".join(PACES), value))
        return str(value).strip()
    if key not in defaults:
        close = [k for k in sorted(defaults) if k.split(".")[-1] == key.split(".")[-1] or key in k][:3]
        raise CalError("framework/config.md has no setting %r%s" % (
            key, (" (did you mean %s?)" % ", ".join(close)) if close else ""))
    default = defaults[key]
    if isinstance(default, bool):
        if isinstance(value, bool):
            return value
        if str(value).strip().lower() in ("true", "yes", "on", "1"):
            return True
        if str(value).strip().lower() in ("false", "no", "off", "0"):
            return False
        raise CalError("cfg.%s is true or false, got %r" % (key, value))
    if isinstance(default, (int, float)):
        if isinstance(value, bool) or isinstance(value, list):
            raise CalError("cfg.%s is a number, got %r" % (key, value))
        try:
            number = float(value)
        except (TypeError, ValueError):
            raise CalError("cfg.%s is a number, got %r" % (key, value))
        if number != number:
            raise CalError("cfg.%s is a number, got %r" % (key, value))
        low, high = CFG_RANGES.get(key, (None, None))
        # A whole-number default is a count unless its range says fractions make sense (6 hours, 7.5 hours).
        if isinstance(default, int) and not isinstance(low, float) and not isinstance(high, float):
            if not number.is_integer():
                raise CalError("cfg.%s is a whole number, got %r" % (key, value))
            number = int(number)
        if (low is not None and number < low) or (high is not None and number > high):
            raise CalError("cfg.%s must be between %s and %s, got %s" % (key, low, high, value))
        return number
    if key.startswith("pace.") and key.endswith(".unlock") and str(value).strip() not in ("consolidating", "learning"):
        raise CalError("cfg.%s is consolidating or learning, got %r" % (key, value))
    return value


def _date(key: str, text: str) -> str:
    if not _DATE_RE.match(text):
        raise CalError("%s is a date like 2027-02-07, got %r" % (key, text))
    try:
        date.fromisoformat(text)
    except ValueError:
        raise CalError("%s: %r is not a real date" % (key, text))
    return text


def _number(key: str, text: str, low: float, high: float, whole: bool = False):
    try:
        value = float(text)
    except ValueError:
        raise CalError("%s is a number, got %r" % (key, text))
    if whole and not value.is_integer():
        raise CalError("%s is a whole number, got %r" % (key, text))
    if not low <= value <= high:
        raise CalError("%s must be between %s and %s, got %s" % (key, _plain(low), _plain(high), text))
    return int(value) if whole or value.is_integer() else value


def _plain(x):
    return int(x) if float(x).is_integer() else x


# Keys the engine reads (besides cfg.<setting>), as documented in framework/rules/engine.md.
KNOWN_KEYS = ("name", "onboarded", "tracks", "goals", "focus", "mode.default", "teach.style", "sleep.start",
              "sleep.end", "workout.minutes", "daily.target_hours", "reminders.times", "gate.year", "gate.papers",
              "gate.registered", "gate.target_rank", "gate.target_source", "cp.handle", "cp.target_rating",
              "cp.target_date", "cp.language", "book.format", "stock.at")
KNOWN_PREFIXES = ("cfg.", "gate.target_marks.", "gate.exam_date.")


def known(key: str) -> bool:
    return key in KNOWN_KEYS or key.startswith(KNOWN_PREFIXES)


def parse(key: str, words, text: bool, defaults: dict):
    """The value `profile set KEY WORDS...` stores, or None for "none" (which unsets the key).
    Raises CalError for a value the engine cannot use."""
    words = [str(w) for w in words]
    joined = " ".join(words).strip()
    if not joined:
        raise CalError("usage: profile set <key> <value>")
    if not text and key not in TEXT_KEYS and not key.startswith("cfg.") and joined.lower() in ("none", "null"):
        return None  # "no reminders", "no focus": the same as unsetting the key
    if key.startswith("cfg."):
        return coerce_cfg(key[4:], fm.parse_value(joined), defaults)
    if text or key in TEXT_KEYS:
        return joined
    if key in LIST_KEYS:
        inner = joined[1:-1] if joined.startswith("[") and joined.endswith("]") else joined
        items = [fm.parse_value(v) for v in csv_list(inner.replace(" ", ","))]
        if key == "reminders.times":
            for t in items:
                if parse_hhmm(t) is None:
                    raise CalError("reminders.times are times like 09:00,14:00; got %r" % (t,))
        if key == "gate.papers":
            items = [str(p).upper() for p in items]
            for p in items:
                if not re.match(r"^[A-Z]{2}$", p):
                    raise CalError("gate.papers are two-letter paper codes such as CS or DA; got %r" % p)
        return items
    if key in ("sleep.start", "sleep.end", "stock.at"):
        if parse_hhmm(joined) is None:
            raise CalError("%s is a time like 23:30, got %r" % (key, joined))
        return joined
    if key in ("onboarded", "gate.registered"):
        value = fm.parse_value(joined)
        if not isinstance(value, bool):
            raise CalError("%s is true or false, got %r" % (key, joined))
        return value
    if key == "book.format":
        if joined not in ("markdown", "pdf"):
            raise CalError("book.format is markdown (the default) or pdf, got %r" % joined)
        return joined
    if key == "mode.default":
        if joined not in ("mastery", "brushup"):
            raise CalError("mode.default is mastery or brushup, got %r" % joined)
        return joined
    if key == "workout.minutes":
        return _number(key, joined, 0, 600, whole=True)
    if key == "daily.target_hours":
        return _number(key, joined, 0, 24)
    if key == "gate.year":
        return _number(key, joined, 2000, 2100, whole=True)
    if key == "gate.target_rank":
        return _number(key, joined, 1, 10 ** 7, whole=True)
    if key.startswith("gate.target_marks."):
        return _number(key, joined, 0, 100)
    if key == "cp.target_rating":
        return _number(key, joined, 0, 5000, whole=True)
    if key.startswith("gate.exam_date.") or key == "cp.target_date":
        return _date(key, joined)
    if "," in joined and not joined.startswith("["):
        return [fm.parse_value(v) for v in csv_list(joined)]
    return fm.parse_value(joined)
