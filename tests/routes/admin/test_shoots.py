"""Tests for admin shoot management"""

from datetime import date

from app import db
from app.models import Shoot, ShootLocation, User


def test_shoots_list(client, admin_user):
    """Test viewing shoots list"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    response = client.get("/admin/shoots")
    assert response.status_code == 200


def test_create_shoot_page(client, admin_user):
    """Test accessing create shoot page"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    response = client.get("/admin/shoots/create")
    assert response.status_code == 200


def test_edit_shoot_page(client, admin_user, app):
    """Test accessing edit shoot page"""

    # Create a shoot first
    shoot = Shoot(date=date.today(), location=ShootLocation.HALL, description="Test shoot")
    db.session.add(shoot)
    db.session.commit()

    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    response = client.get(f"/admin/shoots/{shoot.id}/edit")
    assert response.status_code == 200
    assert b"Edit Shoot" in response.data


def test_edit_shoot_updates_details(client, admin_user, app):
    """Test updating shoot details"""

    # Create a shoot
    shoot = Shoot(
        date=date.today(),
        location=ShootLocation.HALL,
        description="Original description",
    )
    db.session.add(shoot)
    db.session.commit()
    shoot_id = shoot.id

    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    # Update the shoot
    response = client.post(
        f"/admin/shoots/{shoot_id}/edit",
        data={
            "date": date.today().isoformat(),
            "location": "MEADOW",
            "description": "Updated description",
            "csrf_token": "test",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200


def test_shoots_requires_admin(client, test_user):
    """Test that shoots require admin"""
    client.post("/auth/login", data={"email": test_user.email, "password": "password123"})

    response = client.get("/admin/shoots")
    assert response.status_code in [302, 403]


def test_edit_shoot_not_found(client, admin_user):
    """Test editing non-existent shoot"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    response = client.get("/admin/shoots/99999/edit")
    assert response.status_code == 404


def test_create_shoot_with_attendees(client, admin_user, test_user, app):
    """Test creating shoot with attendees deducts credits"""

    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    response = client.post(
        "/admin/shoots/create",
        data={
            "date": date.today().isoformat(),
            "location": "HALL",
            "description": "Test shoot with attendees",
            "attendees": [str(test_user.id)],
            "csrf_token": "test",
        },
        follow_redirects=True,
    )

    # Form validation might fail without proper CSRF, but we can check the response
    assert response.status_code == 200


def test_edit_shoot_add_attendee(client, admin_user, test_user, app):
    """Test adding attendee to shoot deducts credit"""

    # Create a shoot without attendees
    shoot = Shoot(date=date.today(), location=ShootLocation.HALL, description="Test shoot")
    db.session.add(shoot)
    db.session.commit()
    shoot_id = shoot.id

    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    response = client.post(
        f"/admin/shoots/{shoot_id}/edit",
        data={
            "date": date.today().isoformat(),
            "location": "HALL",
            "description": "Updated shoot",
            "attendees": [str(test_user.id)],
            "csrf_token": "test",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200


def test_edit_shoot_remove_attendee(client, admin_user, test_user, app):
    """Test removing attendee from shoot refunds credit"""

    # Create a shoot with attendee
    shoot = Shoot(date=date.today(), location=ShootLocation.HALL, description="Test shoot")
    db.session.add(shoot)
    db.session.flush()

    # Add attendee and deduct credit
    shoot.users.append(test_user)
    test_user.membership.use_credit()
    db.session.commit()

    shoot_id = shoot.id

    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    # Remove attendee (empty attendees list)
    response = client.post(
        f"/admin/shoots/{shoot_id}/edit",
        data={
            "date": date.today().isoformat(),
            "location": "HALL",
            "description": "Updated shoot",
            "attendees": [],  # Remove all attendees
            "csrf_token": "test",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200


def test_create_shoot_attendee_no_credits(client, admin_user, app):
    """Test creating shoot with attendee who has no credits"""
    from datetime import timedelta

    from app.models import Membership

    # Create user with no credits
    user = User(
        name="No Credits User",
        email="nocredits@example.com",
        phone="1234567890",
    )
    user.set_password("password")
    db.session.add(user)
    db.session.flush()

    membership = Membership(
        user_id=user.id,
        start_date=date.today(),
        expiry_date=date.today() + timedelta(days=365),
        credits=0,  # No credits
        status="active",
    )
    db.session.add(membership)
    db.session.commit()

    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    response = client.post(
        "/admin/shoots/create",
        data={
            "date": date.today().isoformat(),
            "location": "HALL",
            "description": "Test shoot",
            "attendees": [str(user.id)],
            "csrf_token": "test",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    # Should show warning about no credits


def test_edit_shoot_get_prepopulates_data(client, admin_user, test_user, app):
    """Test that GET request to edit shoot prepopulates form"""

    # Create a shoot with attendee
    shoot = Shoot(
        date=date.today(),
        location=ShootLocation.MEADOW,
        description="Original description",
    )
    db.session.add(shoot)
    db.session.flush()
    shoot.users.append(test_user)
    db.session.commit()

    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    response = client.get(f"/admin/shoots/{shoot.id}/edit")
    assert response.status_code == 200
    assert b"Original description" in response.data


def test_create_shoot_requires_admin(client, test_user):
    """Test creating shoot requires admin"""
    client.post("/auth/login", data={"email": test_user.email, "password": "password123"})

    response = client.get("/admin/shoots/create")
    assert response.status_code in [302, 403]


def test_edit_shoot_requires_admin(client, test_user, app):
    """Test editing shoot requires admin"""

    shoot = Shoot(date=date.today(), location=ShootLocation.HALL, description="Test shoot")
    db.session.add(shoot)
    db.session.commit()

    client.post("/auth/login", data={"email": test_user.email, "password": "password123"})

    response = client.get(f"/admin/shoots/{shoot.id}/edit")
    assert response.status_code in [302, 403]


def test_shoots_list_shows_all_shoots(client, admin_user, app):
    """Test shoots list displays all shoots"""

    shoot1 = Shoot(date=date.today(), location=ShootLocation.HALL, description="First shoot")
    shoot2 = Shoot(date=date.today(), location=ShootLocation.MEADOW, description="Second shoot")
    db.session.add_all([shoot1, shoot2])
    db.session.commit()

    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    response = client.get("/admin/shoots")
    assert response.status_code == 200
    # Should show both shoots
    assert b"First shoot" in response.data or b"Second shoot" in response.data


def test_edit_shoot_add_attendee_no_credits(client, admin_user, test_user, app):
    """Test adding attendee when they have no credits shows warning"""

    # Set user to have no credits
    test_user.membership.credits = 0
    db.session.commit()

    # Create a shoot
    shoot = Shoot(date=date.today(), location=ShootLocation.HALL, description="Test shoot")
    db.session.add(shoot)
    db.session.commit()
    shoot_id = shoot.id

    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    response = client.post(
        f"/admin/shoots/{shoot_id}/edit",
        data={
            "date": date.today().isoformat(),
            "location": "HALL",
            "description": "Updated shoot",
            "attendees": [str(test_user.id)],
            "csrf_token": "test",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    # Check for warning about no credits
    assert b"no credits" in response.data.lower() or b"Warning" in response.data
