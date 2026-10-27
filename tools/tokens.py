"""How many tokens Claude Code sessions spend in a checkout, read from their transcripts.

    python3 tools/tokens.py [--root DIR | --dir DIR] [--since YYYY-MM-DD] [--n 10]
    python3 tools/tokens.py --skills          per skill, across the same sessions
    python3 tools/tokens.py --session ID      one session: per request, agents, the largest tool results
    python3 tools/tokens.py --json            everything, for scripts (tools/baseline.py uses it)

Claude Code keeps one JSONL transcript per session under ~/.claude/projects/<folder>/, where
<folder> is the checkout's path with every other character than a letter or digit turned into
`-`; an agent's transcript sits in <session>/subagents/. Every API request records its usage:
fresh input, input written to the prompt cache, input read from it, and output. This tool adds
them up per session, per skill (each request names the skill it was made for) and per agent.

The *context* of a request is everything sent with it (fresh + cache write + cache read); the
first request of a session shows the fixed cost of the system prompt, tools, CLAUDE.md, the
skill listing and the session-start hook. *Weighted* input is an estimate of what the input
costs relative to fresh input: cache writes at 1.25x (5-minute) or 2x (1-hour), cache reads at
0.1x. It prints numbers and names only (tools, skills, agents, engine subcommands), never what
was said. Standard library only, like the engine. Read-only.
"""
import argparse
import glob
import json
import os
import re
import sys
from datetime import datetime

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENGINE_CALL = re.compile(r"engine/calamity\.py\s+([a-z-]+)(?:\s+([a-z-]+))?")
WITH_ACTIONS = {"item", "tree", "cf", "gate", "notes", "stats", "dash", "source", "test", "boss", "profile", "remind",
                "syllabus", "rename", "clean", "guard"}  # engine commands whose second word is an action


def transcripts_dir(root):
    """Where Claude Code keeps the transcripts of sessions started in `root`."""
    base = os.path.join(os.path.expanduser("~"), ".claude", "projects")
    for path in (os.path.abspath(root), os.path.realpath(root)):
        candidate = os.path.join(base, re.sub(r"[^A-Za-z0-9]", "-", path))
        if os.path.isdir(candidate):
            return candidate
    return os.path.join(base, re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(root)))


