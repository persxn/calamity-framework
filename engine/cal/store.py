"""Repository layout, configuration, learner profile and the append-only event log.

The event log is the single source of truth for progress. Every machine
appends to its own file (learner/events/<YYYY-MM>.<machine>.jsonl), so two
machines never edit the same file and git merges cleanly. All derived
numbers (schedules, mastery, dashboards) are recomputed by replaying it.
"""
from __future__ import annotations

import contextlib
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
LOCK_WAIT = 15.0  # seconds a command waits for another engine process to finish writing


def _next_q() -> int:
    """A number that grows with every event written on this machine: wall-clock microseconds,
    nudged forward when two events fall in the same microsecond."""
    global _last_q
    _last_q = max(_last_q + 1, time.time_ns() // 1000)
    return _last_q


def order_key(event: dict):
    q = event.get("q")
    return (utc(event["_dt"]), str(event["m"]), q if isinstance(q, int) else 0, str(event["id"]))


def _engine_dir() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def write_text(path: str, text: str, durable: bool = True) -> None:
    """Write a file atomically with LF newlines and UTF-8.

    The text goes to a temporary file in the same folder, which then replaces the target, so a
    reader never sees half a file. `durable` also flushes it to disk first, so a power cut cannot
    leave an empty file behind (caches skip that). On Windows a file that another program holds
    open cannot be replaced for a moment (an antivirus scan, a sync client, another engine
    command reading it), so the replace is retried for a while before giving up.
    """
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".tmp-", dir=os.path.dirname(path) or ".")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
            if durable:
                fh.flush()
                try:
                    os.fsync(fh.fileno())
                except OSError:
                    pass
        for attempt in range(12):
            try:
                os.replace(tmp, path)
                break
            except PermissionError:
                if attempt == 11:
                    raise
                time.sleep(0.05 * (attempt + 1))
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


@contextlib.contextmanager
def file_lock(path: str, wait: float = LOCK_WAIT):
    """Hold an exclusive lock on `path` (a small lock file) while the block runs.

    Engine commands can run at the same time: a background examiner storing items while the
    tutor records an answer. Appends to the event log and read-modify-write updates of the
    profile go through this lock so that neither can damage or lose the other's write. On
    Linux and macOS appends are atomic anyway; on Windows they are not.
    """
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fh = open(path, "a+b")
    locked = False
    try:
        deadline = time.monotonic() + wait
        if os.name == "nt":
            import msvcrt

            while not locked:
                try:
                    fh.seek(0)
                    msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
                    locked = True
                except OSError:
                    if time.monotonic() > deadline:
                        raise CalError("another Calamity command is still writing (lock: %s). Try again; if "
                                       "nothing else is running, delete that file." % path)
                    time.sleep(0.02)
        else:
            import fcntl

            while not locked:
                try:
                    fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    locked = True
                except OSError:
                    if time.monotonic() > deadline:
                        raise CalError("another Calamity command is still writing (lock: %s). Try again; if "
                                       "nothing else is running, delete that file." % path)
                    time.sleep(0.02)
        yield
    finally:
        if locked and os.name == "nt":
            import msvcrt

            try:
                fh.seek(0)
                msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
            except OSError:
                pass
        fh.close()  # closing the file also releases a flock


BAD_UTF8 = "\x00not utf-8"  # stands in for a line that is not UTF-8 (see log_text)


def log_text(raw: bytes) -> str:
    """The text of a log file as Python's text mode reads it (UTF-8, universal newlines).

    A line that is not valid UTF-8 (a write cut off in the middle of a character) is replaced by
    BAD_UTF8, which parse_event_text reports for that line alone: the rest of the file still counts.
    """
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        lines = []
        for line in raw.split(b"\n"):
            try:
                lines.append(line.decode("utf-8"))
            except UnicodeDecodeError:
                lines.append(BAD_UTF8)
        text = "\n".join(lines)
    return text.replace("\r\n", "\n").replace("\r", "\n")


