"""Property-based tests for Membership credit logic using Hypothesis.

These tests verify invariants that must hold for *any* combination of
initial/purchased credit values and operation sequences.  They complement the
example-based tests in ``test_membership.py``.

The ``membership`` helper constructs ``Membership`` objects using the normal
constructor within an app context (required by SQLAlchemy), but never adds
them to the session — no database IO takes place.
"""

from datetime import date, timedelta

import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.models import Membership


@pytest.fixture(autouse=True)
def _app_context(app):
    """Ensure an app context is available for SQLAlchemy model construction."""
    pass


def _make_membership(initial: int = 20, purchased: int = 0, active: bool = True) -> Membership:
    """Build a transient Membership (not added to DB session)."""
    return Membership(
        user_id=1,
        start_date=date.today() - timedelta(days=30),
        expiry_date=date.today() + timedelta(days=335),
        initial_credits=initial,
        purchased_credits=purchased,
        status="active" if active else "pending",
    )


# ---------------------------------------------------------------------------
# credits_remaining is always initial + purchased
# ---------------------------------------------------------------------------


@given(
    initial=st.integers(-50, 200),
    purchased=st.integers(-50, 200),
)
def test_credits_remaining_equals_initial_plus_purchased(initial, purchased):
    m = _make_membership(initial=initial, purchased=purchased)
    assert m.credits_remaining() == initial + purchased


# ---------------------------------------------------------------------------
# use_credit decreases total by exactly 1 when it returns True
# ---------------------------------------------------------------------------


@given(
    initial=st.integers(0, 100),
    purchased=st.integers(0, 100),
)
def test_use_credit_decreases_total_by_one(initial, purchased):
    m = _make_membership(initial=initial, purchased=purchased)
    before = m.credits_remaining()

    result = m.use_credit()

    if before > 0:
        assert result is True
        assert m.credits_remaining() == before - 1
    else:
        assert result is False
        assert m.credits_remaining() == before


# ---------------------------------------------------------------------------
# use_credit takes from initial before purchased
# ---------------------------------------------------------------------------


@given(
    initial=st.integers(1, 100),
    purchased=st.integers(0, 100),
)
def test_use_credit_takes_initial_first(initial, purchased):
    m = _make_membership(initial=initial, purchased=purchased)

    m.use_credit()

    assert m.initial_credits == initial - 1
    assert m.purchased_credits == purchased


@given(purchased=st.integers(1, 100))
def test_use_credit_takes_purchased_when_initial_zero(purchased):
    m = _make_membership(initial=0, purchased=purchased)

    m.use_credit()

    assert m.initial_credits == 0
    assert m.purchased_credits == purchased - 1


# ---------------------------------------------------------------------------
# use_credit(allow_negative=False) never mutates when returning False
# ---------------------------------------------------------------------------


@given(
    initial=st.integers(-50, 0),
    purchased=st.integers(-50, 0),
)
def test_use_credit_no_mutation_on_false(initial, purchased):
    m = _make_membership(initial=initial, purchased=purchased)

    result = m.use_credit(allow_negative=False)

    assert result is False
    assert m.initial_credits == initial
    assert m.purchased_credits == purchased


# ---------------------------------------------------------------------------
# add_credits only affects purchased_credits
# ---------------------------------------------------------------------------


@given(
    initial=st.integers(-50, 100),
    purchased=st.integers(-50, 100),
    amount=st.integers(0, 100),
)
def test_add_credits_only_changes_purchased(initial, purchased, amount):
    m = _make_membership(initial=initial, purchased=purchased)

    m.add_credits(amount)

    assert m.initial_credits == initial
    assert m.purchased_credits == purchased + amount


# ---------------------------------------------------------------------------
# remove_credits takes from initial first, then purchased
# ---------------------------------------------------------------------------


@given(
    initial=st.integers(0, 100),
    purchased=st.integers(0, 100),
    amount=st.integers(0, 200),
)
def test_remove_credits_deducts_initial_first(initial, purchased, amount):
    m = _make_membership(initial=initial, purchased=purchased)

    m.remove_credits(amount)

    deduct_from_initial = min(amount, max(initial, 0))
    remaining = amount - deduct_from_initial

    assert m.initial_credits == initial - deduct_from_initial
    if remaining > 0:
        assert m.purchased_credits == purchased - remaining
    else:
        assert m.purchased_credits == purchased


# ---------------------------------------------------------------------------
# credits_remaining is consistent after any sequence of operations
# ---------------------------------------------------------------------------


@given(
    initial=st.integers(0, 50),
    purchased=st.integers(0, 50),
    operations=st.lists(
        st.one_of(
            st.tuples(st.just("use"), st.just(None)),
            st.tuples(st.just("add"), st.integers(1, 20)),
            st.tuples(st.just("remove"), st.integers(1, 20)),
        ),
        max_size=30,
    ),
)
def test_credits_remaining_invariant_after_operations(initial, purchased, operations):
    """credits_remaining() == initial_credits + purchased_credits after any operation sequence."""
    m = _make_membership(initial=initial, purchased=purchased)

    for op, arg in operations:
        if op == "use":
            m.use_credit()
        elif op == "add":
            m.add_credits(arg)
        elif op == "remove":
            m.remove_credits(arg)

    assert m.credits_remaining() == m.initial_credits + m.purchased_credits
