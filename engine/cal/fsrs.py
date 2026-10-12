"""FSRS-6 memory model (Free Spaced Repetition Scheduler), standard library only.

This is an independent port of the published FSRS-6 formulas, checked
number-for-number against py-fsrs 6.3.2 (see tests/test_fsrs.py). The default
parameters are the FSRS-6 defaults shipped by py-fsrs.

  FSRS and py-fsrs: Copyright (c) 2022 Open Spaced Repetition, MIT License.
  https://github.com/open-spaced-repetition/py-fsrs

What differs from py-fsrs on purpose:
  * no minute-level learning steps: a card is scheduled in whole days from its
    first review (the caller decides how soon a failed card comes back);
  * the optional interval "fuzz" takes its randomness from the caller, so
    replaying the event log always produces the same schedule.

Grades: 1 Again (failed), 2 Hard, 3 Good, 4 Easy.
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta

AGAIN, HARD, GOOD, EASY = 1, 2, 3, 4
GRADE_NAMES = {1: "Again", 2: "Hard", 3: "Good", 4: "Easy"}

DEFAULT_PARAMETERS = (
    0.212, 1.2931, 2.3065, 8.2956,   # initial stability for Again / Hard / Good / Easy
    6.4133, 0.8334,                  # initial difficulty
    3.0194, 0.001,                   # difficulty update, mean reversion
    1.8722, 0.1666, 0.796,           # stability after recall
    1.4835, 0.0614, 0.2629, 1.6483,  # stability after forgetting
    0.6014, 1.8729,                  # hard penalty, easy bonus
    0.5425, 0.0912, 0.0658,          # same-day (short-term) stability
    0.1542,                          # decay
)

STABILITY_MIN = 0.001
MIN_DIFFICULTY = 1.0
MAX_DIFFICULTY = 10.0

_FUZZ_RANGES = ((2.5, 7.0, 0.15), (7.0, 20.0, 0.1), (20.0, math.inf, 0.05))


class Card:
    """Memory state of one reviewable thing (here: one topic)."""

    __slots__ = ("s", "d", "last", "due", "reps", "lapses")

    def __init__(self, s=None, d=None, last=None, due=None, reps=0, lapses=0):
        self.s = s          # stability, in days
        self.d = d          # difficulty, 1..10
        self.last = last    # datetime of the last review
        self.due = due      # datetime of the next review
        self.reps = reps
        self.lapses = lapses

    def copy(self) -> "Card":
        return Card(self.s, self.d, self.last, self.due, self.reps, self.lapses)

    def __repr__(self) -> str:
        return "Card(s=%r, d=%r, last=%r, due=%r)" % (self.s, self.d, self.last, self.due)


class Scheduler:
    def __init__(self, parameters=DEFAULT_PARAMETERS, retention: float = 0.9, max_interval: int = 36500):
        if len(parameters) != 21:
            raise ValueError("FSRS-6 needs 21 parameters, got %d" % len(parameters))
        self.w = tuple(float(x) for x in parameters)
        self.retention = float(retention)
        self.max_interval = int(max_interval)
        self._decay = -self.w[20]
        self._factor = 0.9 ** (1.0 / self._decay) - 1.0

    # ---------------------------------------------------------- formulas

    def retrievability(self, stability: float, elapsed_days: float) -> float:
        """Probability of recall after elapsed_days at the given stability."""
        if not stability or stability <= 0:
            return 0.0
        return (1.0 + self._factor * max(0.0, elapsed_days) / stability) ** self._decay

    def initial_stability(self, grade: int) -> float:
        return max(self.w[grade - 1], STABILITY_MIN)

    def initial_difficulty(self, grade: int, clamp: bool = True) -> float:
        d = self.w[4] - math.exp(self.w[5] * (grade - 1)) + 1.0
        return _clamp_d(d) if clamp else d

    def interval(self, stability: float, retention: float | None = None) -> int:
        """Whole days until recall probability falls to the target retention."""
        r = self.retention if retention is None else retention
        days = (stability / self._factor) * (r ** (1.0 / self._decay) - 1.0)
        return min(max(int(round(days)), 1), self.max_interval)

    def short_term_stability(self, stability: float, grade: int) -> float:
        increase = math.exp(self.w[17] * (grade - 3 + self.w[18])) * stability ** (-self.w[19])
        if grade >= HARD:
            increase = max(increase, 1.0)
        return max(stability * increase, STABILITY_MIN)

    def next_difficulty(self, difficulty: float, grade: int) -> float:
        target = self.initial_difficulty(EASY, clamp=False)
        delta = -(self.w[6] * (grade - 3))
        damped = difficulty + (10.0 - difficulty) * delta / 9.0
        return _clamp_d(self.w[7] * target + (1.0 - self.w[7]) * damped)

    def next_stability(self, difficulty: float, stability: float, retrievability: float, grade: int) -> float:
        if grade == AGAIN:
            long_term = (
                self.w[11]
                * difficulty ** (-self.w[12])
                * ((stability + 1.0) ** self.w[13] - 1.0)
                * math.exp((1.0 - retrievability) * self.w[14])
            )
            short_term = stability / math.exp(self.w[17] * self.w[18])
            result = min(long_term, short_term)
        else:
            hard_penalty = self.w[15] if grade == HARD else 1.0
            easy_bonus = self.w[16] if grade == EASY else 1.0
            result = stability * (
                1.0
                + math.exp(self.w[8])
                * (11.0 - difficulty)
                * stability ** (-self.w[9])
                * (math.exp((1.0 - retrievability) * self.w[10]) - 1.0)
                * hard_penalty
                * easy_bonus
            )
        return max(result, STABILITY_MIN)

    # ---------------------------------------------------------- review

    def review(self, card: Card | None, grade: int, when: datetime, retention: float | None = None,
               fuzz: float | None = None):
        """Apply one review. Returns (new_card, interval_days).

        `when` must be timezone-aware. `fuzz`, if given, is a number in [0, 1)
        used to spread the interval slightly (deterministic for the caller).
        """
        if grade not in (AGAIN, HARD, GOOD, EASY):
            raise ValueError("grade must be 1..4, got %r" % (grade,))
        new = card.copy() if card is not None else Card()
        if new.s is None or new.d is None or new.last is None:
            new.s = self.initial_stability(grade)
            new.d = self.initial_difficulty(grade)
        else:
            elapsed = (when - new.last).days
            if elapsed < 1:
                new.s = self.short_term_stability(new.s, grade)
            else:
                r = self.retrievability(new.s, max(0, elapsed))
                new.s = self.next_stability(new.d, new.s, r, grade)
            new.d = self.next_difficulty(new.d, grade)
        days = self.interval(new.s, retention)
        if fuzz is not None:
            days = self.fuzzed(days, fuzz)
        new.last = when
        new.due = when + timedelta(days=days)
        new.reps += 1
        if grade == AGAIN:
            new.lapses += 1
        return new, days

    def fuzzed(self, days: int, u: float) -> int:
        """Spread an interval by a few percent using u in [0, 1)."""
        if days < 2.5:
            return days
        delta = 1.0
        for start, end, factor in _FUZZ_RANGES:
            delta += factor * max(min(float(days), end) - start, 0.0)
        low = max(2, int(round(days - delta)))
        high = min(int(round(days + delta)), self.max_interval)
        low = min(low, high)
        return min(low + int(u * (high - low + 1)), high)


def _clamp_d(d: float) -> float:
    return min(max(d, MIN_DIFFICULTY), MAX_DIFFICULTY)
