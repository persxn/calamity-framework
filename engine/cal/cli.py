"""Command line of the Calamity engine.

    python3 engine/calamity.py <command> [options]

Every change to a learner's progress goes through these commands. Run
`python3 engine/calamity.py --help` for the list, `<command> --help` for one.
Exit codes: 0 ok, 1 doctor found problems, 2 error, 3 nothing due (remind),
4 no verified item available (ask / test build).
"""
from __future__ import annotations

import argparse
import codecs
import hashlib
import json
import os
import re
import subprocess
import sys

from . import fm, items, plan, scratch, session, sources, tree as tree_mod
from . import profile as profile_rules
from .state import State, restorable as state_restorable
from .store import Repo, read_text
from .tree import Tree
from .util import CalError, csv_list, now, term_width, to_ascii, utf8_stdio

VERSION_FILE = "VERSION"


class Ctx:
    """Lazily built repo, tree and state shared by one command."""

    def __init__(self):
        self.repo = Repo()
        self.when = now()
        self._tree = None
        self._state = None

    @property
    def tree(self) -> Tree:
        if self._tree is None:
            self._tree = Tree(self.repo)
        return self._tree

    @property
    def state(self) -> State:
        if self._state is None:
            self._state = State(self.repo, self.tree)
        return self._state

    def refresh(self) -> None:
        self.repo.invalidate()
        self._tree = None
        self._state = None


def decode_text(raw: bytes) -> str:
    """Bytes from a file or a pipe as text: UTF-8, or UTF-16 when a byte-order mark says so
    (Windows PowerShell 5 writes UTF-16 when output is redirected to a file)."""
    if raw.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        return raw.decode("utf-16")
    return raw.decode("utf-8-sig")


def _stdin_bytes() -> bytes:
    """Standard input as raw bytes, whatever code page the console or pipe would decode it with."""
    if hasattr(sys.stdin, "buffer"):
        return sys.stdin.buffer.read()
    return sys.stdin.read().encode("utf-8")


def _read_json(args):
    try:
        if getattr(args, "stdin", False):
            raw = decode_text(_stdin_bytes())
        elif getattr(args, "file", None):
            try:
                with open(args.file, "rb") as fh:
                    raw = decode_text(fh.read())
            except OSError as exc:
                raise CalError("could not read %s (%s)" % (args.file, exc.strerror or exc))
        else:
            raise CalError("give the JSON with --file PATH or --stdin")
    except UnicodeDecodeError:
        raise CalError("the JSON is not UTF-8 text; save it as UTF-8 and try again")
    try:
        return json.loads(raw)
    except ValueError as exc:
        raise CalError("not valid JSON: %s" % exc)


def _discard_draft_file(repo, args, batch: bool = False) -> None:
    """A draft holds an answer key in plain text: once stored, remove it if it sits in the scratch folder,
    with the examiner's whole batch folder (the computations behind the keys) after an import."""
    scratch.discard_import(repo, getattr(args, "file", None), batch=batch)


# ---------------------------------------------------------------- session-level commands


def cmd_brief(c, a):
    from . import machine

    if a.hook:
        try:
            src, data = "manual", None
            if not sys.stdin.isatty():
                src = "startup"
                try:  # what Claude Code says about the session; anything unexpected is not a reason to fail
                    data = json.loads(decode_text(_stdin_bytes()) or "{}")
                    if isinstance(data, dict) and isinstance(data.get("source"), str) and data["source"]:
                        src = data["source"][:20]
                except (ValueError, OSError, AttributeError):
                    pass
            if c.repo.onboarded():
                c.repo.append("session", when=c.when, src=src)
            # The hook input may name the model and effort (optional fields): the advice line uses them.
            return 0, plan.brief(c.repo, c.tree, c.state, c.when, machine.engine_cmd(c.repo),
                                 current=data if isinstance(data, dict) else None)
        except Exception as exc:  # a hook must never break the session
            return 0, ("=== CALAMITY BRIEF ===\nThe brief could not be built (%s: %s).\n"
                       "Run the doctor command to see what is wrong.\n=== END BRIEF ===" % (exc.__class__.__name__, exc))
    return 0, plan.brief(c.repo, c.tree, c.state, c.when, machine.engine_cmd(c.repo))


def cmd_today(c, a):
    if not c.repo.onboarded():
        return 0, "Not onboarded yet. Run the onboard skill."
    t = plan.today(c.repo, c.tree, c.state, c.when)
    lines = [plan.today_line(t), plan.quota_line(t["quota_info"])]
    n = t["n"]
    lines.append("answered today: %d (%d correct) · active about %d min" % (n["attempts"], n["ok"], round(n["active_min"])))
    if t["relearn"]:
        lines.append("answer again today: %s" % ", ".join(t["relearn"]))
    due = c.state.due(c.when)
    if due:
        lines.append("due now (%d): %s%s" % (len(due), ", ".join(k for k, _ in due[:8]), " ..." if len(due) > 8 else ""))
    if t["candidates"]:
        lines.append("new, in order: %s" % ", ".join(x["key"] for x in t["candidates"][: max(1, t["new_left"])]))
    for src, it in t["pending_lectures"]:
        lines.append("next lecture: %s %s | %s" % (src.id, it.id, it.title))
    if t["boss_ready"]:
        lines.append("boss due: %s" % ", ".join(t["boss_ready"]))
    action = plan.next_action(c.repo, c.tree, c.state, c.when)
    s = t["sleep"]
    if s["set"]:
        if s["inside"]:
            lines.append("inside the sleep window (%s-%s)" % (s["start"], s["end"]))
        elif s["in_guard"]:
            lines.append("new material is paused until tomorrow: sleep window starts at %s" % s["start"])
    lines.append("next: " + plan.action_label(action))
    from . import advise

    hint = advise.line(c.repo, action["action"])
    if hint:
        lines.append(hint)
    if t["finished"] or n["active_min"] >= 120:
        # every call re-reads the whole conversation, so a long one costs more per question
        lines.append("session: %s; a fresh session for the next block costs less per question than a long one"
                     % ("the finish line is reached" if t["finished"] else "a long block is behind you"))
    return 0, "\n".join(lines)


def cmd_next(c, a):
    if a.skill:
        c.tree.get(a.skill)
    action = plan.next_action(c.repo, c.tree, c.state, c.when, skill=a.skill, only=a.only)
    return 0, plan.next_text(c.repo, c.tree, c.state, c.when, action)


def cmd_ask(c, a):
    return session.ask(c.repo, c.tree, c.state, c.when, topic=a.topic, item_id=a.id, skill=a.skill, test=a.test,
                       show_check=a.check, due_only=a.due, taught=a.taught)


def cmd_answer(c, a):
    text = session.answer(c.repo, c.tree, c.state, c.when, a.item, raw=a.answer, result=a.result, hints=a.hints,
                          err=a.err, note=a.note, seconds=a.seconds, blame=a.blame, evidence=a.evidence, kind=a.kind)
    if not a.next:
        return 0, text
    # One call instead of two, feedback first: the next question follows only a right answer. After a
    # wrong one the key, the cause and the repair come before anything new.
    if not text.startswith("CORRECT"):
        return 0, text + "\n--next: nothing served. %s" % (
            "Repair the mistake first, then: ask%s" % (" --skill %s" % a.skill if a.skill else "")
            if text.startswith("WRONG") else "Tests are answered in order with: ask --id <item> --test <test>")
    c.refresh()
    code, more = session.ask(c.repo, c.tree, c.state, c.when, skill=a.skill, due_only=a.due)
    return code, text + "\n\n=== NEXT (tell the learner the result above in one line, then show this) ===\n" + more


def cmd_mistake(c, a):
    items.load(c.repo, a.item)
    st = c.state.items.get(a.item)
    if st is None or not st.last_attempt:
        raise CalError("no recorded answer to %s" % a.item)
    if st.last_ok:
        raise CalError("the last answer to %s was correct: there is no mistake to classify" % a.item)
    c.repo.append("errtag", attempt=st.last_attempt, item=a.item, err=a.kind, note=a.note)
    was = (" (was: %s)" % st.last_err) if st.last_err and st.last_err != a.kind else ""
    return 0, "mistake on %s recorded as %s%s" % (a.item, a.kind, was)


