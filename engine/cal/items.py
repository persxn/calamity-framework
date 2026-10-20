"""Practice items: creation, sealing, blind display, grading and selection.

An item file is written once (learner/items/<skill>/<id>.json) and never
edited; whether it is a draft, verified, rejected or disputed is decided by
events. The answer key and solution are stored base64-"sealed" so that
nobody (the learner browsing files, or an agent grepping the repo) reads
them by accident. That is spoiler protection, not security.

The engine grades mcq / msq / nat / short answers itself. Hands-on types
(code, task, open) are judged by whoever ran the check, and recorded.
"""
from __future__ import annotations

import base64
import json
import os
import re
from fractions import Fraction

from .store import Repo, write_text
from .util import CalError, csv_list, iso, now, short_id

TYPES = ("mcq", "msq", "nat", "short", "code", "task", "open")
AUTO_TYPES = ("mcq", "msq", "nat", "short")
SOURCE_KINDS = ("generated", "official", "imported", "manual")
DEFAULT_EXPECT = {"mcq": 90, "msq": 120, "nat": 150, "short": 60, "code": 900, "task": 900, "open": 300}

_LETTER_RE = re.compile(r"^\W*(?:option\s*)?([A-Za-z])\W*$", re.I)
_NUM_RE = re.compile(r"^\s*=?\s*([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)\s*$")
_FRAC_RE = re.compile(r"^\s*=?\s*([+-]?\d+)\s*/\s*(\d+)\s*$")


# ---------------------------------------------------------------- sealing


def seal(data: dict) -> str:
    raw = json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return base64.b64encode(raw).decode("ascii")


def unseal(item: dict) -> dict:
    try:
        return json.loads(base64.b64decode(item.get("sealed", "")).decode("utf-8"))
    except (ValueError, TypeError):
        raise CalError("item %s has an unreadable key" % item.get("id"))


# ---------------------------------------------------------------- answers


def parse_number(text) -> float:
    s = str(text).strip().replace(",", "") if not isinstance(text, (int, float)) else text
    if isinstance(s, (int, float)) and not isinstance(s, bool):
        return float(s)
    m = _NUM_RE.match(s)
    if m:
        return float(m.group(1))
    m = _FRAC_RE.match(s)
    if m and int(m.group(2)) != 0:
        return float(Fraction(int(m.group(1)), int(m.group(2))))
    raise CalError("expected a number (like 0.42, 17 or 3/8), got %r" % (text,))


def parse_letters(text, options, single: bool):
    """Turn 'b', '(B)', 'A, C', 'ACD' into option labels that exist in the item."""
    labels = [str(k).upper() for k in options]
    raw = text if isinstance(text, (list, tuple)) else [str(text)]
    tokens = []
    for part in raw:
        part = str(part).strip()
        compact = part.replace(" ", "").upper()
        if not single and len(compact) > 1 and compact.isalpha() and all(ch in labels for ch in compact):
            tokens.extend(compact)
            continue
        for piece in re.split(r"[,;/&+]|\band\b", part, flags=re.I):
            piece = piece.strip()
            if piece:
                tokens.append(piece)
    out = []
    for tok in tokens:
        m = _LETTER_RE.match(tok)
        if not m:
            raise CalError("could not read %r as an option letter (%s)" % (tok, "/".join(labels)))
        letter = m.group(1).upper()
        if letter not in labels:
            raise CalError("option %s does not exist (options: %s)" % (letter, ", ".join(labels)))
        if letter not in out:
            out.append(letter)
    if not out:
        raise CalError("no answer given")
    if single:
        if len(out) != 1:
            raise CalError("this question takes exactly one option")
        return out[0]
    return sorted(out)


def norm_text(text) -> str:
    s = " ".join(str(text).strip().split()).casefold()
    return s.strip("`'\" ").rstrip(".").strip()


