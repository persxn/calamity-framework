"""Study sources (a course, a playlist, a book) and the learner's progress through them.

A source is one markdown file, learner/sources/<id>.md, listing its items
(lectures, chapters) and which syllabus topics each one covers. Progress is
logged as events. Only metadata lives here: never the course's content.

How a source gets connected (API, export, pasted progress page, or a quick
manual log) is decided per source by following
framework/rules/bridge-rulebook.md.
"""
from __future__ import annotations

import os

from . import fm
from .store import Repo, write_text
from .util import SKILL_ID_RE, CalError, csv_list, iso, now

ITEM_KEYS = ("topics", "minutes", "order", "section", "url")
KINDS = ("course", "playlist", "book", "site", "other")
ROUTES = ("api", "export", "browser-session", "paste", "manual-log")


class SourceItem:
    __slots__ = ("id", "title", "topics", "minutes", "order", "section", "url", "pos")

    def __init__(self, ident, title, meta, pos):
        self.id = ident
        self.title = title
        self.topics = csv_list(meta.get("topics"))
        self.minutes = _int(meta.get("minutes"), 0)
        self.order = _int(meta.get("order"), pos + 1)
        self.section = str(meta.get("section") or "")
        self.url = str(meta.get("url") or "")
        self.pos = pos


class Source:
    def __init__(self, meta, body, path):
        self.meta = meta
        self.body = body
        self.path = path
        self.id = str(meta.get("id") or "")
        self.title = str(meta.get("title") or self.id)
        self.kind = str(meta.get("kind") or "other")
        self.url = str(meta.get("url") or "")
        self.route = str(meta.get("route") or "manual-log")
        self.tracks = csv_list(meta.get("tracks"))
        self.items = []
        self.errors = []

    def item(self, ident):
        for it in self.items:
            if it.id == ident:
                return it
        return None

    def ordered(self):
        return sorted(self.items, key=lambda it: (it.order, it.pos))


def path_for(repo: Repo, ident: str) -> str:
    return os.path.join(repo.sources_dir, ident + ".md")


def load_all(repo: Repo) -> list:
    cached = repo.memo.get("sources")
    if cached is not None:
        return cached
    out = repo.memo["sources"] = []
    if not os.path.isdir(repo.sources_dir):
        return out
    for name in sorted(os.listdir(repo.sources_dir)):
        if not name.endswith(".md") or name.lower() == "readme.md":
            continue
        path = os.path.join(repo.sources_dir, name)
        try:
            meta, body = fm.load(path)
            src = Source(meta, body, path)
            if not src.id:
                src.id = name[:-3]
            seen = set()
            for pos, entry in enumerate(fm.entries(body, "Items", ITEM_KEYS, where=repo.rel(path))):
                if entry["id"] in seen:
                    src.errors.append("duplicate item id %r" % entry["id"])
                    continue
                seen.add(entry["id"])
                src.items.append(SourceItem(entry["id"], entry["title"], entry["meta"], pos))
        except (CalError, OSError, UnicodeDecodeError) as exc:
            src = Source({"id": name[:-3]}, "", path)
            src.errors.append(str(exc))
        out.append(src)
    return out


def get(repo: Repo, ident: str) -> Source:
    for src in load_all(repo):
        if src.id == ident:
            return src
    have = ", ".join(s.id for s in load_all(repo)) or "none yet"
    raise CalError("unknown source %r (sources: %s)" % (ident, have))


def load_maps(repo: Repo, tree) -> dict:
    """{source id: {item id: [topic keys that exist in the tree]}}"""
    maps = {}
    for src in load_all(repo):
        mapping = {}
        for it in src.items:
            mapping[it.id] = [k for k in it.topics if tree.has_topic(k)]
        maps[src.id] = mapping
    return maps


def load_minutes(repo: Repo) -> dict:
    """{source id: {item id: minutes}} for items that state their length."""
    return {src.id: {it.id: it.minutes for it in src.items if it.minutes} for src in load_all(repo)}


def led_skills(repo: Repo, tree) -> set:
    """Skills that the learner studies from an external source (lectures first, then tested)."""
    skills = set()
    for mapping in load_maps(repo, tree).values():
        for keys in mapping.values():
            for key in keys:
                skills.add(key.split("/", 1)[0])
    return skills