def cmd_quick(c, a):
    return 0, session.quick(c.repo, c.tree, c.state, c.when, a.topic, a.result, note=a.note, err=a.err, hints=a.hints)


def cmd_covered(c, a):
    return 0, session.covered(c.repo, c.tree, a.topics, by=a.by)


def cmd_enroll(c, a):
    return 0, session.enroll(c.repo, c.tree, c.state, a.skill, mode=a.mode or c.repo.prof("mode.default", "mastery"),
                             force=a.force)


def _enrollment(what):
    def run(c, a):
        return 0, session.set_enrollment(c.repo, c.tree, c.state, a.skill, what)
    return run


def cmd_weave(c, a):
    return 0, plan.weave_text(c.repo, c.tree, c.state, c.when, c.tree.get(a.skill).id, a.n)


def cmd_placement(c, a):
    return 0, session.placement(c.repo, c.tree, c.state, a.skill, a.known, a.gaps, a.result, a.note)


def cmd_boss(c, a):
    if a.action == "status":
        return 0, session.boss_status(c.repo, c.tree, c.state, a.skill)
    if not a.skill or a.result not in ("pass", "fail"):
        raise CalError("usage: boss record <skill> pass|fail --evidence \"...\"")
    return 0, session.boss_record(c.repo, c.tree, c.state, a.skill, a.result == "pass", a.evidence or "", a.kind)


def cmd_test(c, a):
    if a.action == "build":
        return session.test_build(c.repo, c.tree, c.state, c.when, a.skills, a.n, a.minutes, a.label)
    if not a.test:
        raise CalError("name the test id")
    if a.action == "finish":
        return 0, session.test_finish(c.repo, c.tree, c.state, c.when, a.test)
    test = c.state.tests.get(a.test)
    if test is None:
        raise CalError("unknown test %s" % a.test)
    lines = ["TEST %s%s · %d items · %s min · %s" % (
        a.test, (" (%s)" % test["label"]) if test.get("label") else "", len(test["items"]), test.get("minutes") or "?",
        "finished" if test["finished"] else "open")]
    for i, item_id in enumerate(test["items"], 1):
        ans = test["answers"].get(item_id)
        lines.append("  %d. %s  %s" % (i, item_id, "answered" if ans else "not answered"))
    return 0, "\n".join(lines)


# ---------------------------------------------------------------- items


def cmd_item(c, a):
    repo, tree = c.repo, c.tree
    if a.action == "needs":
        return 0, session.needs_text(repo, tree, c.state, c.when, a.skill, a.n, full=a.full)
    if a.action == "draft":
        item = items.create(repo, tree, _read_json(a), created_by=a.by or "examiner")
        _discard_draft_file(repo, a)
        return 0, ("draft stored: %s (%s, %s)\nIt stays invisible to the learner until an independent check passes:\n"
                   "  item show %s        (blind: no key)\n  item verify %s --answer <independent answer> --by checker"
                   % (item["id"], item["type"], item["topics"][0], item["id"], item["id"]))
    if a.action == "import":
        data = _read_json(a)
        if not isinstance(data, list):
            raise CalError("an import file is a JSON list of item drafts")
        if not data:
            raise CalError("the import file holds no drafts")
        for n, draft in enumerate(data, 1):  # check everything first: an import stores all drafts or none
            try:
                parts = items.validate_draft(draft, tree)
            except CalError as exc:
                raise CalError("item %d of %d: %s (nothing was stored)" % (n, len(data), exc))
            if a.official and parts["public"]["source"]["kind"] != "official":
                raise CalError("item %d of %d: --official needs source.kind 'official' with source.ref "
                               "(nothing was stored)" % (n, len(data)))
        made = []
        for draft in data:
            item = items.create(repo, tree, draft, created_by=a.by or "examiner")
            made.append(item["id"])
        _discard_draft_file(repo, a, batch=True)
        # Official questions go through the same blind check as any other: until the checker's answer
        # matches the official key, a slip in the transcription could reach the learner.
        tail = ("stored as drafts with their official keys; each needs the checker's blind answer (item verify). "
                "A mismatch puts the item on hold as disputed until the transcription is compared with the paper"
                if a.official else "stored as drafts; each needs: item verify")
        return 0, "imported %d item(s): %s\n%s" % (len(made), ", ".join(made), tail)
    if a.action == "tag":
        if len(a.item) != 1:
            raise CalError("item tag takes one item id: item tag <item> --objectives 1,3 [--strand T|P|I|N] "
                           "[--depth recall|apply|analyse|transfer]")
        ident = a.item[0]
        st = c.state.items.get(ident)
        if st is None or not st.topics:
            raise CalError("unknown item %s" % ident)
        if a.objectives is None and a.strand is None and a.depth is None:
            raise CalError("say what to tag: --objectives, --strand or --depth")
        tags = items.objective_tags(tree, st.topics[0], a.objectives, a.strand, a.depth)
        if a.objectives is None and st.objectives:                  # keep what it had
            tags["objectives"], tags["objsig"] = list(st.objectives), dict(st.objsig)
        repo.append("item_tag", item=ident, **tags)
        return 0, "tagged %s: %s" % (ident, ", ".join("%s %s" % (k, ",".join(map(str, v)) if isinstance(v, list) else v)
                                                     for k, v in tags.items() if k != "objsig"))
    if a.action == "list":
        rows = []
        for it in sorted(c.state.items.values(), key=lambda x: (x.skill or "", x.topics[0] if x.topics else "", x.id)):
            if a.skill and it.skill != a.skill:
                continue
            if a.topic and (not it.topics or it.topics[0] != a.topic):
                continue
            if a.status and it.status != a.status:
                continue
            rows.append([it.id, it.type or "", it.topics[0] if it.topics else "", it.status, it.src, it.n_shown,
                         "%d/%d" % (it.n_ok, it.n_ok + it.n_fail)])
        if not rows:
            return 0, "No items match."
        from .util import table

        return 0, table(rows, ["item", "type", "topic", "status", "source", "shown", "correct"], aligns="lllllrr")
    if not a.item:
        raise CalError("name the item id")
    if a.action == "show" and len(a.item) > 1:  # one call for a checker's whole batch
        blocks = []
        for ident in a.item:
            one = argparse.Namespace(**dict(vars(a), item=[ident]))
            blocks.append(cmd_item(c, one)[1])
        return 0, "\n\n".join(blocks)
    if a.action == "verify" and any("=" in word for word in a.item):  # a checker's whole batch in one call
        if a.answer is not None or a.ran or a.fail:
            raise CalError("give either <item>=<answer> pairs or one item with --answer / --ran")
        pairs = []
        for word in a.item:
            ident, sep, answer = word.partition("=")
            if not sep or not answer.strip():
                raise CalError("in a batch every word is <item>=<answer>; got %r" % word)
            pairs.append((ident.strip(), answer.strip()))
        if len({ident for ident, _ in pairs}) != len(pairs):
            raise CalError("an item appears twice in the batch")
        for ident, _ in pairs:  # every item is checked before anything is recorded
            item = items.load(repo, ident)
            st = c.state.items.get(ident)
            if item["type"] not in items.AUTO_TYPES:
                raise CalError("%s is a %s item: verify it on its own with --ran --evidence" % (ident, item["type"]))
            if st is not None and st.status == "rejected":
                raise CalError("item %s was rejected; write a new draft instead (nothing was recorded)" % ident)
            if st is not None and st.status == "verified":
                raise CalError("item %s is verified already (nothing was recorded)" % ident)
            if (a.by or "").strip() in (item.get("created_by"), "examiner"):
                raise CalError("an item cannot be verified by its own author or by the examiner (%s)" % a.by)
        lines = []
        for ident, answer in pairs:
            one = argparse.Namespace(**dict(vars(a), item=[ident], answer=answer))
            lines.append(cmd_item(c, one)[1].split("\n")[0])
        return 0, "\n".join(lines)
    if len(a.item) > 1:
        raise CalError("item %s takes one item id" % a.action)
    a.item = a.item[0]
    item = items.load(repo, a.item)
    st = c.state.items.get(a.item)
    status = st.status if st else "unknown"
    if a.action == "show":
        text = items.blind_text(item, tree, with_check=a.check)
        if a.reveal:
            # Nothing shown before an answer may leak a key: the key of an item opens only once the
            # learner has answered it, and never while it waits for an answer.
            if status == "draft":
                raise CalError("a draft is shown blind until it is verified")
            if st is None or not st.last_attempt:
                raise CalError("the key of %s stays sealed until the learner has answered it" % a.item)
            if st.open:
                raise CalError("%s is waiting for the learner's answer: record it first (answer %s ...)" % (a.item, a.item))
            text += "\n---\n" + items.reveal_text(item)
        return 0, text + "\n---\nstatus: %s%s" % (status, (" (%s)" % st.reason) if st and st.reason else "")
    if a.action == "verify":
        by = (a.by or "").strip()
        if not by:
            raise CalError("--by is required: who checked it (for example: checker)")
        if by == item.get("created_by") or by == "examiner":
            raise CalError("an item cannot be verified by its own author or by the examiner (%s): the "
                           "checker verifies" % by)
        if status == "rejected":
            raise CalError("item %s was rejected; write a new draft instead" % a.item)
        if status == "verified":
            raise CalError("item %s is verified already. If the learner disputes its key, solve it blind and "
                           "report your answer; the tutor decides with: item dispute %s --reason \"...\" --void"
                           % (a.item, a.item))
        if item["type"] in items.AUTO_TYPES:
            if a.answer is None:
                raise CalError("solve it independently, then: item verify %s --answer <your answer> --by %s" % (a.item, by))
            ok, _ = items.grade(item, a.answer)
            repo.append("item_verify", item=a.item, ok=ok, method="checker", by=by, note=a.note)
            scratch.discard_check(repo, a.item)
            if ok:
                return 0, "verified: %s (the independent answer matches the key)" % a.item
            verdict = "disputed" if item["source"]["kind"] in ("official", "imported") else "rejected"
            return 0, ("%s: %s (the independent answer does not match the key).\n"
                       "It will not be shown to the learner. %s" % (
                           verdict, a.item,
                           "Check the transcription against the official paper." if verdict == "disputed"
                           else "Draft a fresh item rather than repairing this one."))
        if a.fail:
            repo.append("item_verify", item=a.item, ok=False, method="ran", by=by, note=a.note or a.evidence)
            scratch.discard_check(repo, a.item)
            return 0, "rejected: %s" % a.item
        if not a.ran or not (a.evidence or "").strip():
            raise CalError("for a %s item: run its check on a reference solution, then: item verify %s --ran "
                           "--evidence \"what was run, what passed\" --by %s" % (item["type"], a.item, by))
        repo.append("item_verify", item=a.item, ok=True, method="ran", by=by, note=a.evidence.strip())
        scratch.discard_check(repo, a.item)
        return 0, "verified: %s (check ran and passed)" % a.item
    if a.action in ("reject", "dispute"):
        if not (a.reason or "").strip():
            raise CalError("--reason is required")
        if a.void and a.action != "dispute":
            raise CalError("--void goes with: item dispute")
        if a.action == "dispute" and status != "verified":
            raise CalError("only a verified item can be disputed (this one is %s)%s" % (
                status, "; reject it instead" if status == "draft" else ""))
        repo.append("item_" + a.action, item=a.item, reason=a.reason.strip())
        scratch.discard_check(repo, a.item)
        line = "%s: %s (it will not be asked again)" % ("rejected" if a.action == "reject" else "disputed", a.item)
        if a.void:
            if st is None or not st.last_attempt:
                line += "\nno recorded answer to void"
            else:
                repo.append("void", attempt=st.last_attempt, item=a.item, reason=a.reason.strip())
                line += "\nthe last answer to it no longer counts: the topic's schedule is as it was before that answer"
        return 0, line
    if a.action == "restore":
        if status != "disputed":
            raise CalError("only a disputed item can be restored (this one is %s)" % status)
        if not state_restorable(st):
            raise CalError("%s was never verified: it cannot be restored. Have the checker verify a fresh "
                           "draft instead" % a.item)
        repo.append("item_restore", item=a.item)
        return 0, "restored: %s is verified again" % a.item
    raise CalError("unknown item action")


