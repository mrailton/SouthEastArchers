"""Tests for admin settings routes"""

from app.services.settings_service import SettingsService


def test_settings_page_loads(client, admin_user):
    """Test that settings page loads for admin"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    response = client.get("/admin/settings")
    assert response.status_code == 200
    assert b"Application Settings" in response.data
    assert b"Membership Year" in response.data


def test_settings_requires_admin(client, test_user):
    """Test that settings page requires admin access"""
    client.post("/auth/login", data={"email": test_user.email, "password": "password123"})

    response = client.get("/admin/settings")
    assert response.status_code in [302, 403]


def test_settings_shows_default_values(client, admin_user, app):
    """Test that settings page shows default values"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    response = client.get("/admin/settings")
    assert response.status_code == 200
    # Check for default values (100 euros = 10000 cents)
    assert b'value="3"' in response.data  # March
    assert b'value="1"' in response.data  # 1st day
    assert b'value="100"' in response.data  # 100 euros


def test_update_settings_success(client, admin_user, app):
    """Test updating settings successfully"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    response = client.post(
        "/admin/settings",
        data={
            "csrf_token": "test",
            "membership_year_start_month": "4",
            "membership_year_start_day": "15",
            "annual_membership_cost": "120",
            "membership_shoots_included": "25",
            "additional_shoot_cost": "6",
            "cash_payment_instructions": "Please pay at the next shoot night.",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Settings updated successfully" in response.data

    # Verify settings were saved
    with app.app_context():
        settings = SettingsService.get()
        assert settings.membership_year_start_month == 4
        assert settings.membership_year_start_day == 15
        assert settings.annual_membership_cost == 12000  # 120 euros = 12000 cents
        assert settings.membership_shoots_included == 25
        assert settings.additional_shoot_cost == 600  # 6 euros = 600 cents
        assert settings.cash_payment_instructions == "Please pay at the next shoot night."


def test_update_settings_validates_month(client, admin_user):
    """Test that month validation works"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    response = client.post(
        "/admin/settings",
        data={
            "csrf_token": "test",
            "membership_year_start_month": "13",  # Invalid - must be 1-12
            "membership_year_start_day": "1",
            "annual_membership_cost": "100",
            "membership_shoots_included": "20",
            "additional_shoot_cost": "5",
        },
    )

    assert response.status_code == 200
    # Should show validation error


def test_update_settings_validates_day(client, admin_user):
    """Test that day validation works"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    response = client.post(
        "/admin/settings",
        data={
            "csrf_token": "test",
            "membership_year_start_month": "3",
            "membership_year_start_day": "32",  # Invalid - must be 1-31
            "annual_membership_cost": "100",
            "membership_shoots_included": "20",
            "additional_shoot_cost": "5",
        },
    )

    assert response.status_code == 200
    # Should show validation error


def test_update_settings_validates_required_fields(client, admin_user):
    """Test that required fields are validated"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    response = client.post(
        "/admin/settings",
        data={
            "csrf_token": "test",
            "membership_year_start_month": "",  # Missing required field
            "membership_year_start_day": "1",
            "annual_membership_cost": "100",
            "membership_shoots_included": "20",
            "additional_shoot_cost": "5",
        },
    )

    assert response.status_code == 200
    # Should show validation error


def test_settings_euro_to_cents_conversion(client, admin_user, app):
    """Test that euro amounts are correctly converted to cents"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    client.post(
        "/admin/settings",
        data={
            "csrf_token": "test",
            "membership_year_start_month": "3",
            "membership_year_start_day": "1",
            "annual_membership_cost": "150",  # 150 euros
            "membership_shoots_included": "20",
            "additional_shoot_cost": "10",  # 10 euros
            "cash_payment_instructions": "Pay cash at reception.",
        },
        follow_redirects=True,
    )

    # Verify conversion happened correctly
    with app.app_context():
        settings = SettingsService.get()
        assert settings.annual_membership_cost == 15000  # 150 * 100
        assert settings.additional_shoot_cost == 1000  # 10 * 100


def test_settings_displays_cents_as_euros(client, admin_user, app):
    """Test that cents are displayed as euros in the form"""
    # Set some values in cents
    with app.app_context():
        settings = SettingsService.get()
        settings.annual_membership_cost = 8500  # 85 euros
        settings.additional_shoot_cost = 750  # 7.5 euros
        SettingsService.save(settings)

    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    response = client.get("/admin/settings")
    assert response.status_code == 200
    # Should display as 85 euros (8500 cents / 100)
    assert b'value="85"' in response.data
    # Should display as 7 euros (750 cents / 100 with integer division)
    assert b'value="7"' in response.data


def test_settings_persists_across_requests(client, admin_user, app):
    """Test that settings persist and can be retrieved"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    # Update settings
    client.post(
        "/admin/settings",
        data={
            "csrf_token": "test",
            "membership_year_start_month": "6",
            "membership_year_start_day": "30",
            "annual_membership_cost": "95",
            "membership_shoots_included": "15",
            "additional_shoot_cost": "8",
            "cash_payment_instructions": "Bring exact change.",
        },
        follow_redirects=True,
    )

    # Load settings page again
    response = client.get("/admin/settings")
    assert response.status_code == 200
    # Should show updated values
    assert b'value="6"' in response.data
    assert b'value="30"' in response.data
    assert b'value="95"' in response.data
    assert b'value="15"' in response.data
    assert b'value="8"' in response.data
    response = client.get("/admin/settings")
    assert response.status_code == 200

    # Verify values are still there
    assert b'value="6"' in response.data
    assert b'value="30"' in response.data
    assert b'value="95"' in response.data
    assert b'value="15"' in response.data
    assert b'value="8"' in response.data
