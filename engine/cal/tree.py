"""The skill tree: nodes, prerequisites, slots (alternatives) and per-skill topics.

Shipped nodes live in framework/tree/**.md. A learner's own nodes and
overrides live in learner/tree/<id>.md and win over shipped ones, so
framework updates never overwrite a learner's changes. Topics of a skill
come from learner/syllabus/<id>.md when it exists (the per-learner
syllabus), otherwise from the node file's own '# Topics' section.
"""
from __future__ import annotations

import os
import re

from . import fm
from .store import Repo, read_text, write_text
from .util import SKILL_ID_RE, TOPIC_ID_RE, CalError, csv_list

TOPIC_KEYS = ("needs", "level", "minutes", "weight", "band", "aliases", "marks", "same_as")
SKIP_FILES = ("tracks.md", "readme.md", "index.md")


STRAND = re.compile(r"^\[([TPIN])\]\s*")
STRANDS = {"T": "theory", "P": "practice", "I": "implementation", "N": "numerical"}


class Topic:
    __slots__ = ("id", "skill", "title", "needs", "level", "minutes", "weight", "aliases", "same_as",
                 "band", "body", "order")

    def __init__(self, skill, ident, title, meta, body, order):
        self.id = ident
        self.skill = skill
        self.title = title
        self.needs = csv_list(meta.get("needs"))
        self.level = _int(meta.get("level"), 2)
        self.minutes = _int(meta.get("minutes"), 0)
        self.weight = _num(meta.get("weight"), 1.0)
        self.aliases = csv_list(meta.get("aliases"))
        self.same_as = csv_list(meta.get("same_as"))  # the same knowledge listed under another skill
        self.band = _int(meta.get("band"), 0)
        self.body = body
        self.order = order

    @property
    def key(self) -> str:
        return "%s/%s" % (self.skill, self.id)

    def objectives(self) -> list:
        """The topic's objectives in order: [{n, strand, text}], from its top-level `- ` bullets. A bullet may open
        with a strand tag: [T] theory and mechanism, [P] practice and debugging, [I] implementation and
        internals, [N] a numerical (GATE)."""
        out = []
        for line in self.body.split("\n"):
            if line.startswith(("- ", "* ")):
                text = line[2:].strip()
                m = STRAND.match(text)
                out.append({"n": len(out) + 1, "strand": m.group(1) if m else None,
                            "text": text[m.end():].strip() if m else text})
        return out

    def first_line(self) -> str:
        for line in self.body.split("\n"):
            line = line.strip().lstrip("-* ").strip()
            if line:
                return line
        return ""


class Node:
    def __init__(self, meta: dict, body: str, path: str, origin: str):
        self.meta = meta
        self.body = body
        self.path = path
        self.origin = origin  # 'framework' | 'learner'
        self.id = str(meta.get("id") or "")
        self.title = str(meta.get("title") or self.id)
        self.track = str(meta.get("track") or "custom")
        self.group = str(meta.get("group") or "misc")
        self.kind = str(meta.get("kind") or "skill")
        self.prereqs = csv_list(meta.get("prereqs"))
        self.slot = meta.get("slot") or None
        self.tags = csv_list(meta.get("tags"))
        self.weaves_into = csv_list(meta.get("weaves_into"))
        self.optional = bool(meta.get("optional", False))
        self.est_hours = _num(meta.get("est_hours"), 0)
        self.summary = str(meta.get("summary") or "")
        self.aliases = csv_list(meta.get("aliases"))
        self.order = _int(meta.get("order"), 500)
        self.dropped = bool(meta.get("dropped", False))
        self.paper = meta.get("paper") or None
        self.marks = meta.get("marks")
        self.overlaps = csv_list(meta.get("overlaps"))
        self.cf_tags = csv_list(meta.get("cf_tags"))
        self.band = _int(meta.get("band"), 0)
        self.topics = []
        self.topics_path = None
        self.topics_origin = None

    @property
    def has_boss(self) -> bool:
        return bool(fm.section_text(self.body, "Boss"))

    def topic(self, ident: str):
        for t in self.topics:
            if t.id == ident:
                return t
        return None

    def section(self, name: str) -> str:
        return fm.section_text(self.body, name)