# ---------------------------------------------------------------- tree


def _node_meta(a, base=None) -> dict:
    meta = dict(base or {})
    pairs = (("title", a.title), ("track", a.track), ("group", a.group), ("kind", a.kind), ("slot", a.slot),
             ("summary", a.summary), ("est_hours", a.hours))
    for key, value in pairs:
        if value is not None:
            meta[key] = value
    for key, value in (("prereqs", a.prereqs), ("tags", a.tags), ("weaves_into", a.weaves_into), ("aliases", a.aliases)):
        if value is not None:
            meta[key] = csv_list(value)
    if a.optional:
        meta["optional"] = True
    return meta


def cmd_tree(c, a):
    from . import treeview

    repo, tree, state = c.repo, c.tree, None
    if a.action == "check":
        errors, warnings = tree.check()
        lines = ["ERROR " + e for e in errors] + ["warn  " + w for w in warnings]
        live = tree.live()
        lines.append("%d skills, %d topics, %d error(s), %d warning(s)" % (
            len(live), sum(len(n.topics) for n in live), len(errors), len(warnings)))
        return (2 if errors else 0), "\n".join(lines)
    if a.action == "add":
        if not a.id or not a.title:
            raise CalError("tree add needs --id and --title")
        meta = {"id": a.id}
        meta.update(_node_meta(a))
        meta.setdefault("track", "custom")
        meta.setdefault("group", "misc")
        body = "# Scope\n\n%s\n" % (a.scope or "- (list what mastery of this skill covers; the syllabus is built from it)")
        tree_mod.add_node(repo, meta, body)
        c.refresh()
        return 0, "added: %s\n%s" % (a.id, treeview.show_text(repo, c.tree, c.state, c.when, a.id, a.ascii))
    if not a.skill and a.action in ("show", "path", "set", "drop", "restore"):
        raise CalError("name the skill")
    if a.action == "set":
        changes = _node_meta(a)
        if a.clear_slot:
            changes["slot"] = None
        if a.not_optional:
            changes["optional"] = None
        if not changes:
            raise CalError("nothing to change; pass for example --prereqs a,b or --slot name")
        tree_mod.set_node(repo, a.skill, changes)
        c.refresh()
        return 0, "updated: %s (saved in learner/tree/%s.md)\n%s" % (
            a.skill, a.skill, treeview.show_text(repo, c.tree, c.state, c.when, a.skill, a.ascii))
    if a.action == "drop":
        state = c.state
        node = tree.get(a.skill)
        active = [d.id for d in tree.dependents(a.skill) if (state.skills.get(d.id) and state.skills[d.id].enrolled)]
        waiting = [d.id for d in tree.dependents(a.skill)]
        if (active or waiting) and not a.yes:
            lines = ["%s is a prerequisite of: %s" % (a.skill, ", ".join(waiting))]
            if active:
                lines.append("you are learning: %s" % ", ".join(active))
            lines.append("Dropping it treats that prerequisite as met for them. To go ahead: tree drop %s --yes" % a.skill)
            raise CalError("\n".join(lines))
        tree_mod.drop_node(repo, a.skill)
        return 0, "dropped: %s | %s (progress is kept; bring it back with: tree restore %s)" % (a.skill, node.title, a.skill)
    if a.action == "restore":
        tree_mod.restore_node(repo, a.skill)
        return 0, "restored: %s" % a.skill
    state = c.state
    if a.action == "list":
        return 0, treeview.list_text(repo, tree, state, a.track, a.group, a.status, a.ascii)
    if a.action == "show":
        return 0, treeview.show_text(repo, tree, state, c.when, a.skill, a.ascii)
    if a.action == "path":
        return 0, treeview.path_text(repo, tree, state, a.skill, a.ascii)
    if a.action == "suggest":
        return 0, treeview.suggest_text(repo, tree, state, a.n, a.ascii)
    raise CalError("unknown tree action")


def cmd_find(c, a):
    from . import treeview

    return 0, treeview.find_text(c.repo, c.tree, c.state, " ".join(a.query))


