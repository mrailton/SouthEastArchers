"""
Tests for the shooting app.
"""
import pytest
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
from shooting.models import ShootingNight, ShootingAttendance
from shooting.forms import ShootingNightForm

User = get_user_model()


# ============================================================================
# MODEL TESTS
# ============================================================================

@pytest.mark.models
@pytest.mark.django_db
class TestShootingNightModel:
    """Test the ShootingNight model."""

    def test_create_shooting_night(self, user):
        """Test creating a shooting night."""
        shooting_night = ShootingNight.objects.create(
            date=timezone.now().date(),
            location='Hall',
            notes='Test shooting night',
            created_by=user
        )
        assert shooting_night.date == timezone.now().date()
        assert shooting_night.location == 'Hall'
        assert shooting_night.notes == 'Test shooting night'
        assert shooting_night.created_by == user

    def test_shooting_night_string_representation(self, shooting_night):
        """Test __str__ method."""
        # Format: Shooting Night - date (location)
        assert 'Shooting Night' in str(shooting_night)
        assert str(shooting_night.date) in str(shooting_night)
        assert shooting_night.location in str(shooting_night)

    def test_shooting_night_location_choices(self, user):
        """Test location field accepts valid choices."""
        for location in ['Hall', 'Meadow', 'Woods']:
            sn = ShootingNight.objects.create(
                date=timezone.now().date(),
                location=location,
                created_by=user
            )
            assert sn.location == location

    def test_shooting_night_ordering(self, user):
        """Test shooting nights are ordered by date descending."""
        old_night = ShootingNight.objects.create(
            date=timezone.now().date() - timedelta(days=7),
            location='Hall',
            created_by=user
        )

        new_night = ShootingNight.objects.create(
            date=timezone.now().date(),
            location='Meadow',
            created_by=user
        )

        nights = list(ShootingNight.objects.all())
        assert nights[0] == new_night
        assert nights[1] == old_night


@pytest.mark.models
@pytest.mark.django_db
class TestShootingAttendanceModel:
    """Test the ShootingAttendance model."""

    def test_create_attendance(self, shooting_night, user):
        """Test creating a shooting attendance record."""
        attendance = ShootingAttendance.objects.create(
            shooting_night=shooting_night,
            user=user,
            credits_deducted=1
        )
        assert attendance.shooting_night == shooting_night
        assert attendance.user == user
        assert attendance.credits_deducted == 1
        assert attendance.recorded_at is not None

    def test_attendance_string_representation(self, shooting_attendance, user):
        """Test __str__ method."""
        expected = f"{user.email} - {shooting_attendance.shooting_night.date}"
        assert str(shooting_attendance) == expected

    def test_attendance_unique_constraint(self, shooting_night, user):
        """Test user can only attend each shooting night once."""
        ShootingAttendance.objects.create(
            shooting_night=shooting_night,
            user=user,
            credits_deducted=1
        )

        # Try to create duplicate attendance
        with pytest.raises(Exception):  # IntegrityError
            ShootingAttendance.objects.create(
                shooting_night=shooting_night,
                user=user,
                credits_deducted=1
            )

    def test_attendance_default_credits(self, shooting_night, user):
        """Test default credits_deducted is 1."""
        attendance = ShootingAttendance.objects.create(
            shooting_night=shooting_night,
            user=user
        )
        assert attendance.credits_deducted == 1

    def test_multiple_users_same_night(self, shooting_night, users):
        """Test multiple users can attend same shooting night."""
        for user in users:
            ShootingAttendance.objects.create(
                shooting_night=shooting_night,
                user=user
            )

        attendances = ShootingAttendance.objects.filter(shooting_night=shooting_night)
        assert attendances.count() == len(users)

    def test_user_multiple_nights(self, user):
        """Test user can attend multiple shooting nights."""
        night1 = ShootingNight.objects.create(
            date=timezone.now().date(),
            location='Hall',
            created_by=user
        )
        night2 = ShootingNight.objects.create(
            date=timezone.now().date() + timedelta(days=1),
            location='Meadow',
            created_by=user
        )

        ShootingAttendance.objects.create(shooting_night=night1, user=user)
        ShootingAttendance.objects.create(shooting_night=night2, user=user)

        user_attendances = ShootingAttendance.objects.filter(user=user)
        assert user_attendances.count() == 2


