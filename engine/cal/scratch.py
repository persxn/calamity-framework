"""The scratch folder, .calamity/tmp: where agents work out answers before the engine stores them.

The examiner works in .calamity/tmp/examiner/<batch>/ and the checker in .calamity/tmp/checker/<item>/.
Both may hold the computed answer to a sealed item, so the engine removes a batch once `item import`
has stored it and an item's folder once `item verify` (or `item reject`) has recorded it; `doctor`
warns about anything left for more than a day, and `clean tmp` removes everything. Other tools
(bridges, the curriculum architect) leave their JSON at the top of the folder.
"""
from __future__ import annotations

import os
import shutil
import time

STALE_HOURS = 24
AGENTS = ("examiner", "checker")  # agents with a folder of their own


def folder(repo) -> str:
    return os.path.join(repo.local, "tmp")


def agent_folder(repo, agent: str) -> str:
    return os.path.join(folder(repo), agent)


def _inside(path: str, area: str) -> bool:
    try:
        return os.path.commonpath([path, area]) == area
    except ValueError:  # another drive
        return False


def discard_import(repo, path: str | None, batch: bool = False) -> None:
    """After the engine stored a draft file: delete it when it is in scratch, and with `batch` (an import)
    the examiner's whole batch folder it sits in, so the computations behind the keys go with it."""
    if not path:
        return
    try:
        real = os.path.realpath(path)
        if not os.path.isfile(real) or not _inside(real, os.path.realpath(folder(repo))):
            return
        examiner = os.path.realpath(agent_folder(repo, "examiner"))
        if batch and _inside(real, examiner) and os.path.dirname(real) != examiner:
            batch = os.path.join(examiner, os.path.relpath(real, examiner).split(os.sep)[0])
            shutil.rmtree(batch, ignore_errors=True)
        else:
            os.remove(real)
    except (OSError, ValueError):
        pass


def discard_check(repo, item_id: str) -> None:
    """After the checker's result for an item is recorded: its working folder has served its purpose."""
    if not item_id or os.sep in item_id or (os.altsep and os.altsep in item_id) or item_id in (".", ".."):
        return
    shutil.rmtree(os.path.join(agent_folder(repo, "checker"), item_id), ignore_errors=True)


def _files(repo):
    """(relative path, modification time) of every file in the scratch folder."""
    top = folder(repo)
    for base, _, names in os.walk(top):
        for name in names:
            path = os.path.join(base, name)
            try:
                yield os.path.relpath(path, top).replace(os.sep, "/"), os.path.getmtime(path)
            except OSError:
                continue


def stale(repo, hours: float = STALE_HOURS) -> list:
    """Files left in the scratch folder for longer than `hours`, oldest first."""
    cutoff = time.time() - hours * 3600
    return [rel for rel, mtime in sorted(_files(repo), key=lambda f: f[1]) if mtime < cutoff]


def clean(repo, dry_run: bool = False) -> str:
    """Remove everything in the scratch folder: it is scratch, and it may hold worked answers."""
    top = folder(repo)
    entries = sorted(os.listdir(top)) if os.path.isdir(top) else []
    n_files = sum(1 for _ in _files(repo))
    if not entries:
        return "nothing to remove: .calamity/tmp is empty"
    if dry_run:
        return "would remove %d file(s) from .calamity/tmp:\n%s" % (
            n_files, "\n".join("  " + name + ("/" if os.path.isdir(os.path.join(top, name)) else "") for name in entries))
    left = []
    for name in entries:
        path = os.path.join(top, name)
        try:
            if os.path.isdir(path) and not os.path.islink(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        except OSError as exc:
            left.append("%s (%s)" % (name, exc.strerror or exc))
    line = "removed %d file(s) from .calamity/tmp" % n_files
    if left:
        line += "\ncould not remove: %s" % ", ".join(left)
    return line