def cmd_syllabus(c, a):
    node = c.tree.get(a.skill)
    path = os.path.join(c.repo.syllabus_dir, node.id + ".md")
    if a.action == "path":
        os.makedirs(c.repo.syllabus_dir, exist_ok=True)
        return 0, c.repo.rel(path)
    if a.action == "template":
        scope = node.section("Scope") or "(no Scope section in the skill file)"
        text = (
            "Write %s in exactly this shape, then run: syllabus check %s\n\n"
            "---\nskill: %s\nwritten: %s\nsources: [https://official.docs/..., https://...]\n---\n\n# Topics\n\n"
            "## first-topic-id | Human title\nneeds: []\nlevel: 1\n- what the learner must be able to do (one line each)\n\n"
            "## second-topic-id | Human title\nneeds: [first-topic-id]\nlevel: 2\n- ...\n\n"
            "Rules: ids are lower-case words joined by '-'; order topics so every 'needs' comes earlier;\n"
            "level is 1-5; 8-25 topics; one small idea per topic (a 20-40 minute chunk).\n\n"
            "Scope from the skill file (%s):\n%s"
        ) % (c.repo.rel(path), node.id, node.id, c.when.date().isoformat(), c.repo.rel(node.path), scope)
        return 0, text
    errors, warnings = c.tree.check()
    rel_paths = {c.repo.rel(path), c.repo.rel(node.path)}
    mine = [e for e in errors if any(e.startswith(p) for p in rel_paths)]
    lines = ["ERROR " + e for e in mine]
    if not node.topics and not mine:
        lines.append("ERROR no topics found. The file needs a '# Topics' section with '## id | Title' entries.")
    lines += ["warn  " + w for w in warnings if any(w.startswith(p) for p in rel_paths)]
    for topic in node.topics:
        for line in topic.body.split("\n"):
            tag = re.match(r"^[-*] \[([^\]]{1,3})\]", line)
            if tag and tag.group(1) not in ("T", "P", "I", "N"):
                lines.append("warn  %s: [%s] is not a strand tag (T theory, P practice, I implementation, N numerical)"
                             % (topic.key, tag.group(1)))
        text = {str(o["n"]): hashlib.sha1(o["text"].encode("utf-8")).hexdigest()[:8] for o in topic.objectives()}
        drift = sorted({it.id for it in c.state.items.values() if it.topics and it.topics[0] == topic.key
                        and any(text.get(n) != sig for n, sig in it.objsig.items())})
        if drift:
            lines.append("warn  %s: objectives changed since item(s) %s were tagged; re-tag them (item tag) or "
                         "check they still fit" % (topic.key, ", ".join(drift[:5])))
    if any(l.startswith("ERROR") for l in lines):
        return 2, "\n".join(lines)
    lines.append("ok: %s has %d topics (%s)" % (node.id, len(node.topics),
                                               "your syllabus" if node.topics_origin == "learner" else "shipped"))
    return 0, "\n".join(lines)


def cmd_rename(c, a):
    if a.what == "topic":
        if not c.tree.has_topic(a.new):
            raise CalError("rename the topic in the syllabus first; %r does not exist yet" % a.new)
    else:
        c.tree.get(a.new)
    c.repo.append("rename", what=a.what, old=a.old, new=a.new)
    return 0, "progress recorded under %s now counts for %s" % (a.old, a.new)


# ---------------------------------------------------------------- sources, gate, cf, notes


def cmd_source(c, a):
    repo = c.repo
    if a.action == "add":
        if not a.source:
            raise CalError("name the source id")
        path = sources.add(repo, a.source, a.title or a.source, a.kind, a.url or "", a.route, a.tracks, a.note or "")
        return 0, "source created: %s\nadd its items with: source import %s --file items.json" % (repo.rel(path), a.source)
    if a.action == "import":
        if not a.source:
            raise CalError("name the source id")
        rows = _read_json(a)
        if a.dry_run:
            added, replaced = sources.import_items(repo, a.source, rows, dry_run=True)
            unknown = sorted({str(k) for row in rows for k in csv_list(row.get("topics"))
                              if not c.tree.has_topic(str(k))})
            unmapped = sum(1 for row in rows if not csv_list(row.get("topics")))
            lines = ["dry run, nothing written: %d item(s) would be added, %d replaced" % (added, replaced)]
            lines += ["ERROR unknown topic %s" % k for k in unknown]
            if unmapped:
                lines.append("warn  %d item(s) not mapped to any topic" % unmapped)
            return (2 if unknown else 0), "\n".join(lines)
        added, replaced = sources.import_items(repo, a.source, rows)
        c.refresh()
        errors, warnings = sources.check(repo, c.tree)
        tail = "\n".join(["ERROR " + e for e in errors] + ["warn  " + w for w in warnings])
        return (2 if errors else 0), "items: %d added, %d replaced%s" % (added, replaced, ("\n" + tail) if tail else "")
    if a.action == "check":
        errors, warnings = sources.check(repo, c.tree)
        lines = ["ERROR " + e for e in errors] + ["warn  " + w for w in warnings]
        lines.append("%d source(s), %d error(s), %d warning(s)" % (len(sources.load_all(repo)), len(errors), len(warnings)))
        return (2 if errors else 0), "\n".join(lines)
    return 0, sources.status_text(repo, c.state, c.tree, a.source)


def cmd_log(c, a):
    if a.upto:
        if a.undo:
            raise CalError("--upto cannot be combined with --undo")
        done = sources.log_upto(c.repo, c.state, a.source, a.item, a.method)
        if not done:
            return 0, "nothing to log: everything up to that item was already done"
        topics = sum(1 for it in done for k in it.topics if c.tree.has_topic(k))
        return 0, ("logged %d lecture(s) as watched earlier, up to %s | %s\n%d mapped topic(s) are now ready to be "
                   "tested. They do not count as today's lectures." % (len(done), done[-1].id, done[-1].title, topics))
    item = sources.log(c.repo, a.source, a.item, not a.undo, a.score, a.method)
    mapped = [k for k in item.topics if c.tree.has_topic(k)]
    line = "%s: %s %s | %s" % ("un-logged" if a.undo else "logged", a.source, item.id, item.title)
    if mapped and not a.undo:
        line += "\nready to be tested: %s" % ", ".join(mapped)
    elif not a.undo:
        line += "\n(this item is not mapped to a syllabus topic yet)"
    return 0, line


def cmd_gate(c, a):
    from . import gate, stats

    repo, tree, state = c.repo, c.tree, c.state
    if a.action == "status":
        return 0, gate.status_text(repo, tree, state, c.when)
    if a.action == "triage":
        return 0, gate.triage_text(repo, tree, state, c.when)
    if a.action == "enroll":
        return 0, gate.enroll_all(repo, tree, state, a.mode or "mastery")
    if a.action == "mocks":
        return 0, gate.mocks_text(repo, state, (a.args[0].upper() if a.args else None))
    if a.action == "errors":
        return 0, stats.errors_text(repo, tree, state, "gate")
    if a.action == "weights":
        return 0, gate.weights_from_items(repo, tree, state, a.apply)
    if a.action == "mock":
        if len(a.args) < 2:
            raise CalError("usage: gate mock <PAPER> <score> [--max 100] --source \"...\"")
        return 0, gate.mock_add(repo, a.args[0], items.parse_number(a.args[1]), a.max, a.date, a.source or "",
                                a.sections, a.minutes, a.note)
    if a.action == "weight":
        if len(a.args) < 2:
            raise CalError("usage: gate weight <subject> <marks> --source \"...\"")
        return 0, gate.weight_set(repo, tree, a.args[0], items.parse_number(a.args[1]), a.source or "")
    raise CalError("unknown gate action")


