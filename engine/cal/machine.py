"""Per-machine setup and the health check.

`setup` prepares this machine: a machine id, the learner folders and, when
asked, the session-start hook in .claude/settings.local.json (a file that is
never committed) and a `calamity` alias in the shell's start-up file.
`doctor` reports what is and is not in order.
"""
from __future__ import annotations

import json
import os
import platform
import shlex
import shutil
import sys

from . import cf, notes, sources
from .store import Repo, read_text, write_text
from .util import CalError, fmt_delta, now, parse_ts


def _script(repo: Repo) -> str:
    return os.path.join(repo.root, "engine", "calamity.py")


def _machine_json(repo: Repo) -> dict:
    try:
        with open(os.path.join(repo.local, "machine.json"), "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def engine_cmd(repo: Repo) -> str:
    """How to call the engine on this machine, as typed from the repository root. Worked out once
    and kept in .calamity/machine.json, next to the machine id."""
    cmd = _machine_json(repo).get("cmd")
    if isinstance(cmd, str) and cmd:
        return cmd
    cmd = guess_cmd()
    try:
        ident = repo.machine()
        write_text(os.path.join(repo.local, "machine.json"), json.dumps({"id": ident, "cmd": cmd}) + "\n")
    except (OSError, CalError):
        pass  # not cached: worked out again next time
    return cmd


def _works(argv) -> bool:
    """Whether a Python command really runs here and is 3.9 or newer (a Microsoft Store alias with no
    Python behind it does not)."""
    import subprocess

    try:
        proc = subprocess.run(argv + ["-c", "import sys; print(sys.version_info >= (3, 9))"],
                              stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL,
                              timeout=15)
    except (OSError, subprocess.SubprocessError):
        return False
    return proc.returncode == 0 and proc.stdout.strip() == b"True"


def guess_cmd() -> str:
    if platform.system().lower().startswith("win"):
        for name, argv in (("python", ["python"]), ("py -3", ["py", "-3"])):
            if shutil.which(argv[0]) and _works(argv):
                return name + " engine/calamity.py"
        return "py -3 engine/calamity.py"   # neither answered: the launcher is the documented default
    return "python3 engine/calamity.py"


def _settings_path(repo: Repo) -> str:
    return os.path.join(repo.root, ".claude", "settings.local.json")


def _load_settings(path: str) -> dict:
    if not os.path.isfile(path):
        return {}
    try:
        data = json.loads(read_text(path) or "{}")
    except ValueError:
        raise CalError("%s is not valid JSON; fix or remove it, then run setup again" % path)
    if not isinstance(data, dict):
        raise CalError("%s should contain a JSON object" % path)
    return data


# Our two hooks: the brief at session start, and the key guard before every tool that reads (cal.guard).
HOOKS = {"SessionStart": (None, ["brief", "--hook"], 30),
         "PreToolUse": ("Read|Grep|Glob|Bash|PowerShell", ["guard", "tool"], 10)}


def _is_ours(entry, event: str = "SessionStart") -> bool:
    words = HOOKS[event][1][0]
    for hook in (entry or {}).get("hooks", []) if isinstance(entry, dict) else []:
        args = hook.get("args") or []
        blob = " ".join([str(hook.get("command", ""))] + [str(a) for a in args])
        if "calamity.py" in blob and words in blob:
            return True
    return False


def install_hook(repo: Repo) -> str:
    """Add (or refresh) the SessionStart hook that prints the brief and the PreToolUse key guard."""
    path = _settings_path(repo)
    data = _load_settings(path)
    hooks = data.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise CalError("'hooks' in %s is not an object" % path)
    for event, (matcher, args, timeout) in HOOKS.items():
        entries = [e for e in hooks.get(event, []) if not _is_ours(e, event)]
        entry = {"matcher": matcher} if matcher else {}
        entry["hooks"] = [{"type": "command", "command": sys.executable, "args": [_script(repo)] + args,
                           "timeout": timeout}]
        hooks[event] = entries + [entry]
    write_text(path, json.dumps(data, indent=2) + "\n")
    return ("session-start hook written to .claude/settings.local.json, with the key guard that keeps item keys "
            "out of searches and shell commands (both take effect in the next session)")


def remove_hook(repo: Repo) -> str:
    path = _settings_path(repo)
    data = _load_settings(path)
    hooks = data.get("hooks") if isinstance(data.get("hooks"), dict) else {}
    removed = False
    for event in HOOKS:
        before = hooks.get(event, [])
        after = [e for e in before if not _is_ours(e, event)]
        removed = removed or len(after) != len(before)
        if after:
            hooks[event] = after
        else:
            hooks.pop(event, None)
    if not removed:
        return "no Calamity hook was installed"
    if not hooks:
        data.pop("hooks", None)
    write_text(path, json.dumps(data, indent=2) + "\n")
    return "session-start hook removed, and the key guard with it"


def _short_path(path: str) -> str:
    """The 8.3 short form of a Windows path (no spaces), when the file system keeps one."""
    try:
        import ctypes

        buf = ctypes.create_unicode_buffer(1024)
        n = ctypes.windll.kernel32.GetShortPathNameW(path, buf, len(buf))
        if 0 < n < len(buf):
            return buf.value
    except (AttributeError, OSError, ValueError):
        pass
    return path


def install_statusline(repo: Repo) -> str:
    python, script = sys.executable, _script(repo)
    windows = platform.system().lower().startswith("win")
    if windows:
        python, script = (_short_path(p) if " " in p else p for p in (python, script))
    python, script = python.replace("\\", "/"), script.replace("\\", "/")
    if windows and (" " in python or " " in script):
        raise CalError("the status line cannot be set up automatically when the Python or repository path "
                       "contains spaces on Windows and the drive keeps no short (8.3) name for it")
    command = "%s %s statusline --stdin" % ((python, script) if windows else (shlex.quote(python), shlex.quote(script)))
    path = _settings_path(repo)
    data = _load_settings(path)
    data["statusLine"] = {"type": "command", "command": command}
    write_text(path, json.dumps(data, indent=2) + "\n")
    return "status line written to .claude/settings.local.json"


def _our_statusline(data: dict):
    """The status line entry if it is the one `setup --statusline` wrote, else None."""
    entry = data.get("statusLine")
    if isinstance(entry, dict):
        command = str(entry.get("command", ""))
        if "calamity.py" in command and command.rstrip().endswith(("statusline", "statusline --stdin")):
            return entry
    return None


def remove_statusline(repo: Repo) -> str:
    path = _settings_path(repo)
    data = _load_settings(path)
    if _our_statusline(data) is None:
        return "no Calamity status line was installed"
    data.pop("statusLine", None)
    write_text(path, json.dumps(data, indent=2) + "\n")
    return "status line removed"


def statusline_state(repo: Repo) -> str:
    """'ok', 'missing', 'other' (someone else's status line) or what is wrong with ours."""
    try:
        data = _load_settings(_settings_path(repo))
    except CalError:
        return "settings.local.json is not valid JSON"
    entry = _our_statusline(data)
    if entry is None:
        return "other" if data.get("statusLine") else "missing"
    command = str(entry.get("command", ""))
    try:
        parts = shlex.split(command) if not platform.system().lower().startswith("win") else command.split(" ")
    except ValueError:
        return "status line command cannot be read"
    if len(parts) < 3 or not os.path.isfile(parts[0]):
        return "status line points at a Python that no longer exists"
    try:
        if not os.path.samefile(parts[1], _script(repo)):
            return "status line points at a different copy of the repository"
    except OSError:
        return "status line points at a repository path that no longer exists"
    return "ok"


def hook_state(repo: Repo, event: str = "SessionStart") -> str:
    """'ok', 'missing' or a description of what is wrong (the brief's hook, or with PreToolUse the key guard)."""
    path = _settings_path(repo)
    try:
        data = _load_settings(path)
    except CalError:
        return "settings.local.json is not valid JSON"
    entries = (data.get("hooks") or {}).get(event, []) if isinstance(data.get("hooks"), dict) else []
    for entry in entries:
        if not _is_ours(entry, event):
            continue
        hook = entry["hooks"][0]
        if not os.path.isfile(str(hook.get("command", ""))):
            return "hook points at a Python that no longer exists (%s)" % hook.get("command")
        args = hook.get("args") or []
        if not args or not os.path.isfile(str(args[0])):
            return "hook points at a repository path that no longer exists"
        try:
            if not os.path.samefile(args[0], _script(repo)):
                return "hook points at a different copy of the repository"
        except OSError:
            return "hook path could not be checked"
        return "ok"
    return "missing"


# ---------------------------------------------------------------- shell alias

ALIAS_START = "# >>> calamity alias >>>"
ALIAS_END = "# <<< calamity alias <<<"


def rc_file() -> str | None:
    """The start-up file of the learner's shell that the alias belongs in, or None where there is no
    such file to write (Windows, or a shell other than bash or zsh)."""
    if platform.system().lower().startswith("win"):
        return None
    shell = os.path.basename(os.environ.get("SHELL", ""))
    home = os.path.expanduser("~")
    if shell == "zsh":
        return os.path.join(os.environ.get("ZDOTDIR") or home, ".zshrc")
    if shell == "bash":  # a macOS terminal opens a login shell, which reads .bash_profile instead
        return os.path.join(home, ".bash_profile" if platform.system() == "Darwin" else ".bashrc")
    return None


def _shown(path: str) -> str:
    home = os.path.expanduser("~")
    return "~" + path[len(home):] if path.startswith(home + os.sep) else path


def alias_line(repo: Repo) -> str:
    """`calamity` in a terminal: go to this repository and open Claude Code there without permission prompts."""
    return "alias calamity=%s" % shlex.quote("cd -- %s && claude --dangerously-skip-permissions" % shlex.quote(repo.root))


def _without_alias(text: str):
    """The text with our block taken out, and the block's lines (None when there was none)."""
    lines = text.splitlines(True)
    try:
        start = next(i for i, line in enumerate(lines) if line.rstrip("\r\n") == ALIAS_START)
        end = next(i for i in range(start, len(lines)) if lines[i].rstrip("\r\n") == ALIAS_END)
    except StopIteration:
        return text, None
    return "".join(lines[:start] + lines[end + 1:]), [line.rstrip("\r\n") for line in lines[start + 1:end]]


def _write_rc(path: str, text: str) -> None:
    """Write a shell start-up file in place of the old one: through a symbolic link (dotfile managers
    keep them), keeping its permissions."""
    real = os.path.realpath(path)
    try:
        mode = os.stat(real).st_mode & 0o7777
    except OSError:
        mode = 0o644
    write_text(real, text)
    os.chmod(real, mode)


def install_alias(repo: Repo) -> str:
    rc = rc_file()
    if rc is None:
        raise CalError("the alias is written for bash and zsh on Linux and macOS only; this shell is %s"
                       % (os.path.basename(os.environ.get("SHELL", "")) or "unknown"))
    text, _ = _without_alias(read_text(rc) if os.path.isfile(rc) else "")
    if text and not text.endswith("\n"):
        text += "\n"
    _write_rc(rc, text + "%s\n%s\n%s\n" % (ALIAS_START, alias_line(repo), ALIAS_END))
    return ("alias written to %s: `calamity` opens Claude Code in this folder with permission prompts off "
            "(takes effect in a new terminal)" % _shown(rc))


def remove_alias(repo: Repo) -> str:
    rc = rc_file()
    if rc is None or not os.path.isfile(rc):
        return "no Calamity alias was installed"
    text, block = _without_alias(read_text(rc))
    if block is None:
        return "no Calamity alias was installed"
    _write_rc(rc, text)
    return "alias removed from %s (open a new terminal, or run: unalias calamity)" % _shown(rc)


def alias_state(repo: Repo) -> str:
    """'ok', 'missing', 'unsupported' (no bash or zsh) or what is wrong with ours."""
    rc = rc_file()
    if rc is None:
        return "unsupported"
    try:
        _, block = _without_alias(read_text(rc) if os.path.isfile(rc) else "")
    except (OSError, UnicodeDecodeError):
        return "%s cannot be read" % _shown(rc)
    if block is None:
        return "missing"
    return "ok" if block == [alias_line(repo)] else "alias points at a different copy of the repository"


def setup(repo: Repo, machine: str | None = None, hook: bool = False, statusline: bool = False,
          alias: bool = False) -> str:
    repo.ensure_dirs()
    ident = repo.set_machine(machine) if machine else repo.machine()
    cmd = guess_cmd()
    write_text(os.path.join(repo.local, "machine.json"), json.dumps({"id": ident, "cmd": cmd}) + "\n")
    lines = ["machine: %s" % ident, "engine command on this machine: %s" % cmd,
             "python: %s (%s)" % (sys.executable, platform.python_version())]
    if hook:
        lines.append(install_hook(repo))
    else:
        for event, label in (("SessionStart", "session-start hook"), ("PreToolUse", "key guard")):
            state = hook_state(repo, event)
            lines.append("%s: %s%s" % (label, state, "" if state == "ok" else " (install with: setup --hook)"))
    if statusline:
        try:
            lines.append(install_statusline(repo))
        except CalError as exc:  # the hook above is written either way: say so before the refusal
            lines.append("status line NOT written: %s" % exc)
    if alias:
        try:
            lines.append(install_alias(repo))
        except CalError as exc:
            lines.append("alias NOT written: %s" % exc)
    lines.append("learner folders ready under learner/")
    return "\n".join(lines)


# ---------------------------------------------------------------- doctor


def doctor(repo: Repo):
    """Return (exit_code, text). Exit code 1 when something must be fixed."""
    from .state import State
    from .tree import Tree

    rows = []

    def add(level, what, detail=""):
        rows.append((level, what, detail))

    v = sys.version_info
    add("OK" if v >= (3, 9) else "FAIL", "Python %d.%d.%d" % (v[0], v[1], v[2]), "" if v >= (3, 9) else "3.9 or newer is required")
    add("OK" if shutil.which("git") else "WARN", "git", "" if shutil.which("git") else "not found on PATH; syncing between machines needs it")
    for rel in ("config.md", "method.md", os.path.join("tree", "tracks.md")):
        ok = os.path.isfile(os.path.join(repo.framework, rel))
        add("OK" if ok else "FAIL", "framework/%s" % rel.replace(os.sep, "/"), "" if ok else "missing")

    tree = Tree(repo)
    errors, warnings = tree.check()
    live = tree.live()
    add("FAIL" if errors else "OK", "skill tree: %d skills, %d topics" % (len(live), sum(len(n.topics) for n in live)),
        "; ".join(errors[:3]) + (" ..." if len(errors) > 3 else ""))
    if warnings:
        add("WARN", "skill tree warnings: %d" % len(warnings), warnings[0])

    state = State(repo, tree)
    add("OK" if repo.onboarded() else "WARN", "learner profile",
        "" if repo.onboarded() else "not onboarded yet (run the onboard skill)")
    repo.config()
    if repo.config_errors:
        add("WARN", "configuration overrides: %d ignored" % len(repo.config_errors),
            repo.config_errors[0] + "; fix it with profile set cfg.<key> <value> or profile unset cfg.<key>")
    for problem in repo.file_problems:
        add("WARN", "learner file not readable as it is", problem)
    files = repo.event_files()
    add("FAIL" if repo.event_errors else "OK", "event log: %d events in %d file(s)" % (state.n_events, len(files)),
        "; ".join(repo.event_errors[:3]))
    # The replay snapshot is a shortcut and must never change an answer: compare it with a full replay.
    from . import snapshot

    if state.cache_info.startswith("snapshot"):
        try:
            same = state.fingerprint() == State(repo, tree, use_cache=False).fingerprint()
        except snapshot.Uncacheable:
            same = True
        if same:
            add("OK", "replay snapshot", "agrees with a full replay of the log")
        else:
            snapshot.discard(repo)
            add("WARN", "replay snapshot", "disagreed with a full replay and was deleted; please report this")

    on_disk = set()
    if os.path.isdir(repo.items_dir):
        for skill in os.listdir(repo.items_dir):
            d = os.path.join(repo.items_dir, skill)
            if os.path.isdir(d):
                on_disk.update(n[:-5] for n in os.listdir(d) if n.endswith(".json"))
    known = set(state.items)
    missing, orphans = known - on_disk, on_disk - known
    counts = {}
    for it in state.items.values():
        counts[it.status] = counts.get(it.status, 0) + 1
    add("WARN" if (missing or orphans) else "OK",
        "items: %s" % (", ".join("%d %s" % (c, s) for s, c in sorted(counts.items())) or "none"),
        ("%d logged item(s) have no file" % len(missing) if missing else "")
        + ("; %d item file(s) were never logged (not created by the engine)" % len(orphans) if orphans else ""))

    src_errors, src_warnings = sources.check(repo, tree)
    n_sources = len(sources.load_all(repo))
    add("FAIL" if src_errors else "OK", "study sources: %d" % n_sources, "; ".join(src_errors[:3]))
    if src_warnings:
        add("WARN", "study source warnings", src_warnings[0])

    add("OK", "machine id: %s" % repo.machine())
    state_h = hook_state(repo)
    add("OK" if state_h == "ok" else "WARN", "session-start hook",
        "" if state_h == "ok" else "%s; the brief still works when run by hand (setup --hook installs it)" % state_h)
    from . import guard, scratch

    state_g = hook_state(repo, "PreToolUse")
    if state_g == "ok" and not guard.works(repo.root):
        state_g = "installed, but it does not refuse what it should; please report this"
    add("OK" if state_g == "ok" else "WARN", "key guard",
        "" if state_g == "ok" else "%s; it keeps item keys out of searches and shell commands (setup --hook "
                                   "installs it)" % state_g)
    old = scratch.stale(repo)
    add("WARN" if old else "OK", "scratch folder (.calamity/tmp)",
        ("%d file(s) older than a day, which may hold worked answers; remove them with: clean tmp" % len(old))
        if old else "nothing left over")
    state_s = statusline_state(repo)
    if state_s == "ok":
        add("OK", "status line", "installed")
    elif state_s in ("missing", "other"):
        add("OK", "status line", "not installed (optional: setup --statusline)" if state_s == "missing"
            else "another status line is configured")
    else:
        add("WARN", "status line", "%s (setup --statusline writes it again, setup --remove-statusline removes it)" % state_s)
    state_a = alias_state(repo)
    if state_a in ("ok", "missing", "unsupported"):
        add("OK", "shell alias", {"ok": "installed (%s)" % _shown(rc_file() or ""),
                                  "missing": "not installed (optional: setup --alias)",
                                  "unsupported": "not available for this shell"}[state_a])
    else:
        add("WARN", "shell alias", "%s (setup --alias writes it again, setup --remove-alias removes it)" % state_a)

    attrs = os.path.join(repo.root, ".gitattributes")
    has_union = os.path.isfile(attrs) and "merge=union" in read_text(attrs)
    add("OK" if has_union else "WARN", ".gitattributes union merge for the event log",
        "" if has_union else "missing: two machines could then conflict on the same file")
    ignore = os.path.join(repo.root, ".gitignore")
    ignored = os.path.isfile(ignore) and ".calamity" in read_text(ignore)
    add("OK" if ignored else "WARN", ".gitignore covers .calamity/", "" if ignored else "machine-local files could be committed")

    engine = notes.tex_engine()
    add("OK" if engine else "WARN", "TeX engine for PDF notes",
        engine[0] if engine else "none found; notes stay as .tex until one is installed")

    handle = repo.prof("cp.handle")
    if handle:
        data = cf.load(repo)
        if data is None:
            add("WARN", "Codeforces %s" % handle, "not synced on this machine (cf sync)")
        else:
            add("OK", "Codeforces %s" % handle, "synced %s" % fmt_delta(parse_ts(data["fetched"]) - now()))

    width = max(len(r[1]) for r in rows)
    lines = [("%-4s  %s%s" % (level, what.ljust(width), ("  " + detail) if detail else "")).rstrip()
             for level, what, detail in rows]
    fails = sum(1 for r in rows if r[0] == "FAIL")
    warns = sum(1 for r in rows if r[0] == "WARN")
    lines.append("")
    lines.append("%d problem(s), %d warning(s)" % (fails, warns))
    return (1 if fails else 0), "\n".join(lines)
