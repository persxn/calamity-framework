"""The learner store's layout, and the one move it has needed so far.

Until framework 1.1 the deep-coaching skills kept everything under learner/mastery/. The store now
gives each kind of thing its own folder:

    learner/coach/<topic>/      the deep-coaching narrative: curriculum, session log, glossary, reading
    learner/books/<topic>/      a study book (was learner/mastery/<topic>/book/)
    learner/projects/<slug>/    build-it-yourself and integration projects (was learner/mastery/projects/)

`layout migrate` shows the moves; with --write it makes them, with `git mv` for tracked files so the
history follows. A target that already exists is never overwritten: that move is reported and skipped.
"""
from __future__ import annotations

import os
import shutil
import subprocess

from .store import Repo
from .util import CalError

OLD = "mastery"


def _old(repo: Repo) -> str:
    return os.path.join(repo.learner, OLD)


def moves(repo: Repo) -> list:
    """[(from, to)] paths, both absolute, for everything still under learner/mastery/."""
    old = _old(repo)
    if not os.path.isdir(old):
        return []
    out = []
    for name in sorted(os.listdir(old)):
        src = os.path.join(old, name)
        if name.startswith("."):
            continue
        if name == "projects" and os.path.isdir(src):
            for slug in sorted(os.listdir(src)):
                out.append((os.path.join(src, slug), os.path.join(repo.learner, "projects", slug)))
            continue
        if not os.path.isdir(src):
            out.append((src, os.path.join(repo.learner, "coach", name)))
            continue
        for part in sorted(os.listdir(src)):
            here = os.path.join(src, part)
            if part == "book":
                out.append((here, os.path.join(repo.learner, "books", name)))
            else:
                out.append((here, os.path.join(repo.learner, "coach", name, part)))
    return out


def pending(repo: Repo) -> int:
    return len(moves(repo))


def _tracked(repo: Repo, path: str) -> bool:
    if not shutil.which("git") or not os.path.isdir(os.path.join(repo.root, ".git")) and \
            not os.path.isfile(os.path.join(repo.root, ".git")):
        return False
    proc = subprocess.run(["git", "ls-files", "--", os.path.relpath(path, repo.root)], cwd=repo.root,
                          stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    return proc.returncode == 0 and bool(proc.stdout.strip())


def _prune(path: str, stop: str) -> None:
    """Remove empty folders from `path` up to, but not including, `stop`."""
    while os.path.isdir(path) and os.path.normcase(path) != os.path.normcase(stop) and not os.listdir(path):
        os.rmdir(path)
        path = os.path.dirname(path)


def migrate(repo: Repo, write: bool = False) -> str:
    plan = moves(repo)
    if not plan:
        return "the learner store already has the current layout (nothing under learner/%s/)" % OLD
    lines = []
    done = skipped = 0
    for src, dst in plan:
        what = "%s -> %s" % (repo.rel(src), repo.rel(dst))
        if os.path.exists(dst):
            lines.append("skip  %s (the target exists: merge it by hand)" % what)
            skipped += 1
            continue
        if not write:
            lines.append("move  %s" % what)
            continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if _tracked(repo, src):
            proc = subprocess.run(["git", "mv", os.path.relpath(src, repo.root), os.path.relpath(dst, repo.root)],
                                  cwd=repo.root, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if proc.returncode != 0:
                raise CalError("git mv %s failed: %s" % (what, proc.stderr.decode("utf-8", "replace").strip()))
            # git moves only tracked files: carry along anything untracked that stayed behind
            if os.path.isdir(src):
                for root, _, files in os.walk(src, topdown=False):
                    for name in files:
                        rel = os.path.relpath(os.path.join(root, name), src)
                        target = os.path.join(dst, rel)
                        os.makedirs(os.path.dirname(target), exist_ok=True)
                        if not os.path.exists(target):
                            shutil.move(os.path.join(root, name), target)
                    _prune(root, os.path.dirname(src))
        else:
            shutil.move(src, dst)
        lines.append("moved %s" % what)
        done += 1
    if write and os.path.isdir(_old(repo)):
        for root, _, _ in os.walk(_old(repo), topdown=False):
            _prune(root, repo.learner)
        tail = "%d moved, %d skipped" % (done, skipped)
        if done:
            tail += "; commit the moves with your next sync"
    else:
        tail = "%d to move%s; run layout migrate --write to make the moves" % (
            len(plan) - skipped, (", %d skipped" % skipped) if skipped else "")
    return "\n".join(lines + [tail])