def cmd_cf(c, a):
    from . import cf

    repo, tree, state, when = c.repo, c.tree, c.state, c.when
    if a.action == "link":
        if not a.args:
            raise CalError("usage: cf link <handle>")
        return 0, cf.link(repo, a.args[0])
    if a.action == "sync":
        return 0, cf.sync(repo, tree, state, a.full)
    if a.action == "status":
        return 0, cf.status_text(repo, state, when)
    if a.action == "analyse":
        return 0, cf.analyse_text(repo, tree, state, when, a.days)
    if a.action == "recommend":
        return 0, cf.recommend_text(repo, tree, state, when, a.n, a.tags, a.low, a.high, hide_tags=not a.show_tags,
                                    skill=a.skill)
    if a.action == "upsolve":
        return 0, cf.upsolve_text(repo, tree, state, when)
    if a.action == "contests":
        return 0, cf.contests_text(repo, tree, state, when, a.n)
    if a.action == "rating":
        return 0, cf.rating_text(repo, state, when, tree)
    if a.action == "credit":
        if not a.args or not a.topic:
            raise CalError("usage: cf credit <problem> --topic <skill>/<topic> [--also <skill>/<topic>,...] [--hints N]")
        return 0, cf.credit(repo, tree, state, when, a.args[0], a.topic, a.also, a.hints, a.note)
    if a.action == "mark":
        if len(a.args) < 2:
            raise CalError("usage: cf mark <problem> editorial|resolved|skip|subtag|note [--subtags a,b] [--note ...]")
        return 0, cf.mark(repo, a.args[0], a.args[1], a.subtags, a.note)
    if a.action == "assign":
        return 0, cf.assign(repo, a.args, a.reason)
    raise CalError("unknown cf action")


def cmd_notes(c, a):
    from . import notes

    repo, tree = c.repo, c.tree
    if a.action == "status":
        return 0, notes.status_text(repo, tree, a.target)
    if not a.target:
        raise CalError("name the skill (or <skill>/<topic> for fragment and section)")
    if a.action == "fragment":
        return 0, repo.rel(notes.fragment_path(repo, tree, a.target))
    if a.action == "section":
        return 0, repo.rel(notes.section_path(repo, tree, a.target))
    if a.action == "stamp":
        return 0, notes.stamp(repo, tree, a.target)
    if a.action == "assemble":
        return 0, "assembled: " + repo.rel(notes.assemble(repo, tree, a.target))
    if a.action == "pdf":
        return 0, notes.pdf(repo, tree, a.target)
    raise CalError("unknown notes action")


# ---------------------------------------------------------------- observation, stats, dashboards


def cmd_stats(c, a):
    from . import stats

    if a.action == "week":
        return 0, stats.week_text(c.repo, c.state, c.when, a.days)
    if a.action == "hours":
        return 0, stats.hours_text(c.repo, c.state, c.when)
    if a.action == "patterns":
        return 0, stats.patterns_text(c.repo, c.tree, c.state, c.when)
    if a.action == "errors":
        return 0, stats.errors_text(c.repo, c.tree, c.state, a.track)
    flags = stats.flags(c.repo, c.tree, c.state, c.when)
    return 0, "\n".join(flags) if flags else "No teaching observation stands out yet."


def cmd_observe(c, a):
    text = " ".join(a.text).strip()
    if len(text) < 3:
        raise CalError("say what was observed")
    if a.topic:
        c.tree.topic(a.topic)
    if a.skill:
        c.tree.get(a.skill)
    c.repo.append("note", text=text, tag=a.tag or "teaching", pattern=a.pattern, skill=a.skill, topic=a.topic)
    return 0, "noted (%s)" % (a.tag or "teaching")


def cmd_observations(c, a):
    notes_ = [n for n in c.state.notes if not a.tag or n.get("tag") == a.tag]
    if not notes_:
        return 0, "No observations recorded."
    lines = []
    for n in notes_[-a.n:]:
        where = n.get("topic") or n.get("skill") or ""
        lines.append("%s [%s%s] %s" % (n["ts"].strftime("%Y-%m-%d"), n.get("tag") or "teaching",
                                       (" " + where) if where else "", n["text"]))
    return 0, "\n".join(lines)


def cmd_workout(c, a):
    if a.minutes <= 0 or a.minutes > 600:
        raise CalError("minutes must be between 1 and 600")
    c.repo.append("activity", kind="workout", minutes=a.minutes, note=a.note)
    return 0, "workout logged: %d min" % a.minutes


def cmd_dash(c, a):
    from . import dash

    width = a.width or term_width()
    repo, tree, state, when = c.repo, c.tree, c.state, c.when
    if a.view == "roadmap":
        return 0, dash.roadmap(repo, tree, state, when, width, a.ascii, a.track, a.all_tracks)
    if a.view == "queue":
        return 0, dash.queue(repo, tree, state, when, width, a.ascii)
    if a.view == "week":
        return 0, dash.week(repo, tree, state, when)
    if a.view == "gate":
        from . import gate

        return 0, gate.status_text(repo, tree, state, when) + "\n\n" + gate.mocks_text(repo, state)
    if a.view == "cp":
        from . import cf

        if not repo.prof("cp.handle") or cf.load(repo) is None:
            return 0, cf.status_text(repo, state, when)
        return 0, cf.rating_text(repo, state, when, tree) + "\n\n" + cf.analyse_text(repo, tree, state, when)
    if a.view == "all":
        return 0, dash.everything(repo, tree, state, when, width, a.ascii)
    return 0, dash.progress(repo, tree, state, when, width, a.ascii)


def _inputs_stamp(repo) -> str:
    """One hash over the name, size and modification time of every file a view is worked out from."""
    seen = []
    tops = [repo.events_dir, repo.syllabus_dir, repo.tree_dir, repo.sources_dir, os.path.join(repo.learner, "gate"),
            repo.framework, os.path.dirname(os.path.abspath(__file__))]
    paths = [repo.profile_path]
    for top in tops:
        for base, dirs, files in os.walk(top):
            dirs[:] = sorted(d for d in dirs if d != "__pycache__")
            paths.extend(os.path.join(base, name) for name in sorted(files))
    for path in paths:
        try:
            st = os.stat(path)
        except OSError:
            continue
        seen.append("%s|%d|%d" % (path, st.st_size, st.st_mtime_ns))
    return hashlib.sha256("\n".join(seen).encode("utf-8", "replace")).hexdigest()


def cmd_statusline(c, a):
    """Claude Code runs this after every reply, so the answer is kept for as long as it holds:
    until a file it was worked out from changes, or the minute does."""
    from . import dash

    try:
        from . import advise

        current = None
        if getattr(a, "stdin", False):
            try:  # Claude Code passes the session's model and effort on stdin (setup writes --stdin)
                current = json.loads(decode_text(_stdin_bytes()) or "{}")
            except (ValueError, OSError, AttributeError):
                current = None
        key = "%s|%s|%s" % (_inputs_stamp(c.repo), c.when.strftime("%Y-%m-%dT%H:%M%z"), advise.current_text(current))
        kept = c.repo.read_json_cache("statusline.json")
        if isinstance(kept, dict) and kept.get("key") == key and isinstance(kept.get("text"), str):
            return 0, kept["text"]
        text = dash.statusline(c.repo, c.tree, c.state, c.when, current)
        try:
            c.repo.write_json_cache("statusline.json", {"key": key, "text": text})
        except OSError:
            pass
        return 0, text
    except Exception:
        return 0, "CAL"


# ---------------------------------------------------------------- profile and machine


