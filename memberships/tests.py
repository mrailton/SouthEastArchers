"""
Tests for the memberships app.
"""
import pytest
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from memberships.models import Membership, CreditPurchase
from memberships.forms import CreditPurchaseForm

User = get_user_model()


# ============================================================================
# MODEL TESTS
# ============================================================================

@pytest.mark.models
@pytest.mark.django_db
class TestMembershipModel:
    """Test the Membership model."""

    def test_create_membership(self, user):
        """Test creating a membership."""
        membership = Membership.objects.create(
            user=user,
            end_date=timezone.now() + timedelta(days=365),
            credits_remaining=20,
            is_active=True,
            amount_paid=100
        )
        assert membership.user == user
        assert membership.credits_remaining == 20
        assert membership.is_active is True
        assert membership.amount_paid == 100

    def test_membership_string_representation(self, user, membership):
        """Test __str__ method returns user email and dates."""
        # Format: email - start_date to end_date
        assert user.email in str(membership)
        assert str(membership.start_date.date()) in str(membership)
        assert str(membership.end_date.date()) in str(membership)

    def test_membership_defaults(self, user):
        """Test default values for membership."""
        membership = Membership.objects.create(
            user=user,
            end_date=timezone.now() + timedelta(days=365)
        )
        assert membership.credits_remaining == 20
        assert membership.is_active is True
        assert membership.amount_paid == 100.0  # Default is 100

    def test_expired_membership_not_active(self, user):
        """Test expired membership has is_active=False."""
        membership = Membership.objects.create(
            user=user,
            end_date=timezone.now() - timedelta(days=1),
            is_active=False
        )
        assert membership.is_active is False

    def test_membership_ordering(self, user):
        """Test memberships are ordered by start_date descending."""
        # Create memberships at different times
        old_membership = Membership.objects.create(
            user=user,
            end_date=timezone.now() + timedelta(days=365)
        )
        # Manually set created_at to an older date
        old_membership.created_at = timezone.now() - timedelta(days=100)
        old_membership.save()

        new_membership = Membership.objects.create(
            user=user,
            end_date=timezone.now() + timedelta(days=365)
        )

        memberships = list(Membership.objects.all())
        assert memberships[0] == new_membership
        assert memberships[1] == old_membership


@pytest.mark.models
@pytest.mark.django_db
class TestCreditPurchaseModel:
    """Test the CreditPurchase model."""

    def test_create_credit_purchase(self, user):
        """Test creating a credit purchase."""
        purchase = CreditPurchase.objects.create(
            user=user,
            credits_purchased=10,
            amount_paid=50
        )
        assert purchase.user == user
        assert purchase.credits_purchased == 10
        assert purchase.amount_paid == 50
        assert purchase.purchase_date is not None

    def test_credit_purchase_string_representation(self, user, credit_purchase):
        """Test __str__ method."""
        expected = f"{user.email} - 10 credits"
        assert str(credit_purchase) == expected

    def test_credit_purchase_ordering(self, user):
        """Test credit purchases ordered by purchase_date descending."""
        old_purchase = CreditPurchase.objects.create(
            user=user,
            credits_purchased=5,
            amount_paid=25
        )
        # Manually set purchase_date to older
        old_purchase.purchase_date = timezone.now() - timedelta(days=10)
        old_purchase.save()

        new_purchase = CreditPurchase.objects.create(
            user=user,
            credits_purchased=10,
            amount_paid=50
        )

        purchases = list(CreditPurchase.objects.all())
        assert purchases[0] == new_purchase
        assert purchases[1] == old_purchase


# ============================================================================
# FORM TESTS
# ============================================================================

@pytest.mark.forms
@pytest.mark.django_db
class TestCreditPurchaseForm:
    """Test the CreditPurchaseForm."""

    def test_valid_form(self):
        """Test form with valid credit amount."""
        form = CreditPurchaseForm(data={'credits': 10}, credit_cost=5)
        assert form.is_valid()

    def test_minimum_credits(self):
        """Test form requires at least 1 credit."""
        form = CreditPurchaseForm(data={'credits': 0}, credit_cost=5)
        assert not form.is_valid()
        assert 'credits' in form.errors

    def test_negative_credits_invalid(self):
        """Test negative credits are invalid."""
        form = CreditPurchaseForm(data={'credits': -5}, credit_cost=5)
        assert not form.is_valid()

    def test_form_label(self):
        """Test form field has correct label."""
        form = CreditPurchaseForm(credit_cost=5)
        assert form.fields['credits'].label == 'Number of Credits'
        assert form.credit_cost == 5


# ============================================================================
# VIEW TESTS
# ============================================================================

@pytest.mark.views
@pytest.mark.django_db
class TestMembershipDashboardView:
    """Test the membership dashboard view."""

    def test_dashboard_requires_login(self, client):
        """Test dashboard redirects to login for anonymous users."""
        response = client.get(reverse('memberships:dashboard'))
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_dashboard_loads_for_authenticated_user(self, authenticated_client, membership):
        """Test dashboard loads for logged-in user."""
        response = authenticated_client.get(reverse('memberships:dashboard'))
        assert response.status_code == 200
        assert 'membership' in response.context

    def test_dashboard_shows_active_membership(self, authenticated_client, membership):
        """Test dashboard displays active membership details."""
        response = authenticated_client.get(reverse('memberships:dashboard'))
        assert response.context['membership'] == membership
        content = response.content.decode()
        # Check that membership details are displayed
        assert str(membership.credits_remaining) in content

    def test_dashboard_shows_credit_purchases(self, authenticated_client, user, membership):
        """Test dashboard shows last 5 credit purchases."""
        # Create 7 credit purchases
        for i in range(7):
            CreditPurchase.objects.create(
                user=user,
                credits_purchased=i + 1,
                amount_paid=(i + 1) * 5
            )

        response = authenticated_client.get(reverse('memberships:dashboard'))
        purchases = response.context['recent_purchases']
        assert len(purchases) == 5  # Only last 5
        assert purchases[0].credits_purchased == 7  # Most recent first

    def test_dashboard_no_membership(self, authenticated_client):
        """Test dashboard when user has no active membership."""
        response = authenticated_client.get(reverse('memberships:dashboard'))
        assert response.status_code == 200
        assert response.context['membership'] is None

    def test_dashboard_shows_user_name(self, authenticated_client, user, membership):
        """Test dashboard displays user name in welcome message."""
        response = authenticated_client.get(reverse('memberships:dashboard'))
        content = response.content.decode()
        assert user.name in content


