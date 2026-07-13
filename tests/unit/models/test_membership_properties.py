"""Invariant tests for Membership credit logic.

These complement the example-based tests in ``test_membership.py`` by checking
rules that must hold across varied credit balances and operation sequences.

Membership objects are constructed in memory only — no database IO.
"""

from datetime import date, timedelta

import pytest

from app.models import Membership


@pytest.fixture(autouse=True)
def _app_context(app):
    """Ensure an app context is available for SQLAlchemy model construction."""
    pass


def _make_membership(initial: int = 20, purchased: int = 0, active: bool = True) -> Membership:
    return Membership(
        user_id=1,
        start_date=date.today() - timedelta(days=30),
        expiry_date=date.today() + timedelta(days=335),
        initial_credits=initial,
        purchased_credits=purchased,
        status="active" if active else "pending",
    )


@pytest.mark.parametrize(
    "initial,purchased",
    [
        (0, 0),
        (20, 0),
        (0, 15),
        (10, 5),
        (-5, 0),
        (0, -3),
        (-10, 20),
        (200, 50),
    ],
)
def test_credits_remaining_equals_initial_plus_purchased(initial, purchased):
    m = _make_membership(initial=initial, purchased=purchased)
    assert m.credits_remaining() == initial + purchased


@pytest.mark.parametrize(
    "initial,purchased,expected_result,expected_remaining",
    [
        (5, 0, True, 4),
        (0, 3, True, 2),
        (0, 0, False, 0),
        (-2, 0, False, -2),
        (0, -1, False, -1),
    ],
)
def test_use_credit_decreases_total_by_one_when_successful(initial, purchased, expected_result, expected_remaining):
    m = _make_membership(initial=initial, purchased=purchased)
    before = m.credits_remaining()

    result = m.use_credit()

    assert result is expected_result
    assert m.credits_remaining() == expected_remaining
    if expected_result:
        assert m.credits_remaining() == before - 1


@pytest.mark.parametrize(
    "initial,purchased,expected_initial,expected_purchased",
    [
        (10, 5, 9, 5),
        (1, 20, 0, 20),
    ],
)
def test_use_credit_takes_initial_first(initial, purchased, expected_initial, expected_purchased):
    m = _make_membership(initial=initial, purchased=purchased)
    m.use_credit()
    assert m.initial_credits == expected_initial
    assert m.purchased_credits == expected_purchased


@pytest.mark.parametrize("purchased", [1, 5, 20])
def test_use_credit_takes_purchased_when_initial_zero(purchased):
    m = _make_membership(initial=0, purchased=purchased)
    m.use_credit()
    assert m.initial_credits == 0
    assert m.purchased_credits == purchased - 1


@pytest.mark.parametrize(
    "initial,purchased",
    [
        (0, 0),
        (-5, 0),
        (0, -2),
        (-10, -3),
    ],
)
def test_use_credit_no_mutation_on_false(initial, purchased):
    m = _make_membership(initial=initial, purchased=purchased)
    result = m.use_credit(allow_negative=False)
    assert result is False
    assert m.initial_credits == initial
    assert m.purchased_credits == purchased


@pytest.mark.parametrize(
    "initial,purchased,amount,expected_purchased",
    [
        (10, 5, 0, 5),
        (0, 0, 7, 7),
        (-5, 3, 10, 13),
        (20, -2, 4, 2),
    ],
)
def test_add_credits_only_changes_purchased(initial, purchased, amount, expected_purchased):
    m = _make_membership(initial=initial, purchased=purchased)
    m.add_credits(amount)
    assert m.initial_credits == initial
    assert m.purchased_credits == expected_purchased


@pytest.mark.parametrize(
    "initial,purchased,amount,expected_initial,expected_purchased",
    [
        (10, 5, 0, 10, 5),
        (10, 5, 4, 6, 5),
        (10, 5, 10, 0, 5),
        (10, 5, 12, 0, 3),
        (10, 5, 15, 0, 0),
        (0, 8, 3, 0, 5),
        (0, 8, 20, 0, -12),
    ],
)
def test_remove_credits_deducts_initial_first(initial, purchased, amount, expected_initial, expected_purchased):
    m = _make_membership(initial=initial, purchased=purchased)
    m.remove_credits(amount)
    assert m.initial_credits == expected_initial
    assert m.purchased_credits == expected_purchased


@pytest.mark.parametrize(
    "initial,purchased,operations",
    [
        (10, 5, [("use", None), ("use", None), ("add", 3)]),
        (5, 5, [("add", 10), ("remove", 4), ("use", None)]),
        (0, 10, [("use", None), ("use", None), ("remove", 2), ("add", 5)]),
        (20, 0, [("remove", 15), ("use", None), ("add", 1), ("use", None)]),
    ],
)
def test_credits_remaining_invariant_after_operations(initial, purchased, operations):
    m = _make_membership(initial=initial, purchased=purchased)

    for op, arg in operations:
        if op == "use":
            m.use_credit()
        elif op == "add":
            m.add_credits(arg)
        elif op == "remove":
            m.remove_credits(arg)

    assert m.credits_remaining() == m.initial_credits + m.purchased_credits