def _nat_key(answer) -> dict:
    """Normalise a numeric key to {'min': a, 'max': b}."""
    if isinstance(answer, dict):
        if "min" in answer and "max" in answer:
            lo, hi = parse_number(answer["min"]), parse_number(answer["max"])
            if lo > hi:
                raise CalError("numeric key has min > max")
            return {"min": lo, "max": hi}
        if "value" in answer:
            value = parse_number(answer["value"])
            tol = abs(parse_number(answer.get("tol", 0)))
            return {"min": value - tol, "max": value + tol}
        raise CalError("numeric key must be a number, {value, tol} or {min, max}")
    if isinstance(answer, bool):
        raise CalError("numeric key must be a number")
    if isinstance(answer, int):
        return {"min": float(answer), "max": float(answer)}
    value = parse_number(answer)
    text = repr(float(value)) if isinstance(answer, float) else str(answer).strip()
    if "e" in text.lower():  # exponent form: no decimal places to go by, use 0.5% either way
        tol = 0.005 * abs(value)
        return {"min": value - tol, "max": value + tol}
    decimals = len(text.split(".", 1)[1]) if "." in text else 0
    if float(value).is_integer() and (decimals == 0 or text.endswith(".0")):
        return {"min": value, "max": value}
    tol = max(0.5 * 10 ** (-decimals), 0.005 * abs(value))
    return {"min": value - tol, "max": value + tol}


def _short_key(answer) -> dict:
    if isinstance(answer, dict):
        accept = [norm_text(a) for a in csv_list(answer.get("accept"))]
        regex = answer.get("regex") or None
    else:
        accept = [norm_text(a) for a in (answer if isinstance(answer, (list, tuple)) else [answer])]
        regex = None
    accept = [a for a in accept if a]
    if regex:
        try:
            re.compile(regex)
        except re.error as exc:
            raise CalError("bad regex in short-answer key: %s" % exc)
    if not accept and not regex:
        raise CalError("short-answer key needs at least one accepted answer")
    return {"accept": accept, "regex": regex}


def grade(item: dict, raw) -> tuple:
    """Grade a raw answer against the sealed key. Returns (ok, normalised_answer)."""
    kind = item["type"]
    if kind not in AUTO_TYPES:
        raise CalError("%s items are judged by running their check, not graded by the engine" % kind)
    key = unseal(item)["answer"]
    if kind == "mcq":
        given = parse_letters(raw, item["options"], single=True)
        return given == key, given
    if kind == "msq":
        given = parse_letters(raw, item["options"], single=False)
        return given == sorted(key), given
    if kind == "nat":
        given = parse_number(raw)
        eps = 1e-9 * max(1.0, abs(key["min"]), abs(key["max"]))
        return key["min"] - eps <= given <= key["max"] + eps, given
    given = norm_text(raw)
    if given in key["accept"]:
        return True, given
    if key.get("regex") and re.fullmatch(key["regex"], str(raw).strip(), flags=re.I):
        return True, given
    return False, given


def marks_for(item: dict, ok: bool) -> float | None:
    """GATE-style marks: MCQ loses a third of its marks when wrong; MSQ and NAT never go negative."""
    marks = item.get("marks")
    if not marks:
        return None
    if ok:
        return float(marks)
    if item["type"] == "mcq":
        return -float(marks) / 3.0
    return 0.0


# ---------------------------------------------------------------- creation