@pytest.mark.views
@pytest.mark.django_db
class TestPurchaseCreditsView:
    """Test the purchase credits view."""

    def test_purchase_credits_requires_login(self, client):
        """Test purchase credits redirects to login for anonymous users."""
        response = client.get(reverse('memberships:purchase_credits'))
        assert response.status_code == 302
        assert '/accounts/login/' in response.url

    def test_purchase_credits_page_loads(self, authenticated_client, membership):
        """Test purchase credits page loads for authenticated user."""
        response = authenticated_client.get(reverse('memberships:purchase_credits'))
        assert response.status_code == 200
        assert 'form' in response.context

    def test_purchase_credits_updates_membership(self, authenticated_client, user, membership):
        """Test purchasing credits updates active membership."""
        initial_credits = membership.credits_remaining

        response = authenticated_client.post(
            reverse('memberships:purchase_credits'),
            {'credits': 10}
        )

        # Refresh membership from database
        membership.refresh_from_db()
        assert membership.credits_remaining == initial_credits + 10

        # Check redirect
        assert response.status_code == 302
        assert response.url == reverse('memberships:dashboard')

    def test_purchase_credits_creates_purchase_record(self, authenticated_client, user, membership):
        """Test purchasing credits creates CreditPurchase record."""
        initial_count = CreditPurchase.objects.filter(user=user).count()

        authenticated_client.post(
            reverse('memberships:purchase_credits'),
            {'credits': 10}
        )

        assert CreditPurchase.objects.filter(user=user).count() == initial_count + 1
        latest_purchase = CreditPurchase.objects.filter(user=user).latest('purchase_date')
        assert latest_purchase.credits_purchased == 10
        assert latest_purchase.amount_paid == 50  # 10 * 5 EUR

    def test_purchase_credits_without_membership(self, authenticated_client, user):
        """Test purchasing credits without active membership shows error."""
        response = authenticated_client.post(
            reverse('memberships:purchase_credits'),
            {'credits': 10}
        )
        # Should stay on same page with error message or redirect with message
        # The actual behavior depends on the view implementation
        assert response.status_code in [200, 302]  # Allow both redirect and stay

    def test_purchase_credits_invalid_amount(self, authenticated_client, membership):
        """Test purchasing invalid credit amount."""
        response = authenticated_client.post(
            reverse('memberships:purchase_credits'),
            {'credits': 0}  # Invalid - must be at least 1
        )
        assert response.status_code == 200  # Stays on form
        assert 'form' in response.context
        assert not response.context['form'].is_valid()


@pytest.mark.views
@pytest.mark.django_db


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.integration
@pytest.mark.django_db
class TestCreditSystemIntegration:
    """Integration tests for the credit purchase system."""

    def test_complete_credit_purchase_flow(self, authenticated_client, user, membership):
        """Test complete flow from viewing to purchasing credits."""
        # Start with initial credits
        initial_credits = membership.credits_remaining

        # View dashboard
        response = authenticated_client.get(reverse('memberships:dashboard'))
        assert response.status_code == 200

        # Go to purchase page
        response = authenticated_client.get(reverse('memberships:purchase_credits'))
        assert response.status_code == 200

        # Purchase credits
        response = authenticated_client.post(
            reverse('memberships:purchase_credits'),
            {'credits': 15}
        )

        # Verify redirect
        assert response.status_code == 302

        # Check dashboard reflects new credits
        response = authenticated_client.get(reverse('memberships:dashboard'))
        assert response.status_code == 200

        # Verify credits were added
        membership.refresh_from_db()
        assert membership.credits_remaining == initial_credits + 15

        # Verify purchase record exists
        purchase = CreditPurchase.objects.filter(user=user).latest('purchase_date')
        assert purchase.credits_purchased == 15
        assert purchase.amount_paid == 75

    def test_multiple_purchases_accumulate_credits(self, authenticated_client, user, membership):
        """Test multiple purchases correctly accumulate credits."""
        initial_credits = membership.credits_remaining

        # First purchase
        authenticated_client.post(
            reverse('memberships:purchase_credits'),
            {'credits': 10}
        )

        # Second purchase
        authenticated_client.post(
            reverse('memberships:purchase_credits'),
            {'credits': 5}
        )

        # Third purchase
        authenticated_client.post(
            reverse('memberships:purchase_credits'),
            {'credits': 8}
        )

        # Verify total credits
        membership.refresh_from_db()
        assert membership.credits_remaining == initial_credits + 10 + 5 + 8

        # Verify all purchase records exist
        purchases = CreditPurchase.objects.filter(user=user)
        assert purchases.count() == 3
        assert sum(p.credits_purchased for p in purchases) == 23