def cmd_profile(c, a):
    repo = c.repo
    # `--text` may stand anywhere after the action; argparse leaves it among the words in some places
    tokens = ([a.key] if a.key else []) + list(a.value or [])
    words = [w for w in tokens if w != "--text"]
    a.text = a.text or len(words) != len(tokens)
    a.key, a.value = (words[0], words[1:]) if words else (None, [])
    if a.action == "show":
        meta = repo.profile()
        if not meta:
            return 0, "No profile yet (learner/profile.md)."
        return 0, "\n".join("%s: %s" % (k, fm.dump_value(v)) for k, v in sorted(meta.items()))
    if not a.key:
        raise CalError("name the key")
    if a.action == "get":
        value = repo.profile().get(a.key)
        return 0, "" if value is None else fm.dump_value(value)
    if a.action == "unset":
        repo.set_profile(a.key, None)
        return 0, "unset: %s" % a.key
    if "=" in a.key:  # several at once: profile set name=Robin tracks=gate-da "teach.style=examples first"
        changes, lines = {}, []
        for word in [a.key] + list(a.value):
            key, sep, raw = word.partition("=")
            key = key.strip()
            if not sep or not key:
                raise CalError("with key=value, every word is key=value (quote a value with spaces); got %r" % word)
            changes[key] = profile_rules.parse(key, [raw], a.text, repo.config_defaults())  # all checked first
        repo.set_profile_many(changes)
        for key, value in changes.items():
            lines.append("unset: %s" % key if value is None else "%s: %s" % (key, fm.dump_value(value)))
            if value is not None and not profile_rules.known(key):
                lines.append("note: the engine does not read %r; free notes belong below the keys in "
                             "learner/profile.md" % key)
        return 0, "\n".join(lines)
    if not a.value:
        raise CalError("usage: profile set <key> <value>")
    value = profile_rules.parse(a.key, a.value, a.text, repo.config_defaults())
    repo.set_profile(a.key, value)
    if value is None:
        return 0, "unset: %s" % a.key
    line = "%s: %s" % (a.key, fm.dump_value(value))
    if not profile_rules.known(a.key):
        line += ("\nnote: the engine does not read %r. Free notes about the learner belong in the text below the "
                 "keys in learner/profile.md; the keys it reads are listed in framework/rules/engine.md." % a.key)
    return 0, line


def cmd_setup(c, a):
    from . import machine

    if a.remove_hook or a.remove_statusline or a.remove_alias:
        done = []
        if a.remove_hook:
            done.append(machine.remove_hook(c.repo))
        if a.remove_statusline:
            done.append(machine.remove_statusline(c.repo))
        if a.remove_alias:
            done.append(machine.remove_alias(c.repo))
        return 0, "\n".join(done)
    return 0, machine.setup(c.repo, a.machine, a.hook, a.statusline, a.alias)


def cmd_doctor(c, a):
    from . import machine

    return machine.doctor(c.repo)


def cmd_day(c, a):
    from . import day

    words = list(a.words)
    action = words.pop(0) if words and words[0] in ("note", "goal", "done", "undone", "migrate") else "show"
    if action == "migrate":
        return 0, day.migrate(c.repo, write=a.write)
    if action == "note":
        if not words:
            raise CalError("day note <day> \"what is different that day\" (an empty note removes it)")
        return 0, day.set_note(c.repo, day.parse_day(words[0], c.repo, c.when), " ".join(words[1:]))
    when = day.parse_day(a.date, c.repo, c.when)
    if action == "goal":
        return 0, day.add_goal(c.repo, when, " ".join(words), at=a.at, block=a.block)
    if action in ("done", "undone"):
        if len(words) != 1 or not words[0].isdigit():
            raise CalError("day %s <goal number> [--date <day>]" % action)
        return 0, day.mark_goal(c.repo, when, int(words[0]), action == "done")
    if len(words) > 1:
        raise CalError("day [<day>]: one day at a time (today, tomorrow, +2, fri, 2026-11-03)")
    target = day.parse_day(words[0] if words else a.date, c.repo, c.when)
    v = day.view(c.repo, target, c.when)
    finish = None
    if target == day.learner_date(c.repo, c.when) and c.repo.onboarded():
        finish = plan.today_line(plan.today(c.repo, c.tree, c.state, c.when))
    if a.json:
        return 0, json.dumps(dict(v, finish=finish), ensure_ascii=False, indent=1)
    return 0, day.text(v, finish)


def cmd_book(c, a):
    from . import mdbook

    folder = os.path.isdir(a.target)
    joined = mdbook.source(c.repo, a.target)
    out = a.out or (os.path.join(a.target, "book.pdf") if folder else None)
    try:
        return 0, mdbook.pdf(c.repo, joined, out, base=os.path.abspath(a.target) if folder else None)
    finally:
        if folder:
            os.remove(joined)


def cmd_guard(c, a):
    from . import guard

    return guard.hook_main(), ""


def cmd_clean(c, a):
    return 0, scratch.clean(c.repo, dry_run=a.dry_run)


def cmd_rebuild(c, a):
    from . import progress, snapshot

    snapshot.discard(c.repo)  # rebuild means from scratch: the next snapshot is made from this replay
    errors, warnings = c.tree.check()
    state = c.state
    path = progress.write(c.repo, c.tree, state)
    lines = ["replayed %d event(s) from %d file(s)" % (state.n_events, len(c.repo.event_files())),
             "tree: %d error(s), %d warning(s)" % (len(errors), len(warnings)),
             "wrote %s" % c.repo.rel(path)]
    if c.repo.event_errors:
        lines.append("%d event line(s) could not be read:" % len(c.repo.event_errors))
        lines += ["  " + e for e in c.repo.event_errors[:5]]
    return (2 if (errors or c.repo.event_errors) else 0), "\n".join(lines)


def cmd_selftest(c, a):
    engine_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env = {k: v for k, v in os.environ.items() if not k.startswith("CALAMITY_")}
    proc = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", os.path.join(engine_dir, "tests"), "-t", engine_dir],
                          cwd=engine_dir, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = proc.stdout.decode("utf-8", "replace").strip().split("\n")
    if proc.returncode == 0:
        return 0, "\n".join(out[-4:])
    return 2, "\n".join(out[-400:])  # the whole report: the failure is what the reader needs


def cmd_version(c, a):
    path = os.path.join(c.repo.framework, VERSION_FILE)
    version = read_text(path).strip() if os.path.isfile(path) else "unknown"
    return 0, "Calamity framework %s · state schema %s · Python %s" % (
        version, c.repo.cfg("schema", 1), sys.version.split()[0])


def cmd_remind(c, a):
    from . import remind

    if a.action == "check":
        return remind.check(c.repo, c.tree, c.state, c.when, a.always)
    if a.action == "remove":
        return 0, remind.remove(c.repo, a.os)
    return 0, remind.render(c.repo, a.times, a.os)


# ---------------------------------------------------------------- parser


def _number(kind, low, what):
    def convert(text):
        try:
            value = kind(text)
        except (TypeError, ValueError):
            raise argparse.ArgumentTypeError("%r is not a number" % text)
        if value != value or value < low:
            raise argparse.ArgumentTypeError("%s, got %s" % (what, text))
        return value
    return convert