def validate_draft(data, tree) -> dict:
    """Check an examiner's draft and return the normalised public item plus its sealed part."""
    if not isinstance(data, dict):
        raise CalError("an item draft must be a JSON object")
    kind = data.get("type")
    if kind not in TYPES:
        raise CalError("item type must be one of %s" % ", ".join(TYPES))
    topics = csv_list(data.get("topics"))
    if not topics:
        raise CalError("an item needs at least one topic (<skill>/<topic>); the first is its primary topic")
    for key in topics:
        tree.topic(key)  # raises with a helpful message if unknown
    if len(set(topics)) != len(topics):
        raise CalError("an item lists the same topic twice")
    skill = topics[0].split("/", 1)[0]
    if data.get("skill") and data["skill"] != skill:
        raise CalError("item skill %r does not match its primary topic %r" % (data["skill"], topics[0]))
    stem = str(data.get("stem") or "").strip()
    if len(stem) < 8:
        raise CalError("item stem is missing or too short")
    try:
        if isinstance(data.get("difficulty"), bool):
            raise TypeError
        difficulty = int(data.get("difficulty", 2))
    except (TypeError, ValueError, OverflowError):
        raise CalError("difficulty must be 1..5")
    if not 1 <= difficulty <= 5:
        raise CalError("difficulty must be 1..5")
    marks = data.get("marks")
    node = tree.get(skill)
    if marks is None and node.track.startswith("gate") and kind in ("mcq", "msq", "nat"):
        marks = 1
    if marks is not None and (isinstance(marks, bool) or marks not in (1, 2)):
        raise CalError("marks must be 1 or 2 (or omitted)")
    expect = data.get("expect_s")
    if expect is None:
        expect = (90 if marks == 1 else 210) if marks else DEFAULT_EXPECT[kind]
    try:
        if isinstance(expect, bool):
            raise TypeError
        expect = int(expect)
    except (TypeError, ValueError, OverflowError):
        raise CalError("expect_s must be a number of seconds")
    if expect <= 0:
        raise CalError("expect_s must be positive")

    public = {"type": kind, "skill": skill, "topics": topics, "difficulty": difficulty,
              "marks": marks, "expect_s": expect, "stem": stem}
    sealed = {"solution": str(data.get("solution") or "").strip()}

    if kind in ("mcq", "msq"):
        options = data.get("options")
        if isinstance(options, list):
            options = {chr(65 + i): v for i, v in enumerate(options)}
        if not isinstance(options, dict) or not 2 <= len(options) <= 8:
            raise CalError("%s items need 2 to 8 options" % kind)
        options = {str(k).strip().upper(): str(v).strip() for k, v in options.items()}
        if any(len(k) != 1 or not k.isalpha() for k in options) or any(not v for v in options.values()):
            raise CalError("option labels must be single letters with non-empty text")
        if len(set(norm_text(v) for v in options.values())) != len(options):
            raise CalError("two options have the same text")
        public["options"] = dict(sorted(options.items()))
        if "answer" not in data:
            raise CalError("%s items need an 'answer'" % kind)
        sealed["answer"] = parse_letters(data["answer"], options, single=(kind == "mcq"))
    elif kind == "nat":
        if "answer" not in data:
            raise CalError("nat items need a numeric 'answer' (a number, {value, tol} or {min, max})")
        sealed["answer"] = _nat_key(data["answer"])
    elif kind == "short":
        if "answer" not in data:
            raise CalError("short items need an 'answer' (text, a list of accepted texts, or {accept, regex})")
        sealed["answer"] = _short_key(data["answer"])
    else:
        check = str(data.get("check") or "").strip()
        rubric = [str(r).strip() for r in (data.get("rubric") or []) if str(r).strip()]
        if kind in ("code", "task") and len(check) < 10:
            raise CalError("%s items need a 'check': the exact commands to run and what must be true to pass" % kind)
        # The checker runs the check on its own solution in a scratch folder and the tutor on the learner's
        # work, so the check must not lead into the learner's exercise folder itself.
        if "learner/work" in check.replace("\\", "/"):
            raise CalError("a check runs from inside the exercise folder: give its commands without "
                           "`cd learner/work/...` or any path into learner/work/ (the stem names the folder)")
        if kind == "open" and not rubric:
            raise CalError("open items need a 'rubric' (a list of things a correct answer must contain)")
        public["check"] = check
        public["rubric"] = rubric
    if kind in AUTO_TYPES and len(sealed["solution"]) < 10:
        raise CalError("items need a 'solution' that explains why the key is right")

    source = data.get("source") or {}
    if isinstance(source, str):
        source = {"kind": source}
    if not isinstance(source, dict):
        raise CalError("source must be a kind (generated, official, ...) or {kind, ref, url}")
    src_kind = source.get("kind") or "generated"
    if src_kind not in SOURCE_KINDS:
        raise CalError("source.kind must be one of %s" % ", ".join(SOURCE_KINDS))
    if src_kind == "official" and not source.get("ref"):
        raise CalError("official items need source.ref (paper, year, question number)")
    public["source"] = {"kind": src_kind, "ref": str(source.get("ref") or ""), "url": str(source.get("url") or "")}
    return {"public": public, "sealed": sealed}


def create(repo: Repo, tree, data, created_by: str = "examiner") -> dict:
    """Validate and store a draft item; returns the stored item (with id)."""
    parts = validate_draft(data, tree)
    item = dict(parts["public"])
    item["id"] = short_id("it-")
    item["v"] = 1
    item["created"] = iso(now())
    item["created_by"] = created_by
    item["sealed"] = seal(parts["sealed"])
    path = os.path.join(repo.items_dir, item["skill"], item["id"] + ".json")
    write_text(path, json.dumps(item, ensure_ascii=False, indent=1) + "\n")
    repo.append("item_draft", item=item["id"], skill=item["skill"], topics=item["topics"],
                type=item["type"], src=item["source"]["kind"])
    return item


def find_path(repo: Repo, ident: str):
    if not re.match(r"^it-[a-z0-9]{6,26}$", ident or ""):
        raise CalError("item ids look like it-xxxxxxxxxx; got %r" % ident)
    if os.path.isdir(repo.items_dir):
        for skill in sorted(os.listdir(repo.items_dir)):
            path = os.path.join(repo.items_dir, skill, ident + ".json")
            if os.path.isfile(path):
                return path
    return None