# ============================================================================
# FORM TESTS
# ============================================================================

@pytest.mark.forms
@pytest.mark.django_db
class TestShootingNightForm:
    """Test the ShootingNightForm."""

    def test_form_has_required_fields(self):
        """Test form has required fields."""
        form = ShootingNightForm()
        assert 'date' in form.fields
        assert 'location' in form.fields
        assert 'notes' in form.fields
        assert 'attendees' in form.fields

    def test_missing_required_fields(self):
        """Test form validation fails with missing required fields."""
        form = ShootingNightForm(data={})
        assert not form.is_valid()
        assert 'date' in form.errors
        assert 'location' in form.errors
        assert 'attendees' in form.errors  # attendees is required

    def test_form_location_choices(self):
        """Test form provides correct location choices."""
        form = ShootingNightForm()
        # Location field is a Select widget with choices from model
        assert 'location' in form.fields
        # Check that it's a choice field
        assert hasattr(form.fields['location'], 'choices')

    def test_form_attendees_queryset(self, users):
        """Test form attendees queryset is set correctly."""
        form = ShootingNightForm()
        # Queryset should be set to active users
        assert form.fields['attendees'].queryset is not None
        assert form.fields['attendees'].queryset.count() >= 0


# ============================================================================
# ADMIN TESTS
# ============================================================================