def parse_event_text(name: str, text: str, first_line: int = 1):
    """Events in the text of one log file, or of its tail starting at line `first_line`.
    Returns (events, problems), each problem as (file, line, what is wrong)."""
    events, problems = [], []
    for n, raw in enumerate(text.split("\n"), first_line):
        raw = raw.strip()
        if not raw:
            continue
        if raw == BAD_UTF8:
            problems.append((name, n, "not valid UTF-8 (a write was cut off?); this line is skipped"))
            continue
        if raw.startswith(("<<<<<<<", "=======", ">>>>>>>")):
            problems.append((name, n, "git conflict marker (resolve by keeping both sides)"))
            continue
        try:
            event = json.loads(raw)
        except ValueError:
            problems.append((name, n, "not a valid event (not JSON)"))
            continue
        problem = check_event(event)
        if problem is None:
            try:
                event["_dt"] = parse_ts(event["ts"], naive_ok=False)
            except (ValueError, TypeError) as exc:
                problem = "'ts' is not a timestamp with a UTC offset" if "offset" in str(exc) else "'ts' is not a timestamp"
        if problem is not None:
            problems.append((name, n, "not a valid event (%s)" % problem))
            continue
        event.setdefault("m", "unknown")
        event["_seq"] = (name, n)
        events.append(event)
    return events, problems


def order_and_dedup(events, seen_ids: set, seen_keys: set):
    """Sort events into replay order and drop duplicates (an id, or an idempotency key 'k', seen
    before, in this list or in the sets given). Returns (events, seen_ids, seen_keys)."""
    events = sorted(events, key=order_key)
    unique = []
    for event in events:
        if event["id"] in seen_ids:
            continue
        k = event.get("k")
        if k is not None:
            if k in seen_keys:
                continue
            seen_keys.add(k)
        seen_ids.add(event["id"])
        unique.append(event)
    return unique, seen_ids, seen_keys


def format_problems(problems) -> list:
    """Problems with log lines as the messages doctor and the brief show, in file and line order."""
    return [("%s: %s" % (name, what)) if not n else ("%s:%d: %s" % (name, n, what))
            for name, n, what in sorted(problems, key=lambda p: (p[0], p[1]))]


def check_event(event) -> str | None:
    """Why a parsed log line is not a usable event, or None if it is."""
    if not isinstance(event, dict):
        return "not a JSON object"
    for field in ("id", "t", "ts"):
        if not isinstance(event.get(field), str) or not event[field]:
            return "'%s' is missing or not a string" % field
    for field in ("k", "m"):
        if field in event and not isinstance(event[field], str):
            return "'%s' is not a string" % field
    if "q" in event and (not isinstance(event["q"], int) or isinstance(event["q"], bool)):
        return "'q' is not an integer"
    for field in ID_FIELDS:
        if field in event and not isinstance(event[field], str):
            return "'%s' is not a string" % field
    return None