_positive = _number(int, 1, "must be 1 or more")
_count = _number(int, 0, "must be 0 or more")
_hours = _number(float, 0, "must be 0 or more")
_width = _number(int, 20, "must be 20 or more")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="calamity", description="The Calamity learning engine.")
    sub = p.add_subparsers(dest="cmd", metavar="<command>")

    def add(name, func, help_text):
        sp = sub.add_parser(name, help=help_text, description=help_text)
        sp.set_defaults(func=func)
        return sp

    sp = add("brief", cmd_brief, "Session-start summary of where the learner stands.")
    sp.add_argument("--hook", action="store_true", help="called by the SessionStart hook")
    add("today", cmd_today, "Today's plan and finish line.")
    sp = add("next", cmd_next, "The single next thing to do.")
    sp.add_argument("--skill", help="draw new material only from this skill")
    sp.add_argument("--only", action="store_true", help="also restrict reviews to --skill")

    sp = add("ask", cmd_ask, "Serve one verified item (for a topic, an item id, or whatever is next).")
    sp.add_argument("--topic")
    sp.add_argument("--id")
    sp.add_argument("--skill")
    sp.add_argument("--test")
    sp.add_argument("--check", action="store_true", help="also print the check/rubric of a hands-on item")
    sp.add_argument("--due", action="store_true", help="serve a review only: never new material")
    sp.add_argument("--taught", action="store_true", help="with --topic: record that it was just taught, then serve")
    sp = add("answer", cmd_answer, "Record the learner's answer to the open item.")
    sp.add_argument("item")
    sp.add_argument("--answer", help="the learner's answer (mcq/msq/nat/short)")
    sp.add_argument("--result", choices=("pass", "fail"), help="outcome of a hands-on item's check")
    sp.add_argument("--evidence", help="what was run and what happened (hands-on items)")
    sp.add_argument("--hints", type=_count, default=0)
    sp.add_argument("--err", help="error kind when wrong: " + ", ".join(session.ERROR_TAGS))
    sp.add_argument("--note")
    sp.add_argument("--seconds", type=_count, help="time taken, if measured by hand")
    sp.add_argument("--blame", help="when a woven exercise fails: the topic(s) that broke")
    sp.add_argument("--kind", choices=("new", "review", "weave", "boss", "placement"))
    sp.add_argument("--next", action="store_true",
                    help="after a right answer, also serve what `ask` would (one call instead of two)")
    sp.add_argument("--skill", help="with --next: draw new material from this skill, as ask --skill does")
    sp.add_argument("--due", action="store_true", help="with --next: serve a review only, as ask --due does")
    sp = add("mistake", cmd_mistake, "Say what kind of mistake the last wrong answer to an item was.")
    sp.add_argument("item")
    sp.add_argument("kind", choices=session.ERROR_TAGS)
    sp.add_argument("--note")
    sp = add("quick", cmd_quick, "Record an oral check (schedules the topic; never mastery evidence).")
    sp.add_argument("topic")
    sp.add_argument("result", choices=("pass", "fail"))
    sp.add_argument("--note")
    sp.add_argument("--err")
    sp.add_argument("--hints", type=_count, default=0)
    sp = add("covered", cmd_covered, "Mark topics as taught (ready for their first test).")
    sp.add_argument("topics", nargs="+")
    sp.add_argument("--by", default="tutor", choices=("tutor", "self", "source"))

    sp = add("enroll", cmd_enroll, "Start learning a skill.")
    sp.add_argument("skill")
    sp.add_argument("--mode", choices=session.MODES)
    sp.add_argument("--force", action="store_true", help="start even though prerequisites are unmet")
    for name, text in (("pause", "Pause a skill (its reviews stop)."), ("resume", "Resume a paused skill."),
                       ("unenroll", "Stop a skill (progress is kept).")):
        add(name, _enrollment(name), text).add_argument("skill")
    sp = add("weave", cmd_weave, "Earlier topics to embed in the next exercise for a skill.")
    sp.add_argument("skill")
    sp.add_argument("--n", type=_positive)
    sp = add("placement", cmd_placement, "Record the outcome of a placement test.")
    sp.add_argument("skill")
    sp.add_argument("--known", help="topic ids the learner already knows")
    sp.add_argument("--gaps", help="topic ids still to learn")
    sp.add_argument("--result", choices=("known", "partial", "none"))
    sp.add_argument("--note")
    sp = add("boss", cmd_boss, "Boss tests and projects: status, or record an attempt.")
    sp.add_argument("action", choices=("status", "record"))
    sp.add_argument("skill", nargs="?")
    sp.add_argument("result", nargs="?")
    sp.add_argument("--evidence")
    sp.add_argument("--kind", default="project", choices=("project", "test", "capstone"))
    sp = add("test", cmd_test, "Timed mixed tests built from verified items.")
    sp.add_argument("action", choices=("build", "show", "finish"))
    sp.add_argument("test", nargs="?")
    sp.add_argument("--skills")
    sp.add_argument("--n", type=_positive, default=10)
    sp.add_argument("--minutes", type=_positive, default=25)
    sp.add_argument("--label")

    sp = add("item", cmd_item, "Item bank: needs, draft, import, show (blind), verify, list, reject, dispute, restore, tag.")
    sp.add_argument("action", choices=("needs", "draft", "show", "verify", "reject", "dispute", "restore", "list", "import",
                                       "tag"))
    sp.add_argument("item", nargs="*", help="item id (show takes several)")
    sp.add_argument("--file")
    sp.add_argument("--stdin", action="store_true")
    sp.add_argument("--by")
    sp.add_argument("--answer")
    sp.add_argument("--ran", action="store_true")
    sp.add_argument("--fail", action="store_true")
    sp.add_argument("--evidence")
    sp.add_argument("--note")
    sp.add_argument("--reason")
    sp.add_argument("--check", action="store_true")
    sp.add_argument("--reveal", action="store_true")
    sp.add_argument("--official", action="store_true")
    sp.add_argument("--skill")
    sp.add_argument("--topic")
    sp.add_argument("--status", choices=("draft", "verified", "rejected", "disputed"))
    sp.add_argument("--n", type=_positive, default=6, help="needs: how many topics to list")
    sp.add_argument("--full", action="store_true", help="needs: with objectives, difficulty, format and topics to weave")
    sp.add_argument("--void", action="store_true", help="dispute: also cancel the last answer recorded against the item")
    sp.add_argument("--objectives", help="tag: the numbers of the primary topic's objectives it tests, e.g. 1,3")
    sp.add_argument("--strand", help="tag: T (theory), P (practice), I (implementation) or N (numerical)")
    sp.add_argument("--depth", help="tag: recall, apply, analyse or transfer")

    sp = add("tree", cmd_tree, "The skill tree: list, show, path, suggest, check, add, set, drop, restore.")
    sp.add_argument("action", choices=("list", "show", "path", "suggest", "check", "add", "set", "drop", "restore"))
    sp.add_argument("skill", nargs="?")
    sp.add_argument("--id")
    sp.add_argument("--title")
    sp.add_argument("--track")
    sp.add_argument("--group")
    sp.add_argument("--kind", choices=("skill", "milestone"))
    sp.add_argument("--prereqs", help="comma list of skill ids or slot:<name>")
    sp.add_argument("--slot", help="alternatives share a slot; 'slot:<name>' in a prerequisite accepts any of them")
    sp.add_argument("--clear-slot", action="store_true")
    sp.add_argument("--tags")
    sp.add_argument("--weaves-into", dest="weaves_into")
    sp.add_argument("--aliases")
    sp.add_argument("--summary")
    sp.add_argument("--scope", help="markdown bullet list of what mastery covers (tree add)")
    sp.add_argument("--hours", type=_hours)
    sp.add_argument("--optional", action="store_true")
    sp.add_argument("--not-optional", dest="not_optional", action="store_true")
    sp.add_argument("--status")
    sp.add_argument("--n", type=_positive, default=5)
    sp.add_argument("--yes", action="store_true")
    sp.add_argument("--ascii", action="store_true")
    sp = add("find", cmd_find, "Search skills, topics, lectures and notes.")
    sp.add_argument("query", nargs="+")
    sp = add("syllabus", cmd_syllabus, "Per-skill syllabus: template, path, check.")
    sp.add_argument("action", choices=("template", "path", "check"))
    sp.add_argument("skill")
    sp = add("rename", cmd_rename, "Carry progress over after renaming a topic or skill.")
    sp.add_argument("what", choices=("topic", "skill"))
    sp.add_argument("old")
    sp.add_argument("new")

    sp = add("source", cmd_source, "Study sources: add, import items, status, check.")
    sp.add_argument("action", choices=("add", "import", "status", "check"))
    sp.add_argument("source", nargs="?")
    sp.add_argument("--title")
    sp.add_argument("--kind", default="course", choices=sources.KINDS)
    sp.add_argument("--url")
    sp.add_argument("--route", default="manual-log", choices=sources.ROUTES)
    sp.add_argument("--tracks")
    sp.add_argument("--note", help="what the terms allow, in one line")
    sp.add_argument("--file")
    sp.add_argument("--stdin", action="store_true")
    sp.add_argument("--dry-run", dest="dry_run", action="store_true", help="import: check and count, write nothing")
    sp = add("log", cmd_log, "Log a lecture or chapter as done (by id, number or a piece of its title).")
    sp.add_argument("source")
    sp.add_argument("item")
    sp.add_argument("--undo", action="store_true")
    sp.add_argument("--upto", action="store_true", help="log everything up to and including this item (catching up)")
    sp.add_argument("--score")
    sp.add_argument("--method", choices=("manual", "manual-log", "paste", "screenshot", "api", "export",
                                         "browser-session"))

    sp = add("gate", cmd_gate, "GATE companion: status, triage, enroll, mock, mocks, errors, weight, weights.")
    sp.add_argument("action", choices=("status", "triage", "enroll", "mock", "mocks", "errors", "weight", "weights"))
    sp.add_argument("args", nargs="*")
    sp.add_argument("--max", type=float, default=100.0)
    sp.add_argument("--date")
    sp.add_argument("--source")
    sp.add_argument("--sections")
    sp.add_argument("--minutes", type=_positive)
    sp.add_argument("--note")
    sp.add_argument("--mode", choices=session.MODES)
    sp.add_argument("--apply", action="store_true")

    sp = add("cf", cmd_cf, "Codeforces: link, sync, status, analyse, recommend, upsolve, contests, rating, mark, assign, credit.")
    sp.add_argument("action", choices=("link", "sync", "status", "analyse", "recommend", "upsolve", "contests", "rating",
                                       "mark", "assign", "credit"))
    sp.add_argument("args", nargs="*")
    sp.add_argument("--full", action="store_true")
    sp.add_argument("--days", type=_positive, default=180)
    sp.add_argument("--n", type=_positive, default=5)
    sp.add_argument("--tags")
    sp.add_argument("--low", type=int)
    sp.add_argument("--high", type=int)
    sp.add_argument("--show-tags", dest="show_tags", action="store_true")
    sp.add_argument("--subtags")
    sp.add_argument("--note")
    sp.add_argument("--reason")
    sp.add_argument("--skill", help="recommend: take the tags from this cp skill")
    sp.add_argument("--topic", help="credit: the topic this problem exercised")
    sp.add_argument("--also", help="credit: further topics the same problem exercised")
    sp.add_argument("--hints", type=_count, default=0)

    sp = add("notes", cmd_notes, "Study notes: status, fragment, section, stamp, assemble, pdf.")
    sp.add_argument("action", choices=("status", "fragment", "section", "stamp", "assemble", "pdf"))
    sp.add_argument("target", nargs="?", help="a skill, or <skill>/<topic> for fragment and section")

    sp = add("stats", cmd_stats, "How the learner works: week, hours, patterns, errors, flags.")
    sp.add_argument("action", nargs="?", default="flags", choices=("flags", "week", "hours", "patterns", "errors"))
    sp.add_argument("--days", type=_positive, default=7)
    sp.add_argument("--track")
    sp = add("observe", cmd_observe, "Record an observation about what helps this learner.")
    sp.add_argument("text", nargs="+")
    sp.add_argument("--tag", help="teaching (default) or coach")
    sp.add_argument("--pattern", help="the behaviour pattern id this raises (coach)")
    sp.add_argument("--skill")
    sp.add_argument("--topic")
    sp = add("observations", cmd_observations, "Show recorded observations.")
    sp.add_argument("--tag")
    sp.add_argument("--n", type=_positive, default=15)
    sp = add("workout", cmd_workout, "Log a workout.")
    sp.add_argument("minutes", type=int)
    sp.add_argument("--note")

    sp = add("dash", cmd_dash, "Dashboards: progress, roadmap, queue, gate, cp, week, all.")
    sp.add_argument("view", nargs="?", default="progress", choices=("progress", "roadmap", "queue", "gate", "cp", "week", "all"))
    sp.add_argument("--width", type=_width)
    sp.add_argument("--ascii", action="store_true")
    sp.add_argument("--track")
    sp.add_argument("--all-tracks", dest="all_tracks", action="store_true")
    sp = add("statusline", cmd_statusline, "One line for the Claude Code status line.")
    sp.add_argument("--stdin", action="store_true",
                    help="read the session data Claude Code passes (its model and effort) from standard input")

    sp = add("profile", cmd_profile, "Learner profile: show, get, set, unset.")
    sp.add_argument("action", choices=("show", "get", "set", "unset"))
    sp.add_argument("key", nargs="?")
    sp.add_argument("value", nargs=argparse.REMAINDER, help="the value (the rest of the line)")
    sp.add_argument("--text", action="store_true", help="store the value as one piece of text (allowed anywhere)")
    sp = add("setup", cmd_setup, "Prepare this machine (machine id, folders, optional hook, status line and alias).")
    sp.add_argument("--machine", help="a name for this computer (default: from its host name)")
    sp.add_argument("--hook", action="store_true",
                    help="install the session-start hook and the key guard in .claude/settings.local.json")
    sp.add_argument("--remove-hook", dest="remove_hook", action="store_true",
                    help="take the session-start hook and the key guard out again")
    sp.add_argument("--statusline", action="store_true", help="show the finish line in Claude Code's status line")
    sp.add_argument("--remove-statusline", dest="remove_statusline", action="store_true",
                    help="take the status line out again")
    sp.add_argument("--alias", action="store_true",
                    help="add a `calamity` shell alias: cd here and run claude --dangerously-skip-permissions")
    sp.add_argument("--remove-alias", dest="remove_alias", action="store_true", help="take the alias out again")
    sp = add("day", cmd_day, "The day's shape: its blocks with the current one marked, the day's note and goals, "
                              "the finish line. Also: day note, day goal, day done, day migrate.")
    sp.add_argument("words", nargs="*", help="[<day>] | note <day> <text> | goal <text> | done|undone <n> | migrate")
    sp.add_argument("--date", help="goal, done, undone: the day (default today)")
    sp.add_argument("--at", help="goal: a time of day, HH:MM")
    sp.add_argument("--block", help="goal: the block it belongs to")
    sp.add_argument("--json", action="store_true", help="the day as JSON (tools/timetable.py reads it)")
    sp.add_argument("--write", action="store_true", help="migrate: rewrite learner/schedule.md (default: show it)")
    sp = add("book", cmd_book, "Study books: pdf turns a Markdown book (a file, or a folder of chapters) into a PDF.")
    sp.add_argument("action", choices=("pdf",))
    sp.add_argument("target", help="a .md file, or a book folder (README.md, then 01-*.md, 02-*.md ...)")
    sp.add_argument("--out", help="where to write the PDF (default: beside the book)")
    add("doctor", cmd_doctor, "Check that everything is in order.")
    sp = add("guard", cmd_guard, "The key guard Claude Code runs before each Read, Grep, Glob and shell call "
                                 "(installed by setup --hook; reads the call as JSON on stdin).")
    sp.add_argument("action", choices=("tool",))
    sp = add("clean", cmd_clean, "Remove the scratch folder's contents (.calamity/tmp), worked answers included.")
    sp.add_argument("action", choices=("tmp",))
    sp.add_argument("--dry-run", dest="dry_run", action="store_true", help="list what would go, remove nothing")
    add("rebuild", cmd_rebuild, "Replay the event log and rewrite learner/PROGRESS.md.")
    add("selftest", cmd_selftest, "Run the engine's own tests.")
    add("version", cmd_version, "Print versions.")
    sp = add("remind", cmd_remind, "Reminders: check what is due, render scheduler files, or print how to remove them.")
    sp.add_argument("action", choices=("check", "render", "remove"))
    sp.add_argument("--always", action="store_true", help="check: say something even when nothing is due")
    sp.add_argument("--times", help="render: times of day, e.g. 09:00,14:00,21:00 (default: reminders.times)")
    sp.add_argument("--os", choices=("linux", "darwin", "windows"), help="render: for another system than this one")
    return p


def main(argv=None) -> int:
    utf8_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 0
    try:
        code, text = args.func(Ctx(), args)
        if text:
            if getattr(args, "ascii", False):
                text = to_ascii(text)
            sys.stdout.write(text.rstrip("\n") + "\n")
            sys.stdout.flush()
    except CalError as exc:
        sys.stderr.write("error: %s\n" % exc)
        return 2
    except BrokenPipeError:
        return 0
    except KeyboardInterrupt:
        sys.stderr.write("interrupted\n")
        return 130
    except OSError as exc:  # the machine said no: a full disk, a file another program holds, no permission
        where = (" %s:" % exc.filename) if getattr(exc, "filename", None) else ""
        hint = (" Another program may have the file open, or it is read-only."
                if isinstance(exc, PermissionError) else "")
        sys.stderr.write("error:%s %s.%s\n" % (where, exc.strerror or exc, hint))
        return 2
    except Exception:  # a bug in the engine: say so plainly, keep the details for the report
        import traceback

        traceback.print_exc()
        sys.stderr.write("error: internal error in the engine (details above). Run `doctor`; if this keeps "
                         "happening, report it with the lines above.\n")
        return 2
    return int(code or 0)
