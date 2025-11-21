"""Tests for membership model"""

from datetime import date, timedelta

import pytest


class TestMembership:
    def test_is_active(self, test_user):
        assert test_user.membership.is_active()

    def test_credits_remaining(self, test_user):
        """Test credits remaining"""
        assert test_user.membership.credits_remaining() >= 0

    def test_use_credit(self, test_user):
        """Test using a credit"""
        initial_credits = test_user.membership.credits
        result = test_user.membership.use_credit()

        assert result is True
        assert test_user.membership.credits == initial_credits - 1

    def test_use_credit_when_none_left(self, test_user):
        """Test using credit when none left"""
        test_user.membership.credits = 0
        result = test_user.membership.use_credit()

        assert result is False
        assert test_user.membership.credits == 0

    def test_add_credits(self, test_user):
        """Test adding credits"""
        initial_credits = test_user.membership.credits
        test_user.membership.add_credits(5)

        assert test_user.membership.credits == initial_credits + 5

    def test_renew(self, test_user):
        """Test membership renewal"""
        test_user.membership.credits = 5
        test_user.membership.renew()

        assert test_user.membership.start_date == date.today()
        assert test_user.membership.credits == 20
        assert test_user.membership.status == "active"

    def test_activate(self, test_user):
        """Test activating a pending membership"""
        test_user.membership.status = "pending"
        test_user.membership.activate()

        assert test_user.membership.status == "active"

    def test_membership_repr(self, test_user):
        """Test membership string representation"""
        repr_str = repr(test_user.membership)

        assert "Membership" in repr_str
        assert str(test_user.id) in repr_str
