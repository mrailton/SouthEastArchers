"""Tests for membership model"""
import pytest
from datetime import date


class TestMembership:
    def test_is_active(self, test_user):
        assert test_user.membership.is_active()
    
    def test_nights_remaining(self, test_user):
        from config.config import Config
        remaining = test_user.membership.nights_remaining()
        assert remaining == Config.MEMBERSHIP_NIGHTS_INCLUDED
    
    def test_renew(self, test_user):
        original_expiry = test_user.membership.expiry_date
        test_user.membership.renew()
        
        assert test_user.membership.start_date == date.today()
        assert test_user.membership.nights_used == 0
        assert test_user.membership.expiry_date > original_expiry
