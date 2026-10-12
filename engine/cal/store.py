"""Repository layout, configuration, learner profile and the append-only event log.

The event log is the single source of truth for progress. Every machine
appends to its own file (learner/events/<YYYY-MM>.<machine>.jsonl), so two
machines never edit the same file and git merges cleanly. All derived
numbers (schedules, mastery, dashboards) are recomputed by replaying it.
"""
from __future__ import annotations

import json
import os
import re
import socket
import tempfile
import time

from . import fm
from .util import CalError, iso, new_id, now, parse_ts, slug, utc

SCHEMA = 1
_MACHINE_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,31}$")
_last_q = 0  # write order within this process (see Repo.append)


def _next_q() -> int:
    """A number that grows with every event written on this machine: wall-clock microseconds,
    nudged forward when two events fall in the same microsecond."""
    global _last_q
    _last_q = max(_last_q + 1, time.time_ns() // 1000)
    return _last_q


def _order_key(event: dict):
    q = event.get("q")
    return (utc(event["_dt"]), str(event["m"]), q if isinstance(q, int) else 0, str(event["id"]))


def _engine_dir() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def write_text(path: str, text: str) -> None:
    """Write a file atomically with LF newlines and UTF-8."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".tmp-", dir=os.path.dirname(path) or ".")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


class Repo:
    """Paths plus cached access to config, profile and events."""

    def __init__(self, root: str | None = None):
        real_root = os.path.dirname(_engine_dir())
        self.root = os.path.abspath(root or os.environ.get("CALAMITY_ROOT") or real_root)
        env_fw = os.environ.get("CALAMITY_FRAMEWORK")
        own_fw = os.path.join(self.root, "framework")
        if env_fw:
            self.framework = os.path.abspath(env_fw)
        elif os.path.isdir(own_fw):
            self.framework = own_fw
        else:
            self.framework = os.path.join(real_root, "framework")
        self.learner = os.path.join(self.root, "learner")
        self.local = os.path.join(self.root, ".calamity")
        self.events_dir = os.path.join(self.learner, "events")
        self.items_dir = os.path.join(self.learner, "items")
        self.syllabus_dir = os.path.join(self.learner, "syllabus")
        self.tree_dir = os.path.join(self.learner, "tree")
        self.sources_dir = os.path.join(self.learner, "sources")
        self.notes_dir = os.path.join(self.learner, "notes")
        self.cache_dir = os.path.join(self.local, "cache")
        self.profile_path = os.path.join(self.learner, "profile.md")
        self._config = None
        self._profile = None
        self._profile_body = ""
        self._events = None
        self.event_errors = []
        self.memo = {}  # files parsed during this command (sources, exam facts); cleared by invalidate()

    # ------------------------------------------------------------ paths

    def rel(self, path: str) -> str:
        try:
            return os.path.relpath(path, self.root).replace(os.sep, "/")
        except ValueError:
            return path

    def ensure_dirs(self) -> None:
        for d in (
            self.events_dir,
            self.items_dir,
            self.syllabus_dir,
            self.tree_dir,
            self.sources_dir,
            self.notes_dir,
            os.path.join(self.learner, "work"),
            os.path.join(self.learner, "cp", "solutions"),
            self.cache_dir,
            os.path.join(self.local, "tmp"),
        ):
            os.makedirs(d, exist_ok=True)

    # ------------------------------------------------------------ config

    def config(self) -> dict:
        if self._config is None:
            path = os.path.join(self.framework, "config.md")
            meta = {}
            if os.path.isfile(path):
                meta, _ = fm.load(path)
            for key, value in self.profile().items():
                if key.startswith("cfg."):
                    meta[key[4:]] = value
            self._config = meta
        return self._config

    def cfg(self, key: str, default=None):
        value = self.config().get(key, default)
        return default if value is None else value

    # ------------------------------------------------------------ profile

    def profile(self) -> dict:
        if self._profile is None:
            if os.path.isfile(self.profile_path):
                self._profile, self._profile_body = fm.load(self.profile_path)
            else:
                self._profile, self._profile_body = {}, ""
        return self._profile

    def prof(self, key: str, default=None):
        value = self.profile().get(key, default)
        return default if value is None else value

    def onboarded(self) -> bool:
        return bool(self.prof("onboarded", False))

    def save_profile(self, meta: dict) -> None:
        self.profile()
        body = self._profile_body or (
            "# Notes about this learner\n\n"
            "Free-form notes on what helps this learner. The tutor reads this file;\n"
            "keys above the line are set with `profile set`.\n"
        )
        ordered = dict(sorted(meta.items()))
        os.makedirs(self.learner, exist_ok=True)
        write_text(self.profile_path, fm.dump(ordered, body).rstrip("\n") + "\n")
        self._profile, self._profile_body, self._config = ordered, body, None
        self.memo = {}

    def set_profile(self, key: str, value) -> None:
        if not re.match(r"^[A-Za-z0-9_][A-Za-z0-9_.\-]*$", key):
            raise CalError("bad profile key %r" % key)
        meta = dict(self.profile())
        if value is None:
            meta.pop(key, None)
        else:
            meta[key] = value
        self.save_profile(meta)

    # ------------------------------------------------------------ machine

    def machine(self) -> str:
        path = os.path.join(self.local, "machine.json")
        try:
            with open(path, "r", encoding="utf-8") as fh:
                ident = json.load(fh).get("id", "")
            if _MACHINE_RE.match(ident):
                return ident
        except (OSError, ValueError):
            pass
        return self.set_machine(None)

    def set_machine(self, name: str | None) -> str:
        if name:
            ident = slug(name, 32)
        else:
            host = slug(socket.gethostname() or "machine", 20)
            ident = slug("%s-%s" % (host, new_id()[-4:]), 32)
        if not _MACHINE_RE.match(ident):
            raise CalError("machine name must be letters, digits and dashes")
        os.makedirs(self.local, exist_ok=True)
        write_text(os.path.join(self.local, "machine.json"), json.dumps({"id": ident}) + "\n")
        return ident

    # ------------------------------------------------------------ events

    def append(self, etype: str, key: str | None = None, when=None, **payload) -> dict:
        """Append one event to this machine's log and return it."""
        when = when or now()
        event = {"id": new_id(), "ts": iso(when), "m": self.machine(), "t": etype, "v": SCHEMA, "q": _next_q()}
        if key:
            event["k"] = key
        for name, value in payload.items():
            if value is not None:
                event[name] = value
        os.makedirs(self.events_dir, exist_ok=True)
        path = os.path.join(self.events_dir, "%s.%s.jsonl" % (when.strftime("%Y-%m"), event["m"]))
        line = json.dumps(event, ensure_ascii=False, separators=(",", ":"))
        needs_newline = False
        try:
            with open(path, "rb") as fh:
                fh.seek(0, os.SEEK_END)
                if fh.tell() > 0:
                    fh.seek(-1, os.SEEK_END)
                    needs_newline = fh.read(1) != b"\n"
        except OSError:
            pass
        with open(path, "a", encoding="utf-8", newline="\n") as fh:
            if needs_newline:
                fh.write("\n")
            fh.write(line + "\n")
            fh.flush()
            try:
                os.fsync(fh.fileno())
            except OSError:
                pass
        self._events = None  # reload on next read, so order always matches the files
        return event

    def event_files(self) -> list:
        if not os.path.isdir(self.events_dir):
            return []
        return sorted(
            os.path.join(self.events_dir, name)
            for name in os.listdir(self.events_dir)
            if name.endswith(".jsonl")
        )

    def events(self) -> list:
        """All events from every machine, in a deterministic order.

        Order: timestamp, then machine, then the order in which that machine
        wrote them ('q'), then id. It does not depend on which file a line is
        in or where, so copying, re-ordering or union-merging the files
        cannot change the result. Duplicates (same id, or same idempotency
        key 'k') are dropped.
        """
        if self._events is not None:
            return self._events
        loaded, errors = [], []
        for path in self.event_files():
            name = os.path.basename(path)
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    lines = fh.read().split("\n")
            except (OSError, UnicodeDecodeError) as exc:
                errors.append("%s: unreadable (%s)" % (name, exc))
                continue
            for n, raw in enumerate(lines, 1):
                raw = raw.strip()
                if not raw:
                    continue
                if raw.startswith(("<<<<<<<", "=======", ">>>>>>>")):
                    errors.append("%s:%d: git conflict marker (resolve by keeping both sides)" % (name, n))
                    continue
                try:
                    event = json.loads(raw)
                    event["_dt"] = parse_ts(event["ts"])
                    event["t"], event["id"]
                except (ValueError, KeyError, TypeError) as exc:
                    errors.append("%s:%d: not a valid event (%s)" % (name, n, exc.__class__.__name__))
                    continue
                event.setdefault("m", "unknown")
                event["_seq"] = (name, n)
                loaded.append(event)
        loaded.sort(key=_order_key)
        seen_ids, seen_keys, unique = set(), set(), []
        for event in loaded:
            if event["id"] in seen_ids:
                continue
            k = event.get("k")
            if k is not None:
                if k in seen_keys:
                    continue
                seen_keys.add(k)
            seen_ids.add(event["id"])
            unique.append(event)
        self._events, self.event_errors = unique, errors
        return unique

    def invalidate(self) -> None:
        self._events = None
        self._profile = None
        self._config = None
        self.memo = {}

    # ------------------------------------------------------------ misc

    def tmp_path(self, name: str) -> str:
        d = os.path.join(self.local, "tmp")
        os.makedirs(d, exist_ok=True)
        return os.path.join(d, name)

    def read_json_cache(self, name: str):
        path = os.path.join(self.cache_dir, name)
        try:
            with open(path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, ValueError):
            return None

    def write_json_cache(self, name: str, data) -> str:
        path = os.path.join(self.cache_dir, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        write_text(path, json.dumps(data, ensure_ascii=False))
        return path