def add(repo: Repo, ident: str, title: str, kind: str, url: str, route: str, tracks, note: str) -> str:
    if not SKILL_ID_RE.match(ident) or "." in ident:
        raise CalError("source ids are short lower-case names like 'gate-course' or 'yt-dsa'")
    if kind not in KINDS:
        raise CalError("kind must be one of %s" % ", ".join(KINDS))
    if route not in ROUTES:
        raise CalError("route must be one of %s" % ", ".join(ROUTES))
    path = path_for(repo, ident)
    if os.path.exists(path):
        raise CalError("source %r already exists (%s)" % (ident, repo.rel(path)))
    meta = {
        "id": ident, "title": title or ident, "kind": kind, "url": url or "", "route": route,
        "tracks": csv_list(tracks), "terms_checked": now().date().isoformat(), "terms_note": note or "",
    }
    body = (
        "Only progress metadata belongs in this file: item ids, titles, topic mapping.\n"
        "Never paste course content, notes or question banks here.\n\n"
        "# Items\n"
    )
    os.makedirs(repo.sources_dir, exist_ok=True)
    write_text(path, fm.dump(meta, body))
    repo.memo.pop("sources", None)
    return path


def import_items(repo: Repo, ident: str, rows, dry_run: bool = False) -> tuple:
    """Add or replace items of a source from a list of dicts. Returns (added, replaced).

    `dry_run` checks the list and counts what would change without writing anything."""
    src = get(repo, ident)
    if not isinstance(rows, list):
        raise CalError("expected a JSON list of items")
    existing = {it.id: it for it in src.items}
    order = [it.id for it in src.items]
    added = replaced = 0
    entries = {}
    for it in src.items:
        entries[it.id] = (it.title, {"topics": it.topics, "minutes": it.minutes or None, "order": it.order,
                                     "section": it.section, "url": it.url})
    for n, row in enumerate(rows):
        if not isinstance(row, dict) or not row.get("id"):
            raise CalError("item %d has no 'id'" % (n + 1))
        item_id = str(row["id"]).strip()
        if not all(ch.isalnum() or ch in "-_." for ch in item_id) or len(item_id) > 64:
            raise CalError("bad item id %r (letters, digits, '-', '_', '.')" % item_id)
        meta = {
            "topics": csv_list(row.get("topics")),
            "minutes": _int(row.get("minutes"), 0) or None,
            "order": _int(row.get("order"), len(order) + 1),
            "section": str(row.get("section") or ""),
            "url": str(row.get("url") or ""),
        }
        if item_id in existing:
            replaced += 1
        else:
            added += 1
            order.append(item_id)
        entries[item_id] = (str(row.get("title") or item_id).strip().replace("\n", " "), meta)
    if dry_run:
        return added, replaced
    body_lines = src.body.split("\n")
    lines, start = fm.section(src.body, "Items")
    if lines is None:
        head, tail = src.body, ""
    else:  # keep whatever is written before and after the '# Items' section
        head = "\n".join(body_lines[: start - 1])
        tail = "\n".join(body_lines[start + len(lines):])
    out = [head.rstrip("\n"), "", "# Items", ""]
    for item_id in order:
        title, meta = entries[item_id]
        out.append(fm.render_entry(item_id, title, meta))
    if tail.strip():
        out.append(tail.strip("\n"))
    write_text(src.path, fm.dump(src.meta, "\n".join(out).rstrip("\n") + "\n"))
    repo.memo.pop("sources", None)
    return added, replaced


def check(repo: Repo, tree) -> tuple:
    errors, warnings = [], []
    for src in load_all(repo):
        where = repo.rel(src.path)
        errors.extend("%s: %s" % (where, e) for e in src.errors)
        if src.route not in ROUTES:
            warnings.append("%s: unknown route %r" % (where, src.route))
        unmapped = 0
        for it in src.items:
            if not it.topics:
                unmapped += 1
            for key in it.topics:
                if not tree.has_topic(key):
                    errors.append("%s: item %r maps to unknown topic %r" % (where, it.id, key))
        if unmapped:
            warnings.append("%s: %d item(s) not mapped to any topic yet" % (where, unmapped))
    return errors, warnings


def resolve_item(src: Source, token: str) -> SourceItem:
    """Find an item by id, by its order number, or by a unique piece of its title."""
    token = str(token).strip()
    hit = src.item(token)
    if hit:
        return hit
    if token.isdigit():
        hits = [it for it in src.items if it.order == int(token)]
        if len(hits) == 1:
            return hits[0]
    low = token.lower()
    hits = [it for it in src.items if low in it.id.lower() or low in it.title.lower()]
    if len(hits) == 1:
        return hits[0]
    if not hits:
        raise CalError("no item matching %r in source %r" % (token, src.id))
    raise CalError("%r matches several items: %s" % (token, ", ".join(it.id for it in hits[:8])))


def log(repo: Repo, source: str, token: str, done: bool, score, method: str, at=None) -> SourceItem:
    """Log one item. `at` backdates it to when it was really watched (never later than now)."""
    src = get(repo, source)
    item = resolve_item(src, token)
    repo.append("src_progress", when=at, source=src.id, item=item.id, done=bool(done), score=score,
                method=method or src.route)
    return item


