"""Per-machine setup and the health check.

`setup` prepares this machine: a machine id, the learner folders and, when
asked, the session-start hook in .claude/settings.local.json (a file that is
never committed), the `calamity` shell function in the shell's start-up file
(no arguments: open Claude Code here with permission prompts off; arguments:
the engine), the `calamity` command in ~/.local/bin, and the permission rules
in a plugin learner's .claude/settings.json. `doctor` reports what is and is
not in order.

Plugin mode (the framework installed as a Claude Code plugin, the learner's
repository elsewhere): bin/calamity is on the shell's PATH, hooks/hooks.json
runs the hooks, and the session-start hook exports CALAMITY_ROOT for the rest
of the session through CLAUDE_ENV_FILE.
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


def framework_root() -> str:
    """The folder this engine came from: the clone, or the plugin's installed copy."""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def plugin_mode() -> bool:
    """Whether this engine runs as the Claude Code plugin (its hooks set CLAUDE_PLUGIN_ROOT to our folder)."""
    root = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if not root:
        return False
    try:
        return os.path.samefile(root, framework_root())
    except OSError:
        return False


def link_framework(repo: Repo) -> str:
    """Plugin mode: a link `framework` in the learner's repository to the plugin's framework/, so the skills' and
    rules' relative paths (framework/method.md, framework/rules/...) resolve there too. Re-pointed when the plugin
    moves (an update installs it under a new version); a real framework/ folder is never touched. Git-ignored."""
    if not separate_engine(repo):
        return "framework: this clone's own"
    target = os.path.join(framework_root(), "framework")
    link = os.path.join(repo.root, "framework")
    try:
        if os.path.islink(link):
            if os.path.realpath(link) == os.path.realpath(target):
                return "framework: linked"
            os.remove(link)
        elif os.path.exists(link):
            return "framework: a framework/ folder of this repository's own is kept"
        try:
            os.symlink(target, link, target_is_directory=True)
        except (OSError, NotImplementedError):
            if not platform.system().lower().startswith("win"):
                raise
            import subprocess                      # Windows without the right to make symbolic links: a junction

            subprocess.run(["cmd", "/c", "mklink", "/J", link, target], check=True, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
        ignore = os.path.join(repo.root, ".gitignore")
        text = read_text(ignore) if os.path.isfile(ignore) else ""
        if "/framework\n" not in text:
            write_text(ignore, text + ("" if not text or text.endswith("\n") else "\n") +
                       "# the Calamity plugin's framework, linked by the engine (never committed)\n/framework\n")
        return "framework: linked to the plugin's (%s)" % target
    except Exception as exc:                       # never break a session over the link
        return "framework: NOT linked (%s); the skills cannot read framework/ files here" % exc


def export_root(repo: Repo) -> bool:
    """In plugin mode at session start, keep CALAMITY_ROOT for the session's shell (Claude Code sources the
    file CLAUDE_ENV_FILE names before each command), so `calamity` finds this learner from any folder."""
    if separate_engine(repo):
        link_framework(repo)
    path = os.environ.get("CLAUDE_ENV_FILE")
    if not path or not plugin_mode():
        return False
    line = "export CALAMITY_ROOT=%s\n" % shlex.quote(repo.root)
    try:
        old = read_text(path) if os.path.isfile(path) else ""
        if line not in old:
            write_text(path, old + ("" if not old or old.endswith("\n") else "\n") + line)
        return True
    except (OSError, CalError):
        return False


def _machine_json(repo: Repo) -> dict:
    try:
        with open(os.path.join(repo.local, "machine.json"), "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def engine_cmd(repo: Repo) -> str:
    """How to call the engine on this machine. `calamity` when the plugin's shim or `setup --shim` put it on the
    PATH; otherwise the form typed from the repository root, worked out once and kept in .calamity/machine.json,
    next to the machine id."""
    if plugin_mode() or shutil.which("calamity"):
        return "calamity"
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


# Our hooks (cal.hooks): the brief at session start, the key guard before every tool that reads (cal.guard),
# and the study hooks around each turn. The output style (.claude/output-styles/calamity-tutor.md) comes with
# them: it is how a study session teaches.
STYLE = "Calamity Tutor"
HOOKS = {"SessionStart": (None, ["brief", "--hook"], 30),
         "PreToolUse": ("Read|Grep|Glob|Bash|PowerShell", ["guard", "tool"], 10),
         "UserPromptSubmit": (None, ["guard", "prompt"], 10),
         "Stop": (None, ["guard", "stop"], 20),
         "PreCompact": (None, ["snapshot", "--session"], 20),
         "SessionEnd": (None, ["guard", "end"], 5)}
STUDY_HOOKS = ("UserPromptSubmit", "Stop", "PreCompact", "SessionEnd")


def _is_ours(entry, event: str = "SessionStart") -> bool:
    words = HOOKS[event][1][0]
    for hook in (entry or {}).get("hooks", []) if isinstance(entry, dict) else []:
        args = hook.get("args") or []
        blob = " ".join([str(hook.get("command", ""))] + [str(a) for a in args])
        if "calamity.py" in blob and words in blob:
            return True
    return False


def separate_engine(repo: Repo) -> bool:
    """Whether the engine lives outside the learner's repository (the plugin), so hooks come from hooks/hooks.json."""
    try:
        return not os.path.samefile(framework_root(), repo.root)
    except OSError:
        return True


def install_hook(repo: Repo) -> str:
    """Add (or refresh) the SessionStart hook that prints the brief and the PreToolUse key guard."""
    if plugin_mode():
        return ("hooks: the plugin runs them (its hooks/hooks.json: the brief, the key guard and the study hooks); "
                "nothing written to .claude/settings.local.json")
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
    style = data.get("outputStyle")
    if style in (None, "", "default", STYLE):
        data["outputStyle"] = STYLE
        style_line = "the %s output style" % STYLE
    else:
        style_line = "your own output style (%s) kept; /output-style %s switches to the tutor's" % (style, STYLE)
    write_text(path, json.dumps(data, indent=2) + "\n")
    return ("session-start hook written to .claude/settings.local.json, with the key guard that keeps item keys "
            "out of searches and shell commands, the study hooks (routing and !feedback, the Stop guard, compaction, "
            "session end; CALAMITY_HOOKS=off turns them off) and %s (all take effect in the next session)" % style_line)


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
    if data.get("outputStyle") == STYLE:
        data.pop("outputStyle")
        removed = True
    if not removed:
        return "no Calamity hook was installed"
    if not hooks:
        data.pop("hooks", None)
    write_text(path, json.dumps(data, indent=2) + "\n")
    return "session-start hook removed, and the key guard, the study hooks and the tutor's output style with it"


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


def study_hooks_state(repo: Repo) -> str:
    """'ok', or which of the study hooks are missing or wrong."""
    bad = [(event, hook_state(repo, event)) for event in STUDY_HOOKS]
    bad = [(e, s) for e, s in bad if s != "ok"]
    if not bad:
        return "ok"
    if all(s == "missing" for _, s in bad):
        return "missing" if len(bad) == len(STUDY_HOOKS) else "missing: %s" % ", ".join(e for e, _ in bad)
    return "; ".join("%s %s" % (e, s) for e, s in bad)


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
    """`calamity` in a terminal (D5): with no arguments, go to this repository and open Claude Code there without
    permission prompts; with arguments, run the engine for this repository (`calamity today`). A function, not an
    alias, so it does both, and Claude Code's shell, which keeps the learner's functions, reaches the engine by
    the same name the skills use."""
    root = shlex.quote(repo.root)
    return ("calamity() { if [ \"$#\" -eq 0 ]; then cd -- %s && claude --dangerously-skip-permissions; "
            "else ( [ -n \"${CALAMITY_ROOT:-}\" ] || CALAMITY_ROOT=%s; export CALAMITY_ROOT; exec %s \"$@\" ); fi; }"
            % (root, root, shlex.quote(os.path.join(framework_root(), "bin", "calamity"))))


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
    # the old block was an alias of the same name; unalias it first or the function cannot be defined
    _write_rc(rc, text + "%s\n%s\n%s\n%s\n" % (ALIAS_START, "unalias calamity 2>/dev/null || true",
                                                 alias_line(repo), ALIAS_END))
    return ("`calamity` written to %s: on its own it opens Claude Code in this folder with permission prompts off; "
            "`calamity <command>` runs the engine (takes effect in a new terminal)" % _shown(rc))


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
    if block == ["unalias calamity 2>/dev/null || true", alias_line(repo)]:
        return "ok"
    if len(block) == 1 and block[0].startswith("alias calamity="):
        return "the old alias: setup --alias writes the function that also runs the engine"
    return "alias points at a different copy of the repository"


# ---------------------------------------------------------------- the calamity command, permissions


def shim_path() -> str:
    name = "calamity.cmd" if platform.system().lower().startswith("win") else "calamity"
    return os.path.join(os.path.expanduser("~"), ".local", "bin", name)


def _shim_text(repo: Repo) -> str:
    target = os.path.join(framework_root(), "bin", "calamity")
    if platform.system().lower().startswith("win"):
        return '@echo off\r\nif not defined CALAMITY_ROOT set "CALAMITY_ROOT=%s"\r\n"%s.cmd" %%*\r\n' % (repo.root, target)
    return ("#!/bin/sh\n# Written by calamity setup --shim: the engine for %s from any folder.\n"
            "[ -n \"${CALAMITY_ROOT:-}\" ] || CALAMITY_ROOT=%s\nexport CALAMITY_ROOT\nexec %s \"$@\"\n"
            % (repo.root, shlex.quote(repo.root), shlex.quote(target)))


def install_shim(repo: Repo) -> str:
    """`calamity` on the PATH outside the plugin: a small script in ~/.local/bin (never sudo) that runs this
    repository's engine, for headless runs (stock, reminders) and shells without the function."""
    path = shim_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    write_text(path, _shim_text(repo))
    if not path.endswith(".cmd"):
        os.chmod(path, 0o755)
    on_path = os.path.dirname(path) in os.environ.get("PATH", "").split(os.pathsep)
    return "`calamity` written to %s%s" % (_shown(path), "" if on_path else
                                           " (that folder is not on PATH: add it in your shell's start-up file)")


def remove_shim(repo: Repo) -> str:
    path = shim_path()
    if os.path.isfile(path) and (path.endswith(".cmd") or "calamity setup --shim" in read_text(path)):
        os.remove(path)
        return "removed %s" % _shown(path)
    return "no calamity command written by setup was found"


def shim_state(repo: Repo) -> str:
    if plugin_mode():
        return "ok (the plugin's bin/calamity)"
    path = shim_path()
    if os.path.isfile(path):
        return "ok" if os.path.abspath(repo.root) in read_text(path) else "points at a different copy of the repository"
    return "ok (on PATH)" if shutil.which("calamity") else "missing"


def install_permissions(repo: Repo) -> str:
    """Copy the framework's permission rules into the learner's .claude/settings.json (a plugin cannot ship
    permissions). In a clone the rules are already the repository's own."""
    source = os.path.join(framework_root(), ".claude", "settings.json")
    target = os.path.join(repo.root, ".claude", "settings.json")
    if os.path.abspath(source) == os.path.abspath(target):
        return "permissions: this clone's .claude/settings.json already holds them"
    linked = link_framework(repo)
    rules = (_load_settings(source).get("permissions") or {})
    data = _load_settings(target)
    perms = data.setdefault("permissions", {})
    added = 0
    for kind in ("allow", "ask", "deny"):
        have = perms.setdefault(kind, [])
        for rule in rules.get(kind, []):
            if rule not in have:
                have.append(rule)
                added += 1
    write_text(target, json.dumps(data, indent=2) + "\n")
    return "permissions: %d rule(s) added to %s (allow, ask, deny)\n%s" % (added, repo.rel(target), linked)


def setup(repo: Repo, machine: str | None = None, hook: bool = False, statusline: bool = False,
          alias: bool = False, shim: bool = False, permissions: bool = False) -> str:
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
        study = study_hooks_state(repo)
        lines.append("study hooks: %s%s" % (study, "" if study == "ok" else " (install with: setup --hook)"))
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
    if shim:
        lines.append(install_shim(repo))
    if permissions:
        lines.append(install_permissions(repo))
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
    from . import layout

    n_old = layout.pending(repo)
    add("WARN" if n_old else "OK", "learner store layout",
        ("%d thing(s) still under learner/mastery/: layout migrate shows the moves, --write makes them" % n_old)
        if n_old else "")
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
    from . import hooks

    state_st = study_hooks_state(repo)
    if hooks.off():
        add("OK", "study hooks", "turned off for this shell (CALAMITY_HOOKS=off or CALAMITY_MAINTAIN=1)")
    else:
        add("OK" if state_st == "ok" else "WARN", "study hooks",
            "routing and !feedback, the Stop guard, compaction, session end" if state_st == "ok" else
            "%s; setup --hook installs them (CALAMITY_HOOKS=off turns them off)" % state_st)
    style_file = os.path.join(repo.root, ".claude", "output-styles", "calamity-tutor.md")
    try:
        style = _load_settings(_settings_path(repo)).get("outputStyle")
    except CalError:
        style = None
    if not os.path.isfile(style_file):
        add("WARN", "output style", "%s is missing; study sessions teach without it" % repo.rel(style_file))
    elif style == STYLE:
        add("OK", "output style", STYLE)
    elif style and style != "default":
        add("OK", "output style", "%s, chosen here (the tutor's is %s: /output-style %s)" % (style, STYLE, STYLE))
    else:
        add("WARN", "output style", "not set: study sessions run without the tutor's style (setup --hook selects "
                                    "%s)" % STYLE)
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
    state_s = shim_state(repo)
    if state_s.startswith("ok"):
        add("OK", "calamity command", state_s)
    else:
        add("WARN", "calamity command", "%s: skills call `calamity <command>`; setup --shim writes it to ~/.local/bin "
                                        "(until then they use the engine command the brief names)" % state_s)

    from . import coach

    dupes = coach.duplicates()
    if dupes:
        add("WARN", "account-level mastery-coach", "%s competes with this framework's engine-backed one for the same "
            "requests; turn it off where it comes from (claude.ai Settings > Capabilities > Skills, or remove the "
            "folder)" % _shown(dupes[0]))
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