ID_FIELDS = ("item", "topic", "skill", "attempt", "test", "problem")  # always text when the engine writes them


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
        self.config_errors = []
        self.file_problems = []  # learner files that could not be read as they are (doctor, brief)
        self.profile_problem = None
        self._raw = {}  # bytes of the files read during this command, so the snapshot key matches them
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

    def read_bytes(self, path: str):
        """A file's bytes, read once per command (None if it does not exist). The snapshot key is
        hashed from these same bytes, so a file changed by another command halfway through this one
        cannot give the snapshot a key that does not match what was replayed."""
        if path not in self._raw:
            try:
                with open(path, "rb") as fh:
                    self._raw[path] = fh.read()
            except OSError:
                self._raw[path] = None
        return self._raw[path]

    def note_file_problem(self, text: str) -> None:
        if text not in self.file_problems:
            self.file_problems.append(text)

    def config_defaults(self) -> dict:
        """framework/config.md as shipped, before the learner's overrides."""
        path = os.path.join(self.framework, "config.md")
        raw = self.read_bytes(path)
        if raw is None:
            return {}
        meta, _ = fm.load(path, raw)
        return meta

    def config(self) -> dict:
        """Defaults with the learner's `cfg.<key>` overrides applied. An override the engine cannot
        use (wrong type, out of range, no such setting) is skipped and listed in config_errors."""
        if self._config is None:
            from .profile import coerce_cfg

            defaults = self.config_defaults()
            meta = dict(defaults)
            errors = []
            for key, value in self.profile().items():
                if key.startswith("cfg."):
                    try:
                        meta[key[4:]] = coerce_cfg(key[4:], value, defaults)
                    except CalError as exc:
                        errors.append("%s (the default is used)" % exc)
            self._config, self.config_errors = meta, errors
        return self._config

    def cfg(self, key: str, default=None):
        value = self.config().get(key, default)
        return default if value is None else value

    # ------------------------------------------------------------ profile

    def profile(self) -> dict:
        if self._profile is None:
            self._raw.pop(self.profile_path, None)
            raw = self.read_bytes(self.profile_path)
            self.profile_problem = None
            if raw is None:
                self._profile, self._profile_body = {}, ""
            else:
                try:
                    fm.decode(raw, self.rel(self.profile_path))
                except CalError as exc:
                    # Read it as well as it can be read, say so, and never write over it (save_profile).
                    self.profile_problem = str(exc)
                    self.note_file_problem(self.profile_problem)
                self._profile, self._profile_body = fm.load(self.profile_path, raw, lenient=True)
        return self._profile

    def prof_text(self, key: str, default: str = "") -> str:
        """A profile value meant as text (a name), whatever the file holds: never a list or a flag."""
        value = self.prof(key)
        if isinstance(value, bool) or value is None or isinstance(value, (list, dict)):
            return default
        return str(value)

    def prof(self, key: str, default=None):
        value = self.profile().get(key, default)
        return default if value is None else value

    def onboarded(self) -> bool:
        return bool(self.prof("onboarded", False))

    def save_profile(self, meta: dict) -> None:
        self.profile()
        if self.profile_problem:
            raise CalError("%s. Nothing was changed: the engine does not write over a file it cannot read "
                           "exactly." % self.profile_problem)
        body = self._profile_body or (
            "# Notes about this learner\n\n"
            "Free-form notes on what helps this learner. The tutor reads this file;\n"
            "keys above the line are set with `profile set`.\n"
        )
        ordered = dict(sorted(meta.items()))
        os.makedirs(self.learner, exist_ok=True)
        text = fm.dump(ordered, body).rstrip("\n") + "\n"
        write_text(self.profile_path, text)
        self._raw[self.profile_path] = text.encode("utf-8")
        self._profile, self._profile_body, self._config = ordered, body, None
        self.memo = {}

    def set_profile(self, key: str, value) -> None:
        self.set_profile_many({key: value})

    def set_profile_many(self, changes: dict) -> None:
        """Set (or, with None, remove) several profile keys in one write."""
        for key in changes:
            if not re.match(r"^[A-Za-z0-9_][A-Za-z0-9_.\-]*$", key):
                raise CalError("bad profile key %r" % key)
        with self.lock():
            self._profile = None  # read it again under the lock: another command may just have changed it
            meta = dict(self.profile())
            for key, value in changes.items():
                if value is None:
                    meta.pop(key, None)
                else:
                    meta[key] = value
            self.save_profile(meta)

    def lock(self):
        """The lock every write to the log or the profile holds (see store.file_lock)."""
        return file_lock(os.path.join(self.local, "write.lock"))

    # ------------------------------------------------------------ machine

    def machine(self) -> str:
        ident = self._read_machine()
        if ident:
            return ident
        with self.lock():  # two first commands at once must not give this machine two names
            return self._read_machine() or self.set_machine(None)

    def _read_machine(self) -> str:
        try:
            with open(os.path.join(self.local, "machine.json"), "r", encoding="utf-8") as fh:
                ident = json.load(fh).get("id", "")
            if isinstance(ident, str) and _MACHINE_RE.match(ident):
                return ident
        except (OSError, ValueError, AttributeError):
            pass
        return ""

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
        data = (json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
        with self.lock():
            try:
                with open(path, "rb") as fh:
                    fh.seek(0, os.SEEK_END)
                    if fh.tell() > 0:
                        fh.seek(-1, os.SEEK_END)
                        if fh.read(1) != b"\n":
                            data = b"\n" + data  # an earlier line lost its newline: never glue two events
            except OSError:
                pass
            with open(path, "ab") as fh:
                fh.write(data)
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

    def read_event_file(self, name: str) -> bytes:
        with open(os.path.join(self.events_dir, name), "rb") as fh:
            return fh.read()

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
        loaded, problems = [], []
        for path in self.event_files():
            name = os.path.basename(path)
            try:
                text = log_text(self.read_event_file(name))
            except (OSError, UnicodeDecodeError) as exc:
                problems.append((name, 0, "unreadable (%s)" % exc))
                continue
            found, bad = parse_event_text(name, text)
            loaded += found
            problems += bad
        unique, _, _ = order_and_dedup(loaded, set(), set())
        self._events, self.event_errors = unique, format_problems(problems)
        return unique

    def invalidate(self) -> None:
        self._events = None
        self._profile = None
        self._config = None
        self._raw = {}
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
        write_text(path, json.dumps(data, ensure_ascii=False), durable=False)
        return path
