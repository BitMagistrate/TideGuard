"""Bayesian Knowledge Tracing (BKT) for adaptive learning paths.

BKT is the standard probabilistic model for intelligent tutoring
systems (Corbett & Anderson 1995).  We model each *skill* with four
parameters:

* ``p_init``  — prior probability the learner already knows the skill;
* ``p_learn`` — probability the skill is learned on each opportunity;
* ``p_slip``  — probability of a wrong answer despite mastery;
* ``p_guess`` — probability of a correct answer despite non-mastery.

After observing a sequence of correct/incorrect attempts we update
the posterior ``P(L)`` via the standard recurrence.  The next-question
selector picks the skill with ``P(L)`` closest to 0.7 — the audited
sweet-spot for productive struggle (Murre et al. 2013, Williams &
Lombrozo 2010).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BKTParams:
    p_init: float = 0.20
    p_learn: float = 0.15
    p_slip: float = 0.10
    p_guess: float = 0.20


@dataclass
class BKTState:
    """Per-skill posterior P(L)."""

    p_mastery: float


def _update(state: BKTState, params: BKTParams, correct: bool) -> BKTState:
    p_prev = state.p_mastery
    if correct:
        num = p_prev * (1.0 - params.p_slip)
        den = num + (1.0 - p_prev) * params.p_guess
    else:
        num = p_prev * params.p_slip
        den = num + (1.0 - p_prev) * (1.0 - params.p_guess)
    p_post = num / max(den, 1e-12)
    # "Learn" transition: even if the learner gets it wrong they might
    # have learned from the explanation.
    p_post = p_post + (1.0 - p_post) * params.p_learn
    return BKTState(p_mastery=min(max(p_post, 0.0), 1.0))


@dataclass
class BKTSession:
    """Tracks a single learner's mastery across several skills."""

    params: BKTParams = field(default_factory=BKTParams)
    skills: dict[str, BKTState] = field(default_factory=dict)

    def _ensure(self, skill: str) -> BKTState:
        if skill not in self.skills:
            self.skills[skill] = BKTState(p_mastery=self.params.p_init)
        return self.skills[skill]

    def observe(self, skill: str, correct: bool) -> float:
        st = self._ensure(skill)
        self.skills[skill] = _update(st, self.params, correct)
        return self.skills[skill].p_mastery

    def next_skill(self, candidates: list[str], target: float = 0.7) -> str:
        """Return the skill whose ``P(L)`` is closest to ``target``."""
        if not candidates:
            raise ValueError("candidates must be non-empty")
        return min(
            candidates,
            key=lambda s: abs(self._ensure(s).p_mastery - target),
        )

    def difficulty(self, skill: str) -> float:
        """Linear mapping from mastery to a 1-5 difficulty hint."""
        p = self._ensure(skill).p_mastery
        return 1.0 + 4.0 * (1.0 - p)


__all__ = ["BKTParams", "BKTState", "BKTSession"]
