"""Opportunity records found on the web: for now GATE mock tests (the opportunity-scout's gate-mocks beat).

A record says what was found, where, when it was fetched and what the site's terms allowed. Nothing is
recommended from memory: a record without a source URL, a fetch date and a terms note is refused. The
gate-strategist reads them for the mock calendar. This is the minimal form of the career schema (WP-25 grows
it to jobs, internships and events).

Events: career_add (one record; a record with the same kind and url replaces the earlier one).
"""
from __future__ import annotations

import hashlib
from datetime import date

from .store import Repo
from .util import CalError, table

KINDS = ("gate-mock",)
MODES = ("online", "offline", "both")
FIELDS = ("kind", "title", "provider", "url", "source", "fetched", "terms", "mode", "city", "dates", "cost", "note")
REQUIRED = ("kind", "title", "url", "source", "fetched", "terms")
STALE_DAYS = 30


def record_id(kind: str, url: str) -> str:
    return "op-" + hashlib.sha1(("%s|%s" % (kind, url)).encode("utf-8")).hexdigest()[:8]


def check(row, when) -> dict:
    if not isinstance(row, dict):
        raise CalError("each record is a JSON object")
    extra = set(row) - set(FIELDS)
    if extra:
        raise CalError("unknown field(s) %s; a record holds %s" % (", ".join(sorted(extra)), ", ".join(FIELDS)))
    missing = [k for k in REQUIRED if not str(row.get(k) or "").strip()]
    if missing:
        raise CalError("%r lacks %s: every record names its source, the day it was fetched and what the site's "
                       "terms allowed" % (row.get("title") or "a record", ", ".join(missing)))
    if row["kind"] not in KINDS:
        raise CalError("kind is one of %s" % ", ".join(KINDS))
    for key in ("url", "source"):
        if not str(row[key]).startswith(("https://", "http://")):
            raise CalError("%s must be a web address (https://...), got %r" % (key, row[key]))
    try:
        fetched = date.fromisoformat(str(row["fetched"]))
    except ValueError:
        raise CalError("fetched is the day it was read, such as 2026-10-28; got %r" % row["fetched"])
    if fetched > when.date():
        raise CalError("fetched %s is in the future" % fetched)
    mode = row.get("mode")
    if mode is not None and mode not in MODES:
        raise CalError("mode is one of %s" % ", ".join(MODES))
    if mode in ("offline", "both") and not str(row.get("city") or "").strip():
        raise CalError("an offline mock names its centre's city")
    out = {k: (str(row[k]).strip() if not isinstance(row[k], (int, float)) else row[k]) for k in FIELDS
           if row.get(k) not in (None, "")}
    out["fetched"] = fetched.isoformat()
    for k in ("title", "note", "terms"):
        if len(str(out.get(k, ""))) > 300:
            raise CalError("%s is a line, not a page (300 characters at most)" % k)
    return out


def add(repo: Repo, rows, when) -> str:
    if isinstance(rows, dict):
        rows = [rows]
    if not isinstance(rows, list) or not rows:
        raise CalError("career add takes a JSON list of records")
    clean = [check(r, when) for r in rows]          # all or none
    for rec in clean:
        repo.append("career_add", id=record_id(rec["kind"], rec["url"]), **rec)
    return "recorded %d record(s): %s" % (len(clean), ", ".join(record_id(r["kind"], r["url"]) for r in clean))


def list_text(state, when, kind: str | None = None) -> str:
    rows = [r for r in state.career.values() if not kind or r["kind"] == kind]
    if not rows:
        return "No records%s yet. The opportunity-scout agent finds them (gate skill: \"find mocks\")." % (
            (" of kind %s" % kind) if kind else "")
    out = []
    for r in sorted(rows, key=lambda r: (r["kind"], r.get("mode") or "", r["title"])):
        age = (when.date() - date.fromisoformat(r["fetched"])).days
        out.append([r["id"], r["kind"], r["title"][:40], r.get("provider", "")[:24], r.get("mode", "-"),
                    r.get("city", "-"), r.get("dates", "-")[:24],
                    r["fetched"] + (" (stale)" if age > STALE_DAYS else "")])
    return table(out, ["id", "kind", "title", "provider", "mode", "city", "dates", "fetched"]) + \
        "\nEach record carries its source and terms note (career show <id>). Older than %d days: check again." \
        % STALE_DAYS


def show_text(state, ident: str) -> str:
    r = state.career.get(ident)
    if r is None:
        raise CalError("unknown record %s (career list)" % ident)
    return "\n".join("%s: %s" % (k, r[k]) for k in ("id",) + FIELDS if k in r)
