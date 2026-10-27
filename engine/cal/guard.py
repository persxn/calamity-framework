"""The key guard: Claude Code consults it before every Read, Grep, Glob and shell call.

An item's key, and the worked answer behind it, must never reach the conversation the learner
sees. Settings deny the Read tool learner/items/; this hook also covers searches, shell commands
and the examiner's and checker's scratch folders (cal.scratch), which hold computed answers until
the engine has stored or checked them. `setup --hook` installs it as a PreToolUse hook in
.claude/settings.local.json. Claude Code passes the call as JSON on standard input, with
`agent_type` set inside a subagent; a refusal is printed as JSON, and silence lets the call go on.

    learner/items/            nobody: the engine reads it, and agents see items through `item show`
    .calamity/tmp/examiner/   the examiner
    .calamity/tmp/checker/    the checker

It stops slips and instructions planted in pages or files, not a determined person at the keyboard.
"""
from __future__ import annotations

import json
import os
import sys

TOOLS = ("Read", "Grep", "Glob", "Bash", "PowerShell")
SHELLS = ("Bash", "PowerShell")


def _norm(path: str) -> str:
    return os.path.normcase(os.path.realpath(path))


def _inside(path: str, area: str) -> bool:
    try:
        return os.path.commonpath([path, area]) == area
    except ValueError:  # another drive
        return False


def _areas(root: str):
    """(area, the agent allowed in it or None, how it is named in a command)."""
    return [(os.path.join(root, "learner", "items"), None, "learner/items"),
            (os.path.join(root, ".calamity", "tmp", "examiner"), "examiner", ".calamity/tmp/examiner"),
            (os.path.join(root, ".calamity", "tmp", "checker"), "checker", ".calamity/tmp/checker")]


def _occupied(area: str) -> bool:
    try:
        with os.scandir(area) as entries:
            return any(True for _ in entries)
    except OSError:
        return False


def _narrowed(tool_input: dict) -> bool:
    """A search limited to files that cannot be item files (those are JSON)."""
    kind = str(tool_input.get("type") or "")
    if kind:
        return kind != "json"
    pattern = str(tool_input.get("glob") or "").replace("\\", "/")
    return bool(pattern) and "json" not in pattern.lower() and not pattern.rstrip("}").endswith("*")


def decide(payload: dict, root: str) -> str | None:
    """The reason to refuse this tool call, or None to let it go on."""
    tool = payload.get("tool_name")
    if tool not in TOOLS:
        return None
    agent = str(payload.get("agent_type") or "").rsplit(":", 1)[-1]  # plugin agents arrive as calamity:examiner
    tool_input = payload.get("tool_input") if isinstance(payload.get("tool_input"), dict) else {}
    cwd = str(payload.get("cwd") or os.getcwd())
    barred = [(area, name) for area, owner, name in _areas(root) if owner is None or owner != agent]
    who = "the %s agent" % agent if agent else "the tutor"

    if tool in SHELLS:
        command = str(tool_input.get("command") or "").replace("\\", "/")
        for _, name in barred:
            if name in command:
                return ("%s may not touch %s from the shell: it holds sealed keys or the work behind them. "
                        "Items are seen through the engine (item show, item list)." % (who, name))
        return None

    field = "file_path" if tool == "Read" else "path"
    target = str(tool_input.get(field) or "")
    if tool == "Glob" and not target:
        pattern = str(tool_input.get("pattern") or "")
        target = pattern.split("*", 1)[0].rsplit("/", 1)[0] if "/" in pattern.split("*", 1)[0] else ""
    target = _norm(os.path.join(cwd, target) if target else cwd)
    for area, name in barred:
        area = _norm(area)
        if _inside(target, area):
            return ("%s may not read %s: it holds sealed keys or the work behind them. "
                    "Items are seen through the engine (item show, item list)." % (who, name))
        if tool == "Grep" and _inside(area, target) and _occupied(area) and not _narrowed(tool_input):
            return ("this search would reach %s, which holds sealed keys or the work behind them: search a "
                    "narrower folder (framework/, engine/, learner/notes/ ...) or limit it to a file type" % name)
    return None


def hook_main(stream=None) -> int:
    """Run as the PreToolUse hook: read the call, print a refusal if there is one. Never block on a fault:
    a broken guard must not stop every tool, so `doctor` checks that it works."""
    from .store import Repo

    try:
        raw = (stream or sys.stdin.buffer).read()
        payload = json.loads(raw.decode("utf-8-sig") if isinstance(raw, bytes) else raw)
        reason = decide(payload, Repo().root) if isinstance(payload, dict) else None
    except Exception:  # noqa: BLE001 - see the docstring
        return 0
    if reason:
        sys.stdout.write(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                                            "permissionDecision": "deny",
                                                            "permissionDecisionReason": reason}}) + "\n")
    return 0


def works(root: str) -> bool:
    """Whether the guard refuses what it must and allows what it must (`doctor` runs this)."""
    items = os.path.join(root, "learner", "items", "x.json")
    scratch = os.path.join(root, ".calamity", "tmp", "examiner", "b", "a.py")
    framework = os.path.join(root, "framework", "method.md")
    return bool(decide({"tool_name": "Read", "tool_input": {"file_path": items}, "cwd": root}, root)
                and decide({"tool_name": "Bash", "tool_input": {"command": "cat learner/items/x.json"}, "cwd": root}, root)
                and decide({"tool_name": "Read", "tool_input": {"file_path": scratch}, "cwd": root}, root)
                and not decide({"tool_name": "Read", "tool_input": {"file_path": scratch}, "cwd": root,
                                "agent_type": "examiner"}, root)
                and not decide({"tool_name": "Read", "tool_input": {"file_path": framework}, "cwd": root}, root))
