"""Unit tests for the Bayesian Knowledge Tracing service."""

from __future__ import annotations

from tideguard_api.services.bkt import BKTParams, BKTSession


def test_correct_answers_increase_mastery() -> None:
    s = BKTSession(params=BKTParams(p_init=0.20))
    prev = s.observe("currents", correct=False)
    for _ in range(5):
        new = s.observe("currents", correct=True)
        assert new >= prev
        prev = new
    assert prev > 0.8


def test_incorrect_answer_after_mastery_decreases() -> None:
    s = BKTSession(params=BKTParams(p_init=0.95))
    p1 = s.observe("currents", correct=False)
    p2 = s.observe("currents", correct=False)
    # After two wrong answers from a "knew it" start, mastery should drop
    # below the initial value (slip is much smaller than 1 - guess).
    assert p1 < 0.95
    assert p2 < p1


def test_next_skill_picks_zpd() -> None:
    s = BKTSession(params=BKTParams(p_init=0.20))
    s.observe("currents", correct=True)  # bumps mastery
    s.observe("currents", correct=True)
    # 'tides' was never practised, so P(L)=p_init=0.2. We want the
    # selector to prefer the one closer to 0.7 — currents.
    chosen = s.next_skill(["currents", "tides"])
    assert chosen == "currents"


def test_difficulty_decreases_with_mastery() -> None:
    s = BKTSession()
    base = s.difficulty("currents")
    for _ in range(10):
        s.observe("currents", correct=True)
    after = s.difficulty("currents")
    assert after < base
    assert 1.0 <= after <= 5.0