class Tree:
    def __init__(self, repo: Repo):
        self.repo = repo
        self.nodes = {}
        self.errors = []
        self.warnings = []
        self.tracks = []
        self.track_meta = {}
        self._equiv = None
        self._ordered = None
        self._load()

    # ------------------------------------------------------------ loading

    def _load(self) -> None:
        repo = self.repo
        fw_tree = os.path.join(repo.framework, "tree")
        tracks_path = os.path.join(fw_tree, "tracks.md")
        meta = {}
        if os.path.isfile(tracks_path):
            try:
                meta, _ = fm.load(tracks_path)
            except CalError as exc:
                self.errors.append(str(exc))
        self.tracks = csv_list(meta.get("tracks"))
        self.track_meta = meta

        shipped = {}
        for path in _walk_md(fw_tree):
            node = self._read_node(path, "framework")
            if node is None:
                continue
            if node.id in shipped:
                self.errors.append(
                    "duplicate skill id %r: %s and %s" % (node.id, repo.rel(shipped[node.id].path), repo.rel(path))
                )
                continue
            shipped[node.id] = node
        self.nodes = shipped

        for path in _walk_md(repo.tree_dir):
            node = self._read_node(path, "learner")
            if node is None:
                continue
            base = self.nodes.get(node.id)
            if node.dropped and base is not None and base.origin == "framework" and len(node.meta) <= 3:
                base.dropped = True  # a stub that only says "this shipped skill is dropped"
                base.meta = dict(base.meta, dropped=True)
                continue
            self.nodes[node.id] = node

        for node in self.nodes.values():
            self._load_topics(node)
            if node.track not in self.tracks:
                self.tracks.append(node.track)

    def _read_node(self, path: str, origin: str):
        try:
            meta, body = fm.load(path)
        except (CalError, OSError, UnicodeDecodeError) as exc:
            self.errors.append("%s: %s" % (self.repo.rel(path), exc))
            return None
        if not meta.get("id"):
            self.errors.append("%s: missing 'id' in front matter" % self.repo.rel(path))
            return None
        node = Node(meta, body, path, origin)
        if not SKILL_ID_RE.match(node.id):
            self.errors.append("%s: bad skill id %r (use lower-case letters, digits, '-', '.')" % (self.repo.rel(path), node.id))
            return None
        stem = os.path.splitext(os.path.basename(path))[0]
        if stem != node.id:
            self.warnings.append("%s: file name does not match id %r" % (self.repo.rel(path), node.id))
        return node

    def _load_topics(self, node: Node) -> None:
        syllabus = os.path.join(self.repo.syllabus_dir, node.id + ".md")
        if os.path.isfile(syllabus):
            path, origin = syllabus, "learner"
            try:
                _, body = fm.load(path)
            except (CalError, OSError, UnicodeDecodeError) as exc:
                self.errors.append("%s: %s" % (self.repo.rel(path), exc))
                return
        else:
            path, origin, body = node.path, node.origin, node.body
        try:
            entries = fm.entries(body, "Topics", TOPIC_KEYS, where=self.repo.rel(path))
        except CalError as exc:
            self.errors.append(str(exc))
            return
        seen = set()
        for i, entry in enumerate(entries):
            ident = entry["id"]
            if not TOPIC_ID_RE.match(ident):
                self.errors.append("%s: bad topic id %r" % (self.repo.rel(path), ident))
                continue
            if ident in seen:
                self.errors.append("%s: duplicate topic id %r" % (self.repo.rel(path), ident))
                continue
            seen.add(ident)
            node.topics.append(Topic(node.id, ident, entry["title"], entry["meta"], entry["body"], i))
        node.topics_path = path if entries else None
        node.topics_origin = origin if entries else None

    # ------------------------------------------------------------ lookups

    def get(self, ident: str) -> Node:
        node = self.nodes.get(ident)
        if node is None:
            close = self.find(ident, limit=3)
            hint = (" Did you mean: %s?" % ", ".join(n.id for n in close)) if close else ""
            raise CalError("unknown skill %r.%s" % (ident, hint))
        return node

    def topic(self, key: str) -> Topic:
        if "/" not in key:
            raise CalError("topic keys look like <skill>/<topic>; got %r" % key)
        skill, tid = key.split("/", 1)
        node = self.get(skill)
        topic = node.topic(tid)
        if topic is None:
            have = ", ".join(t.id for t in node.topics[:12]) or "(no topics yet)"
            raise CalError("unknown topic %r in skill %r. Topics: %s" % (tid, skill, have))
        return topic

    def has_topic(self, key: str) -> bool:
        if "/" not in key:
            return False
        skill, tid = key.split("/", 1)
        node = self.nodes.get(skill)
        return bool(node and node.topic(tid))

    def equivalents(self, key: str) -> list:
        """Topics declared (from either side) to be the same knowledge as `key`."""
        if self._equiv is None:
            pairs = {}
            for node in self.nodes.values():
                for topic in node.topics:
                    for other in topic.same_as:
                        if other != topic.key and self.has_topic(other):
                            pairs.setdefault(topic.key, set()).add(other)
                            pairs.setdefault(other, set()).add(topic.key)
            self._equiv = pairs
        return sorted(self._equiv.get(key, ()))

    def live(self) -> list:
        """Nodes that are not dropped, in display order."""
        return [n for n in self.ordered() if not n.dropped]

    def ordered(self) -> list:
        """Every node in display order: track, group, then the order given in the skill files."""
        if self._ordered is None:   # a Tree is never changed after loading; edits build a new one
            track_pos = {t: i for i, t in enumerate(self.tracks)}

            def group_pos(node):
                groups = csv_list(self.track_meta.get(node.track + ".groups"))
                return groups.index(node.group) if node.group in groups else len(groups)

            self._ordered = sorted(
                self.nodes.values(),
                key=lambda n: (track_pos.get(n.track, 999), group_pos(n), n.order, n.id),
            )
        return list(self._ordered)

    def groups(self, track: str) -> list:
        groups = csv_list(self.track_meta.get(track + ".groups"))
        for node in self.ordered():
            if node.track == track and node.group not in groups:
                groups.append(node.group)
        return groups

    def track_title(self, track: str) -> str:
        return str(self.track_meta.get(track + ".title") or track)

    def slot_members(self, slot: str) -> list:
        return [n for n in self.ordered() if n.slot == slot]

    def requirement_groups(self, node: Node) -> list:
        """Each prerequisite as (label, [alternative skill ids])."""
        out = []
        for pre in node.prereqs:
            if pre.startswith("slot:"):
                members = [n.id for n in self.slot_members(pre[5:])]
                out.append((pre, members))
            else:
                out.append((pre, [pre] if pre in self.nodes else []))
        return out

    def dependents(self, ident: str) -> list:
        target = self.nodes.get(ident)
        out = []
        for node in self.ordered():
            if node.id == ident or node.dropped:
                continue
            for pre in node.prereqs:
                if pre == ident or (target is not None and target.slot and pre == "slot:" + target.slot):
                    out.append(node)
                    break
        return out

    def find(self, query: str, limit: int = 8) -> list:
        """Alias-aware lookup of skills by id, title, alias or summary words."""
        q = query.strip().lower()
        if not q:
            return []
        words = [w for w in q.replace("/", " ").replace("-", " ").split() if w]
        scored = []
        for node in self.nodes.values():
            hay_id = node.id.lower()
            names = [hay_id, node.title.lower()] + [a.lower() for a in node.aliases]
            score = 0
            if q in names:
                score = 100
            elif any(q in n for n in names):
                score = 60
            else:
                text = " ".join(names + [node.summary.lower(), node.group.lower()])
                hits = sum(1 for w in words if w in text)
                if hits:
                    score = 10 * hits + (5 if hits == len(words) else 0)
            if score:
                scored.append((-score, node.id, node))
        scored.sort()
        return [n for _, _, n in scored[:limit]]

    # ------------------------------------------------------------ validation

    def check(self):
        """Return (errors, warnings) for the whole tree."""
        errors, warnings = list(self.errors), list(self.warnings)
        for node in self.nodes.values():
            where = self.repo.rel(node.path)
            for pre in node.prereqs:
                if pre.startswith("slot:"):
                    if not self.slot_members(pre[5:]):
                        errors.append("%s: prerequisite %r has no skills in that slot" % (where, pre))
                    continue
                other = self.nodes.get(pre)
                if other is None:
                    errors.append("%s: unknown prerequisite %r" % (where, pre))
                elif other.dropped and not node.dropped:
                    warnings.append("%s: prerequisite %r is dropped (treated as satisfied)" % (where, pre))
                if pre == node.id:
                    errors.append("%s: a skill cannot require itself" % where)
            if node.kind not in ("skill", "milestone"):
                warnings.append("%s: unknown kind %r" % (where, node.kind))
            twhere = self.repo.rel(node.topics_path) if node.topics_path else where
            ids = {t.id for t in node.topics}
            for topic in node.topics:
                for need in topic.needs:
                    if "/" in need:  # a topic of another skill, by its full key
                        if not self.has_topic(need):
                            errors.append("%s: topic %r needs unknown topic %r" % (twhere, topic.id, need))
                    elif need not in ids:
                        errors.append("%s: topic %r needs unknown topic %r" % (twhere, topic.id, need))
                for other in topic.same_as:
                    if "/" not in other:
                        errors.append("%s: topic %r same_as %r must be a full <skill>/<topic> key" % (twhere, topic.id, other))
                    elif not self.has_topic(other):
                        warnings.append("%s: topic %r same_as %r does not exist (ignored)" % (twhere, topic.id, other))
            cyc = _find_cycle({t.id: [n for n in t.needs if n in ids] for t in node.topics})
            if cyc:
                errors.append("%s: topics form a cycle: %s" % (twhere, " -> ".join(cyc)))
        graph = {}
        for node in self.nodes.values():
            edges = []
            for _, alts in self.requirement_groups(node):
                edges.extend(a for a in alts if a != node.id)
            graph[node.id] = edges
        cyc = _find_cycle(graph)
        if cyc:
            errors.append("prerequisites form a cycle: %s" % " -> ".join(cyc))
        return errors, warnings

    # ------------------------------------------------------------ graph walks

    def ancestors(self, ident: str, choose=None) -> list:
        """All skills needed before `ident` (not including it), deepest first.

        `choose(alternatives)` picks which member of a slot to follow.
        """
        choose = choose or (lambda alts: alts[0])
        seen, order = set(), []

        def visit(nid, stack):
            node = self.nodes.get(nid)
            if node is None or nid in stack:
                return
            for _, alts in self.requirement_groups(node):
                alts = [a for a in alts if a in self.nodes and not self.nodes[a].dropped]
                if not alts:
                    continue
                pick = choose(alts)
                if pick not in seen:
                    visit(pick, stack | {nid})
                    if pick not in seen:
                        seen.add(pick)
                        order.append(pick)

        visit(ident, frozenset())
        return order

    def layers(self, ident: str, choose=None, skip=None) -> list:
        """Group `ident` and its prerequisites into layers that can run in parallel.

        `skip(skill_id)` returning True removes skills already satisfied.
        """
        choose = choose or (lambda alts: alts[0])
        skip = skip or (lambda nid: False)
        wanted = [a for a in self.ancestors(ident, choose) if not skip(a)] + [ident]
        wanted_set = set(wanted)
        depth = {}

        def depth_of(nid, stack=frozenset()):
            if nid in depth:
                return depth[nid]
            node = self.nodes[nid]
            best = 0
            for _, alts in self.requirement_groups(node):
                alts = [a for a in alts if a in wanted_set and a not in stack]
                if alts:
                    pick = choose(alts) if choose(alts) in alts else alts[0]
                    best = max(best, 1 + depth_of(pick, stack | {nid}))
            depth[nid] = best
            return best

        for nid in wanted:
            depth_of(nid)
        out = []
        for level in range(max(depth.values()) + 1 if depth else 0):
            out.append([nid for nid in wanted if depth[nid] == level])
        return out