def _lines(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                if isinstance(entry, dict):
                    yield entry
    except OSError:
        return


def _usage(entry):
    message = entry.get("message") if isinstance(entry.get("message"), dict) else {}
    usage = message.get("usage") if isinstance(message.get("usage"), dict) else None
    if not usage:
        return None
    split = usage.get("cache_creation") if isinstance(usage.get("cache_creation"), dict) else {}
    write = int(usage.get("cache_creation_input_tokens") or 0)
    write_1h = int(split.get("ephemeral_1h_input_tokens") or 0)
    return {"input": int(usage.get("input_tokens") or 0), "cache_write": write, "cache_write_1h": write_1h,
            "cache_read": int(usage.get("cache_read_input_tokens") or 0),
            "output": int(usage.get("output_tokens") or 0)}


def _tool_label(name, tool_input):
    """A tool call named without its content: an engine command by its subcommand, a skill by name."""
    if name in ("Bash", "PowerShell"):
        match = ENGINE_CALL.search(str(tool_input.get("command", "")))
        if match:
            command, action = match.groups()
            keep = action and (action.startswith("--") or command in WITH_ACTIONS)  # never a learner's words
            return "%s · engine %s" % (name, command + (" " + action if keep else ""))
        return name
    if name == "Skill":
        return "Skill · %s" % tool_input.get("skill", "?")
    if name == "Agent":
        return "Agent · %s" % (tool_input.get("subagent_type") or "general-purpose")
    if name == "Read":
        path = str(tool_input.get("file_path", ""))
        parts = path.replace("\\", "/").split("/")
        for anchor in ("framework", ".claude", "engine", "learner", "docs", "tools"):
            if anchor in parts:
                return "Read · " + "/".join(parts[parts.index(anchor):])
        return "Read"
    return name


def _text_size(content):
    if isinstance(content, str):
        return len(content)
    if isinstance(content, list):
        return sum(len(block.get("text", "")) if isinstance(block, dict) else len(str(block)) for block in content)
    return 0


def read_transcript(path, agent=None):
    """The API requests, tool calls and tool results of one transcript file."""
    requests, seen, labels, results = [], set(), {}, []
    turns = compactions = 0
    started = None
    for entry in _lines(path):
        kind = entry.get("type")
        stamp = entry.get("timestamp")
        if stamp and not started:
            started = stamp
        if kind == "system" and entry.get("subtype") == "compact_boundary":
            compactions += 1
        message = entry.get("message") if isinstance(entry.get("message"), dict) else {}
        content = message.get("content")
        if kind == "assistant":
            for block in content if isinstance(content, list) else []:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    labels[block.get("id")] = _tool_label(block.get("name", "?"), block.get("input") or {})
            usage = _usage(entry)
            key = entry.get("requestId") or message.get("id") or entry.get("uuid")
            if usage and key not in seen:
                seen.add(key)
                usage.update(skill=entry.get("attributionSkill"), agent=agent or ("sidechain" if entry.get("isSidechain") else None),
                             model=message.get("model"), at=stamp)
                requests.append(usage)
        elif kind == "user" and not entry.get("isMeta"):
            blocks = content if isinstance(content, list) else []
            tool_results = [b for b in blocks if isinstance(b, dict) and b.get("type") == "tool_result"]
            for block in tool_results:
                results.append((labels.get(block.get("tool_use_id"), "?"), _text_size(block.get("content"))))
            if not tool_results and (isinstance(content, str) or any(
                    isinstance(b, dict) and b.get("type") == "text" for b in blocks)):
                turns += 1
    return {"requests": requests, "results": results, "turns": turns, "compactions": compactions,
            "started": started}


def read_session(path):
    """A session: its own transcript plus those of the agents it started."""
    main = read_transcript(path)
    session_id = os.path.basename(path)[:-len(".jsonl")]
    agents = []
    for sub in sorted(glob.glob(os.path.join(os.path.dirname(path), session_id, "subagents", "agent-*.jsonl"))):
        kind = "agent"
        try:
            with open(sub[:-len(".jsonl")] + ".meta.json", "r", encoding="utf-8") as fh:
                kind = json.load(fh).get("agentType") or kind
        except (OSError, ValueError):
            pass
        part = read_transcript(sub, agent=kind)
        agents.append(kind)
        main["requests"] += part["requests"]
        main["results"] += [("%s › %s" % (kind, label), size) for label, size in part["results"]]
    main.update(id=session_id, agents=agents)
    return main


def totals(requests):
    out = {"requests": len(requests), "input": 0, "cache_write": 0, "cache_read": 0, "output": 0, "weighted": 0.0}
    for r in requests:
        for key in ("input", "cache_write", "cache_read", "output"):
            out[key] += r[key]
        out["weighted"] += r["input"] + 1.25 * (r["cache_write"] - r["cache_write_1h"]) + 2 * r["cache_write_1h"] \
            + 0.1 * r["cache_read"]
    out["weighted"] = int(round(out["weighted"]))
    out["context"] = out["input"] + out["cache_write"] + out["cache_read"]
    return out


def summary(session):
    own = [r for r in session["requests"] if not r["agent"]]
    first = own[0] if own else None
    out = totals(session["requests"])
    out.update(id=session["id"], started=session["started"], turns=session["turns"],
               compactions=session["compactions"], agents=session["agents"],
               first_context=(first["input"] + first["cache_write"] + first["cache_read"]) if first else 0,
               max_context=max((r["input"] + r["cache_write"] + r["cache_read"] for r in own), default=0),
               models=sorted({r["model"] for r in session["requests"] if r["model"]}),
               largest_results=sorted(session["results"], key=lambda x: -x[1])[:8])
    return out


def by(sessions, field):
    groups = {}
    for session in sessions:
        for r in session["requests"]:
            name = r[field] or ("(main)" if field == "agent" else "(no skill)")
            groups.setdefault(name, []).append(r)
    return {name: totals(reqs) for name, reqs in sorted(groups.items())}


def k(n):
    return "%.1fk" % (n / 1000.0) if n >= 1000 else str(n)


def table(rows, head):
    widths = [max(len(str(x)) for x in col) for col in zip(head, *rows)] if rows else [len(h) for h in head]
    fmt = "  ".join("%%-%ds" % w if i == 0 else "%%%ds" % w for i, w in enumerate(widths))
    return "\n".join([fmt % tuple(head)] + [fmt % tuple(str(x) for x in row) for row in rows])


def load(paths, since=None, n=None):
    sessions = []
    for path in paths:
        session = read_session(path)
        if not session["requests"]:
            continue
        if since and (session["started"] or "") < since:
            continue
        sessions.append(session)
    sessions.sort(key=lambda s: s["started"] or "", reverse=True)
    return sessions[:n] if n else sessions


def main(argv=None):
    p = argparse.ArgumentParser(description="Token use of Claude Code sessions, from their transcripts.")
    p.add_argument("files", nargs="*", help="transcript files (default: every session of the checkout)")
    p.add_argument("--root", default=REPO, help="the checkout whose sessions to read (default: this one)")
    p.add_argument("--dir", help="the transcripts folder itself")
    p.add_argument("--since", help="only sessions started on or after this date (YYYY-MM-DD)")
    p.add_argument("--n", type=int, default=10, help="the most recent N sessions (0: all)")
    p.add_argument("--skills", action="store_true", help="per skill instead of per session")
    p.add_argument("--agents", action="store_true", help="per agent instead of per session")
    p.add_argument("--session", help="one session in detail (an id, or the first characters of one)")
    p.add_argument("--json", action="store_true", help="print JSON")
    a = p.parse_args(argv)

    folder = a.dir or transcripts_dir(a.root)
    paths = a.files or sorted(glob.glob(os.path.join(folder, "*.jsonl")))
    if a.session:
        paths = [x for x in paths if os.path.basename(x).startswith(a.session)]
    if not paths:
        sys.stderr.write("no transcripts found in %s\n" % folder)
        return 1
    sessions = load(paths, a.since, None if a.session else (a.n or None))
    report = {"sessions": [summary(s) for s in sessions], "skills": by(sessions, "skill"),
              "agents": by(sessions, "agent")}
    if a.json:
        print(json.dumps(report, indent=1, default=list))
        return 0
    if a.skills or a.agents:
        rows = [[name, t["requests"], k(t["context"]), k(t["cache_read"]), k(t["cache_write"]), k(t["output"]),
                 k(t["weighted"])] for name, t in report["skills" if a.skills else "agents"].items()]
        print(table(rows, ["skill" if a.skills else "agent", "requests", "context", "cache read", "cache write",
                           "output", "weighted in"]))
        return 0
    rows = []
    for s in report["sessions"]:
        day = (s["started"] or "")[:16].replace("T", " ")
        rows.append([s["id"][:8], day, s["turns"], s["requests"], len(s["agents"]), k(s["first_context"]),
                     k(s["max_context"]), k(s["context"]), k(s["output"]), k(s["weighted"])])
    print(table(rows, ["session", "started (UTC)", "turns", "requests", "agents", "first ctx", "max ctx",
                       "context", "output", "weighted in"]))
    if a.session:
        for s in report["sessions"]:
            print("\nmodels: %s · compactions: %d · agents: %s" % (", ".join(s["models"]) or "?", s["compactions"],
                                                                   ", ".join(s["agents"]) or "none"))
            print("largest tool results (characters):")
            for label, size in s["largest_results"]:
                print("  %8d  %s" % (size, label))
    return 0


if __name__ == "__main__":
    sys.exit(main())