def log_ticks(repo: Repo, state, source: str, ticks, when, method: str | None = None) -> tuple:
    """Log many items with the times they were ticked, e.g. from a tracker: a JSON list of
    {"item": id, "at": ISO time} or an object {id: ISO time | true}. Items already logged are skipped, so a
    sync can be run again. Returns (logged items, skipped count)."""
    from .util import parse_ts

    src = get(repo, source)
    if isinstance(ticks, dict):
        ticks = [{"item": k, "at": v} for k, v in ticks.items()]
    if not isinstance(ticks, list):
        raise CalError('ticks are a JSON list of {"item": "<id>", "at": "<ISO time>"} or an object {"<id>": "<ISO time>"}')
    logged = state.src.get(src.id, {})
    rows = []
    for t in ticks:
        if not isinstance(t, dict) or "item" not in t:
            raise CalError("each tick needs an item id")
        item = resolve_item(src, str(t["item"]))
        at = t.get("at")
        stamp = parse_ts(at) if isinstance(at, str) and at.strip() else when
        if stamp > when:
            raise CalError("%s is ticked in the future (%s)" % (item.id, at))
        rows.append((stamp, item))
    out, skipped, seen = [], 0, set()
    for stamp, item in sorted(rows, key=lambda r: r[0]):
        if logged.get(item.id, {}).get("done") or item.id in seen:
            skipped += 1
            continue
        seen.add(item.id)
        repo.append("src_progress", when=stamp, source=src.id, item=item.id, done=True, method=method or src.route)
        out.append(item)
    return out, skipped


def revise(repo: Repo, state, tree, when, n: int = 8, threshold: float = 0.85) -> list:
    """Watched lectures whose topics are fading: [(source, item, [(topic, recall chance)])], most faded first."""
    rows = []
    for src in load_all(repo):
        done = state.src.get(src.id, {})
        for it in src.ordered():
            if not done.get(it.id, {}).get("done"):
                continue
            fading = []
            for k in it.topics:
                key = state.canon(k)
                ts = state.topics.get(key)
                if ts is not None and ts.card is not None and tree.has_topic(key):
                    r = state.retrievability(key, when)
                    if r < threshold:
                        fading.append((key, r))
            if fading:
                rows.append((src, it, sorted(fading, key=lambda f: f[1])))
    rows.sort(key=lambda r: (-len(r[2]), min(f[1] for f in r[2])))
    return rows[:n]


def log_upto(repo: Repo, state, source: str, token: str, method: str) -> list:
    """Log every not-yet-done item up to and including one item: catching up on what was watched before.

    These are flagged as a catch-up, so they do not count as today's lectures or today's time.
    """
    src = get(repo, source)
    last = resolve_item(src, token)
    logged = state.src.get(src.id, {})
    done = []
    for it in src.ordered():
        if not logged.get(it.id, {}).get("done"):
            repo.append("src_progress", source=src.id, item=it.id, done=True, method=method or src.route, bulk=True)
            done.append(it)
        if it.id == last.id:
            break
    return done


def progress(src: Source, state) -> dict:
    logged = state.src.get(src.id, {})
    done = [it for it in src.items if logged.get(it.id, {}).get("done")]
    minutes_total = sum(it.minutes for it in src.items)
    minutes_done = sum(it.minutes for it in done)
    return {"items": len(src.items), "done": len(done), "minutes_total": minutes_total,
            "minutes_done": minutes_done}


def next_items(repo: Repo, state, tree, limit: int = 3, source: str | None = None) -> list:
    """Not-yet-done items in source order: [(Source, SourceItem)]."""
    out = []
    for src in load_all(repo):
        if source and src.id != source:
            continue
        logged = state.src.get(src.id, {})
        for it in src.ordered():
            if logged.get(it.id, {}).get("done"):
                continue
            out.append((src, it))
            if len(out) >= limit:
                return out
    return out


def lectures_toward(repo: Repo, state, tree, key: str, limit: int = 3) -> list:
    """The next unlogged lectures of the source that will open topic `key`: [(Source, SourceItem)]."""
    for src in load_all(repo):
        logged = state.src.get(src.id, {})
        todo = [it for it in src.ordered() if not logged.get(it.id, {}).get("done")]
        if any(key in it.topics for it in todo):
            return [(src, it) for it in todo[:limit]]
    return []


def waiting_skills(repo: Repo, state, tree) -> set:
    """Skills that still have an unlogged lecture mapped to one of their topics.

    Topics of such a skill that have not been taught wait for their lecture. Once every mapped
    lecture is logged, whatever the source did not cover is taught like any other topic.
    """
    skills = set()
    for src in load_all(repo):
        logged = state.src.get(src.id, {})
        for it in src.items:
            if logged.get(it.id, {}).get("done"):
                continue
            for key in it.topics:
                if tree.has_topic(key):
                    skills.add(key.split("/", 1)[0])
    return skills


