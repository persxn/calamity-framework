"""Facts about a GATE year (dates, pattern), read from data files.

Nothing about a particular year is hard-coded in the engine. Shipped facts
live in framework/gate/<year>.md; a learner can override any key in
learner/gate/<year>.md, and the exam date of a single paper with the profile
key gate.exam_date.<PAPER>.
"""
from __future__ import annotations

import os
from datetime import date, datetime

from . import fm
from .store import Repo
from .util import CalError, csv_list


def year_data(repo: Repo, year=None) -> dict:
    year = year or repo.prof("gate.year")
    if not year:
        return {}
    cache = repo.memo.setdefault("gate years", {})   # read once per command: replay asks for it per answer
    if year not in cache:
        data = {}
        for base in (os.path.join(repo.framework, "gate"), os.path.join(repo.learner, "gate")):
            path = os.path.join(base, "%s.md" % year)
            raw = repo.read_bytes(path)
            if raw is not None:
                try:
                    meta, _ = fm.load(repo.rel(path), raw)
                except CalError as exc:
                    repo.note_file_problem("%s (its exam facts are ignored)" % exc)
                    continue
                data.update({k: v for k, v in meta.items() if v is not None})
        cache[year] = data
    return cache[year]


def papers(repo: Repo) -> list:
    return [str(p).upper() for p in csv_list(repo.prof("gate.papers"))]


def _to_date(value):
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def exam_date(repo: Repo, paper=None):
    """The exam date to plan against: the paper's own date if known, else the first exam day."""
    cache = repo.memo.setdefault("exam dates", {})   # worked out once per command, like year_data
    name = str(paper).upper() if paper else ""
    if name not in cache:
        own = _to_date(repo.prof("gate.exam_date.%s" % name)) if name else None
        if not own:
            days = [d for d in (_to_date(x) for x in csv_list(year_data(repo).get("exam_days"))) if d]
            own = min(days) if days else None
        cache[name] = own
    return cache[name]


def exam_datetime(repo: Repo, paper, like: datetime):
    """Exam date as a datetime in the same timezone as `like`."""
    d = exam_date(repo, paper)
    if d is None:
        return None
    return like.replace(year=d.year, month=d.month, day=d.day, hour=9, minute=0, second=0, microsecond=0)


def days_left(repo: Repo, paper, today: date):
    d = exam_date(repo, paper)
    return None if d is None else (d - today).days


def target_marks(repo: Repo, paper: str):
    value = repo.prof("gate.target_marks.%s" % paper.upper())
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