# ---------------------------------------------------------------- editing


def node_path(repo: Repo, ident: str) -> str:
    return os.path.join(repo.tree_dir, ident + ".md")


def _checked_write(repo: Repo, path: str, text: str | None) -> Tree:
    """Write (or delete when text is None) a learner tree file; roll back if the tree breaks."""
    before = read_text(path) if os.path.isfile(path) else None
    old_errors, _ = Tree(repo).check()
    if text is None:
        if before is not None:
            os.remove(path)
    else:
        write_text(path, text)
    tree = Tree(repo)
    errors, _ = tree.check()
    new_errors = [e for e in errors if e not in old_errors]
    if new_errors:
        if before is None:
            if os.path.isfile(path):
                os.remove(path)
        else:
            write_text(path, before)
        raise CalError("change rejected, the tree would break:\n  " + "\n  ".join(new_errors))
    return tree


def add_node(repo: Repo, meta: dict, body: str = "") -> Tree:
    ident = str(meta.get("id") or "")
    if not SKILL_ID_RE.match(ident):
        raise CalError("bad skill id %r (use lower-case letters, digits, '-', '.')" % ident)
    tree = Tree(repo)
    if ident in tree.nodes and not tree.nodes[ident].dropped:
        raise CalError("skill %r already exists; use 'tree set' to change it" % ident)
    os.makedirs(repo.tree_dir, exist_ok=True)
    return _checked_write(repo, node_path(repo, ident), fm.dump(meta, body))