def upcoming_topics(repo: Repo, state, tree, per_source: int = 12) -> list:
    """Untested topics that the next unlogged lectures will open, in lecture order."""
    out = []
    for src in load_all(repo):
        logged = state.src.get(src.id, {})
        lectures = 0
        for it in src.ordered():
            if logged.get(it.id, {}).get("done"):
                continue
            fresh = []
            for key in it.topics:
                ts = state.topics.get(key)
                if tree.has_topic(key) and (ts is None or ts.card is None) and key not in out and key not in fresh:
                    fresh.append(key)
            if fresh:
                out.extend(fresh)
                lectures += 1
                if lectures >= per_source:
                    break
    return out


def status_text(repo: Repo, state, tree, ident: str | None = None) -> str:
    srcs = load_all(repo)
    if ident:
        srcs = [get(repo, ident)]
    if not srcs:
        return "No study sources connected yet. Use the bridge skill to connect one."
    lines = []
    for src in srcs:
        p = progress(src, state)
        share = (p["done"] / float(p["items"])) if p["items"] else 0.0
        lines.append("%s | %s [%s, route: %s]" % (src.id, src.title, src.kind, src.route))
        lines.append("  %d/%d items done (%d%%)" % (p["done"], p["items"], round(100 * share)))
        if p["minutes_total"]:
            lines.append("  %d of %d minutes watched" % (p["minutes_done"], p["minutes_total"]))
        unmapped = sum(1 for it in src.items if not [k for k in it.topics if tree.has_topic(k)])
        if unmapped:
            lines.append("  %d item(s) not mapped to a topic" % unmapped)
        nxt = next_items(repo, state, tree, limit=3, source=src.id)
        for _, it in nxt:
            lines.append("  next: %s | %s%s" % (it.id, it.title, (" (%dm)" % it.minutes) if it.minutes else ""))
        for err in src.errors:
            lines.append("  ERROR: " + err)
    lines.append("as of " + iso(now())[:16])
    return "\n".join(lines)


def show_text(repo: Repo, tree, ident: str, section: str | None = None, unmapped: bool = False,
              topic: str | None = None, limit: int = 40) -> str:
    """A slice of one source, so that a mapping task never reads the whole file: with no filter, its
    sections with item counts; with --section (a piece of its name), --unmapped or --topic (a topic key,
    or a skill id for all its topics), the matching items in course order, at most `limit`."""
    src = get(repo, ident)
    items = src.ordered()
    unmapped_all = [it for it in items if not [k for k in it.topics if tree.has_topic(k)]]
    head = "source %s | %s: %d items, %d unmapped" % (src.id, src.title, len(items), len(unmapped_all))
    if section is None and not unmapped and topic is None:
        rows, order = {}, []
        for it in items:
            if it.section not in rows:
                rows[it.section] = [0, 0]
                order.append(it.section)
            rows[it.section][0] += 1
            rows[it.section][1] += 0 if [k for k in it.topics if tree.has_topic(k)] else 1
        lines = [head, "sections (items, unmapped):"]
        lines += ["  %s (%d, %d)" % (name or "(no section)", n, u) for name, (n, u) in
                  ((name, rows[name]) for name in order)]
        lines.append("items: source show %s --section <part of a name> | --unmapped | --topic <key or skill>"
                     % src.id)
        return "\n".join(lines)
    picked = items
    if section is not None:
        picked = [it for it in picked if section.lower() in it.section.lower()]
    if unmapped:
        picked = [it for it in picked if it in unmapped_all]
    if topic is not None:
        whole = "/" not in topic
        if whole:
            tree.get(topic)
        else:
            tree.topic(topic)
        picked = [it for it in picked if any(k == topic or (whole and k.startswith(topic + "/")) for k in it.topics)]
    lines = [head, "%d item(s) match%s" % (len(picked), (", showing %d" % limit) if len(picked) > limit else "")]
    for it in picked[:limit]:
        mapped = [k for k in it.topics if tree.has_topic(k)]
        unknown = [k for k in it.topics if not tree.has_topic(k)]
        lines.append("%s | %s | %s | %s%s" % (it.id, it.title, it.section or "-", ", ".join(mapped) or "unmapped",
                                             (" | unknown: " + ", ".join(unknown)) if unknown else ""))
    if len(picked) > limit:
        lines.append("... %d more: --limit %d" % (len(picked) - limit, len(picked)))
    return "\n".join(lines)


def _int(value, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