def load(repo: Repo, ident: str) -> dict:
    path = find_path(repo, ident)
    if path is None:
        raise CalError("no item %s" % ident)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except ValueError:
        raise CalError("item file %s is not valid JSON" % repo.rel(path))


# ---------------------------------------------------------------- display


def blind_text(item: dict, tree, with_check: bool = False) -> str:
    """The question without its key or solution."""
    head = ["ITEM %s" % item["id"], item["type"]]
    primary = item["topics"][0]
    extra = item["topics"][1:]
    head.append(primary + ((" (+%s)" % ", ".join(extra)) if extra else ""))
    head.append("difficulty %d" % item["difficulty"])
    if item.get("marks"):
        head.append("%d mark%s" % (item["marks"], "" if item["marks"] == 1 else "s"))
    head.append("expect %ds" % item["expect_s"])
    lines = [" · ".join(head), "---", item["stem"], ""]
    for label, text in (item.get("options") or {}).items():
        lines.append("%s. %s" % (label, text))
    if item["type"] == "msq":
        lines.append("")
        lines.append("(one or more options may be correct; no partial credit)")
    if item["type"] == "nat":
        lines.append("(numeric answer)")
    text = "\n".join(lines).rstrip()
    if with_check and item["type"] not in AUTO_TYPES:
        # below a second line of dashes: the question above is for the learner, this part is not
        extra = []
        if item.get("check"):
            extra += ["CHECK (run it from inside the exercise folder the question names):", item["check"]]
        if item.get("rubric"):
            extra += ([""] if extra else []) + ["RUBRIC (a correct answer contains):"] + ["- " + r for r in item["rubric"]]
        if extra:
            text += "\n---\n" + "\n".join(extra)
    return text


def reveal_text(item: dict) -> str:
    sealed = unseal(item)
    lines = []
    if "answer" in sealed:
        ans = sealed["answer"]
        if item["type"] == "nat":
            lo, hi = ans["min"], ans["max"]
            shown = _fmt_num(lo) if lo == hi else "%s to %s" % (_fmt_num(lo), _fmt_num(hi))
        elif item["type"] == "msq":
            shown = ", ".join(ans)
        elif item["type"] == "short":
            shown = " | ".join(ans["accept"]) or ("pattern " + str(ans.get("regex")))
        else:
            shown = str(ans)
        lines.append("KEY: " + shown)
    if sealed.get("solution"):
        lines.append("SOLUTION: " + sealed["solution"])
    return "\n".join(lines)


def _fmt_num(x: float) -> str:
    return ("%d" % x) if float(x).is_integer() and abs(x) < 1e15 else ("%.6g" % x)


# ---------------------------------------------------------------- selection


def candidates(state, topic_key: str) -> list:
    """Verified items whose primary topic is topic_key."""
    return [it for it in state.items.values()
            if it.status == "verified" and it.topics and it.topics[0] == topic_key]


def pick(repo: Repo, state, topic_key: str, when, difficulty: int | None = None, exclude=()):
    """Choose the best verified item for a topic, or None.

    Order: items failed and not yet redeemed (but not ones failed today),
    then unseen items, then the least recently seen.
    """
    today = state.day(when)
    rows = []
    for it in candidates(state, topic_key):
        if it.id in exclude:
            continue
        if it.last_ok is False and it.fail_day != today:
            bucket = 0
        elif it.n_shown == 0:
            bucket = 1
        elif it.last_ok is False:
            bucket = 3  # failed today: only if nothing else is left
        else:
            bucket = 2
        gap = 0
        if difficulty is not None:
            try:
                gap = abs(int(load(repo, it.id).get("difficulty", 2)) - difficulty)
            except CalError:
                continue
        last = it.last_ts or it.shown_ts
        rows.append((bucket, gap, last.timestamp() if last else 0.0, it.id))
    if not rows:
        return None
    rows.sort()
    return rows[0][3]


def target_difficulty(state, tree, topic_key: str) -> int:
    """Start at the topic's level; step up after three clean answers, down after two misses."""
    topic = tree.topic(topic_key)
    level = max(1, min(5, topic.level))
    ts = state.topics.get(topic_key)
    if ts is None:
        return level
    recent = [ok for _, ok, _ in ts.recent]
    if len(recent) >= 3 and all(recent[-3:]):
        level += 1
    elif len(recent) >= 2 and not any(recent[-2:]):
        level -= 1
    return max(1, min(5, level))