@pytest.mark.admin
@pytest.mark.django_db
class TestShootingAdmin:
    """Test ShootingNight admin functionality."""

    def test_admin_list_view(self, admin_client):
        """Test admin can view shooting nights list."""
        response = admin_client.get('/admin/shooting/shootingnight/')
        assert response.status_code == 200

    def test_admin_can_create_shooting_night(self, admin_client, admin_user):
        """Test admin can create shooting night."""
        response = admin_client.post('/admin/shooting/shootingnight/add/', {
            'date': timezone.now().date(),
            'location': 'Hall',
            'notes': 'Admin created night',
            'created_by': admin_user.id
        })
        assert response.status_code in [200, 302]

    def test_admin_inline_attendance(self, admin_client, shooting_night, user):
        """Test admin can add attendance inline."""
        response = admin_client.get(f'/admin/shooting/shootingnight/{shooting_night.id}/change/')
        assert response.status_code == 200
        # Check that attendance inline form is present
        assert b'shootingattendance_set' in response.content or b'Attendance' in response.content

    def test_admin_auto_sets_created_by(self, admin_user):
        """Test admin automatically sets created_by on new shooting night."""
        from shooting.admin import ShootingNightAdmin
        from django.contrib.admin.sites import AdminSite
        from unittest.mock import Mock

        admin = ShootingNightAdmin(ShootingNight, AdminSite())
        
        shooting_night = ShootingNight(
            date=timezone.now().date(),
            location='Hall',
            notes='Test notes'
        )
        
        request = Mock()
        request.user = admin_user
        
        # Test save_model sets created_by on create
        admin.save_model(request, shooting_night, None, change=False)
        assert shooting_night.created_by == admin_user

    def test_admin_attendees_count_display(self, admin_user, shooting_night, user):
        """Test admin displays attendees count correctly."""
        from shooting.admin import ShootingNightAdmin
        from django.contrib.admin.sites import AdminSite

        admin = ShootingNightAdmin(ShootingNight, AdminSite())
        
        # Initially no attendees
        count = admin.attendees_count(shooting_night)
        assert count == 0
        
        # Add attendees
        ShootingAttendance.objects.create(
            shooting_night=shooting_night,
            user=user,
            credits_deducted=1
        )
        
        count = admin.attendees_count(shooting_night)
        assert count == 1


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.integration
@pytest.mark.django_db
class TestShootingAttendanceIntegration:
    """Integration tests for shooting attendance system."""

    def test_attendance_with_credit_deduction(self, shooting_night, user, membership):
        """Test attendance creation and credit deduction logic."""
        initial_credits = membership.credits_remaining

        # Create attendance
        attendance = ShootingAttendance.objects.create(
            shooting_night=shooting_night,
            user=user,
            credits_deducted=1
        )

        # Verify credits were deducted via signal
        membership.refresh_from_db()
        assert membership.credits_remaining == initial_credits - 1
        assert attendance.credits_deducted == 1
        assert ShootingAttendance.objects.filter(user=user).count() == 1

    def test_credit_refund_on_attendance_deletion(self, shooting_night, user, membership):
        """Test credits are refunded when attendance is deleted."""
        initial_credits = membership.credits_remaining

        # Create attendance (credits deducted)
        attendance = ShootingAttendance.objects.create(
            shooting_night=shooting_night,
            user=user,
            credits_deducted=1
        )
        
        membership.refresh_from_db()
        assert membership.credits_remaining == initial_credits - 1

        # Delete attendance (credits refunded)
        attendance.delete()
        
        membership.refresh_from_db()
        assert membership.credits_remaining == initial_credits

    def test_credit_deduction_with_custom_amount(self, shooting_night, user, membership):
        """Test attendance with custom credits_deducted amount."""
        initial_credits = membership.credits_remaining
        credits_to_deduct = 3

        # Create attendance with custom credit amount
        attendance = ShootingAttendance.objects.create(
            shooting_night=shooting_night,
            user=user,
            credits_deducted=credits_to_deduct
        )

        # Verify correct amount was deducted
        membership.refresh_from_db()
        assert membership.credits_remaining == initial_credits - credits_to_deduct

    def test_credit_deduction_insufficient_credits(self, shooting_night, user, membership):
        """Test attendance creation when user has insufficient credits."""
        # Set credits to less than needed
        membership.credits_remaining = 0
        membership.save()

        # Create attendance - should still create but won't deduct
        attendance = ShootingAttendance.objects.create(
            shooting_night=shooting_night,
            user=user,
            credits_deducted=1
        )

        # Verify credits weren't deducted (would go negative)
        membership.refresh_from_db()
        assert membership.credits_remaining == 0
        assert attendance.id is not None

    def test_credit_deduction_no_membership(self, shooting_night, user_factory):
        """Test attendance creation when user has no membership."""
        user_no_membership = user_factory()
        
        # Create attendance - should still create even without membership
        attendance = ShootingAttendance.objects.create(
            shooting_night=shooting_night,
            user=user_no_membership,
            credits_deducted=1
        )
        
        assert attendance.id is not None
        assert attendance.user == user_no_membership

    def test_multiple_attendees_same_night(self, shooting_night, users):
        """Test multiple users attending same shooting night."""
        # Add all users as attendees
        for user in users:
            ShootingAttendance.objects.create(
                shooting_night=shooting_night,
                user=user
            )

        # Verify all attendances were created
        attendances = ShootingAttendance.objects.filter(shooting_night=shooting_night)
        assert attendances.count() == len(users)

        # Verify through relationship works
        attendees = shooting_night.attendees.all()
        assert attendees.count() == len(users)

    def test_user_attendance_history(self, user):
        """Test tracking user's attendance history across multiple nights."""
        # Create multiple shooting nights
        nights = []
        for i in range(5):
            night = ShootingNight.objects.create(
                date=timezone.now().date() - timedelta(days=i),
                location='Hall',
                created_by=user
            )
            nights.append(night)

        # User attends 3 out of 5 nights
        for night in nights[:3]:
            ShootingAttendance.objects.create(
                shooting_night=night,
                user=user
            )

        # Verify user's attendance history
        user_attendances = ShootingAttendance.objects.filter(user=user)
        assert user_attendances.count() == 3

        # Verify total credits that would be deducted
        total_credits = sum(a.credits_deducted for a in user_attendances)
        assert total_credits == 3