def set_node(repo: Repo, ident: str, changes: dict, body: str | None = None) -> Tree:
    tree = Tree(repo)
    node = tree.get(ident)
    meta = {k: v for k, v in node.meta.items() if k != "dropped"}
    for key, value in changes.items():
        if value is None:
            meta.pop(key, None)
        else:
            meta[key] = value
    if node.origin == "framework":
        meta["overrides"] = "framework"
    new_body = node.body if body is None else body
    os.makedirs(repo.tree_dir, exist_ok=True)
    return _checked_write(repo, node_path(repo, ident), fm.dump(meta, new_body))


def drop_node(repo: Repo, ident: str) -> Tree:
    tree = Tree(repo)
    node = tree.get(ident)
    os.makedirs(repo.tree_dir, exist_ok=True)
    if node.origin == "framework":
        text = fm.dump({"id": ident, "dropped": True, "overrides": "framework"}, "")
    else:
        text = fm.dump(dict(node.meta, dropped=True), node.body)
    return _checked_write(repo, node_path(repo, ident), text)


def restore_node(repo: Repo, ident: str) -> Tree:
    path = node_path(repo, ident)
    tree = Tree(repo)
    node = tree.nodes.get(ident)
    if node is None or not node.dropped:
        raise CalError("skill %r is not dropped" % ident)
    if node.origin == "framework":
        return _checked_write(repo, path, None)
    meta = {k: v for k, v in node.meta.items() if k != "dropped"}
    return _checked_write(repo, path, fm.dump(meta, node.body))


# ---------------------------------------------------------------- helpers


def _walk_md(top: str):
    if not os.path.isdir(top):
        return
    for base, dirs, files in os.walk(top):
        dirs.sort()
        for name in sorted(files):
            if name.endswith(".md") and name.lower() not in SKIP_FILES and not name.startswith("_"):
                yield os.path.join(base, name)


def _find_cycle(graph: dict):
    """Return one cycle as a list of ids, or None."""
    state = {}

    def visit(nid, trail):
        state[nid] = 1
        trail.append(nid)
        for nxt in graph.get(nid, ()):
            if nxt not in graph:
                continue
            if state.get(nxt) == 1:
                return trail[trail.index(nxt):] + [nxt]
            if state.get(nxt) is None:
                found = visit(nxt, trail)
                if found:
                    return found
        trail.pop()
        state[nid] = 2
        return None

    for nid in sorted(graph):
        if state.get(nid) is None:
            found = visit(nid, [])
            if found:
                return found
    return None


def _int(value, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _num(value, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
