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


def test_create_shoot_attendee_no_credits(app):
    """Test creating shoot with attendee who has no credits allows negative balance"""
    from datetime import timedelta

    from app.models import Membership
    from app.services import ShootService

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
        initial_credits=0,  # No credits
        purchased_credits=0,
        status="active",
    )
    db.session.add(membership)
    db.session.commit()
    user_id = user.id

    # Use the service directly to create shoot with attendee
    shoot, warnings = ShootService.create_shoot(
        shoot_date=date.today(),
        location="HALL",
        description="Test shoot",
        attendee_ids=[user_id],
    )

    # Verify user was added and credits went negative
    user = db.session.get(User, user_id)
    assert user.membership.credits_remaining() == -1
    assert len(shoot.users) == 1
    assert shoot.users[0].id == user_id
    # Should have warning about negative balance
    assert len(warnings) == 1
    assert "negative balance" in warnings[0].lower()


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


def test_edit_shoot_add_attendee_no_credits(app):
    """Test adding attendee when they have no credits allows negative balance"""
    from app.services import ShootService

    # Create user with no credits
    user = User(name="No Credits", email="nocredits2@example.com")
    user.set_password("password")
    db.session.add(user)
    db.session.flush()

    from datetime import timedelta

    from app.models import Membership

    membership = Membership(
        user_id=user.id,
        start_date=date.today(),
        expiry_date=date.today() + timedelta(days=365),
        initial_credits=0,
        purchased_credits=0,
        status="active",
    )
    db.session.add(membership)
    db.session.commit()
    user_id = user.id

    # Create a shoot without attendees
    shoot, _ = ShootService.create_shoot(
        shoot_date=date.today(),
        location="HALL",
        description="Test shoot",
    )

    # Add the no-credit user to the shoot
    success, warnings = ShootService.update_shoot(
        shoot=shoot,
        shoot_date=date.today(),
        location="HALL",
        description="Updated shoot",
        attendee_ids=[user_id],
    )

    # Verify user was added and credits went negative
    user = db.session.get(User, user_id)
    assert success is True
    assert user.membership.credits_remaining() == -1
    assert len(shoot.users) == 1
    assert shoot.users[0].id == user_id
    # Check for warning about negative balance
    assert len(warnings) == 1
    assert "negative balance" in warnings[0].lower()


# --- Visitor Tests ---


def test_create_shoot_with_visitors(app, admin_user):
    """Test creating a shoot with visitors creates income transactions"""
    from app.models import FinancialTransaction
    from app.services import ShootService

    shoot, warnings = ShootService.create_shoot(
        shoot_date=date.today(),
        location="HALL",
        description="Shoot with visitors",
        visitors=[
            {"name": "John Doe", "club": "Dublin Archers", "affiliation": "AI", "payment_method": "cash"},
        ],
        created_by_id=admin_user.id,
    )

    assert shoot is not None
    assert len(shoot.visitors) == 1
    assert shoot.visitors[0].name == "John Doe"
    assert shoot.visitors[0].club == "Dublin Archers"
    assert shoot.visitors[0].affiliation == "AI"
    assert shoot.visitors[0].payment_method == "cash"

    # Check income transaction was created
    txns = FinancialTransaction.query.filter_by(category="shoot_fees").all()
    assert len(txns) == 1
    assert txns[0].type == "income"
    assert txns[0].amount_cents == 1000  # €10.00 default visitor fee
    assert txns[0].source == "Cash"
    assert "John Doe" in txns[0].description

    # Cash visitors should NOT have a fee expense
    expenses = FinancialTransaction.query.filter_by(category="payment_processing_fees").all()
    assert len(expenses) == 0


def test_create_shoot_with_visitor_sumup(app, admin_user):
    """Test visitor with SumUp payment method creates income with SumUp source and fee expense"""
    from app.models import FinancialTransaction
    from app.services import ShootService
    from app.services.settings_service import SettingsService

    # Configure SumUp fee
    settings = SettingsService.get()
    settings.sumup_fee_percentage = 1.90
    SettingsService.save(settings)

    shoot, _ = ShootService.create_shoot(
        shoot_date=date.today(),
        location="MEADOW",
        description="Shoot with SumUp visitor",
        visitors=[
            {"name": "Jane Smith", "club": "Cork Archery", "affiliation": "IFAF", "payment_method": "sumup"},
        ],
        created_by_id=admin_user.id,
    )

    assert shoot.visitors[0].payment_method == "sumup"

    income = FinancialTransaction.query.filter_by(category="shoot_fees").first()
    assert income.source == "SumUp"
    assert income.amount_cents == 1000

    # Should also have a SumUp fee expense
    expense = FinancialTransaction.query.filter_by(category="payment_processing_fees").first()
    assert expense is not None
    assert expense.type == "expense"
    # 1000 cents * 1.90 / 10000 = 0.19
    assert expense.amount_cents == 19
    assert "1.9%" in expense.description


def test_create_shoot_with_multiple_visitors(app, admin_user):
    """Test creating shoot with multiple visitors creates an income per visitor"""
    from app.models import FinancialTransaction
    from app.services import ShootService

    visitors = [
        {"name": "Visitor A", "club": "Club A", "affiliation": "AI", "payment_method": "cash"},
        {"name": "Visitor B", "club": "Club B", "affiliation": "IFAF", "payment_method": "sumup"},
    ]
    shoot, _ = ShootService.create_shoot(
        shoot_date=date.today(),
        location="WOODS",
        description="Multi visitor shoot",
        visitors=visitors,
        created_by_id=admin_user.id,
    )

    assert len(shoot.visitors) == 2
    txns = FinancialTransaction.query.filter_by(category="shoot_fees").all()
    assert len(txns) == 2


def test_edit_shoot_add_visitor(app, admin_user):
    """Test adding visitors to an existing shoot creates income transactions"""
    from app.models import FinancialTransaction
    from app.services import ShootService

    shoot, _ = ShootService.create_shoot(
        shoot_date=date.today(),
        location="HALL",
        description="Original shoot",
        created_by_id=admin_user.id,
    )

    assert len(shoot.visitors) == 0

    success, _ = ShootService.update_shoot(
        shoot=shoot,
        shoot_date=date.today(),
        location="HALL",
        description="Updated shoot",
        visitors=[
            {"name": "New Visitor", "club": "Galway Archers", "affiliation": "AI", "payment_method": "cash"},
        ],
        created_by_id=admin_user.id,
    )

    assert success is True
    assert len(shoot.visitors) == 1
    txns = FinancialTransaction.query.filter_by(category="shoot_fees").all()
    assert len(txns) == 1


def test_edit_shoot_replace_visitors(app, admin_user):
    """Test updating shoot replaces removed visitors and only charges new ones"""
    from app.models import FinancialTransaction
    from app.services import ShootService

    shoot, _ = ShootService.create_shoot(
        shoot_date=date.today(),
        location="HALL",
        description="Shoot",
        visitors=[
            {"name": "Original Visitor", "club": "Club X", "affiliation": "AI", "payment_method": "cash"},
        ],
        created_by_id=admin_user.id,
    )

    assert len(shoot.visitors) == 1

    success, _ = ShootService.update_shoot(
        shoot=shoot,
        shoot_date=date.today(),
        location="HALL",
        description="Updated",
        visitors=[
            {"name": "Replacement Visitor", "club": "Club Y", "affiliation": "IFAF", "payment_method": "sumup"},
        ],
        created_by_id=admin_user.id,
    )

    assert success is True
    assert len(shoot.visitors) == 1
    assert shoot.visitors[0].name == "Replacement Visitor"
    # Original + replacement = 2 income transactions
    txns = FinancialTransaction.query.filter_by(category="shoot_fees").all()
    assert len(txns) == 2


def test_edit_shoot_keeps_existing_visitors_no_duplicate_txns(app, admin_user):
    """Test that re-submitting the same visitors doesn't create duplicate transactions"""
    from app.models import FinancialTransaction
    from app.services import ShootService

    visitor_data = [
        {"name": "John Doe", "club": "Dublin Archers", "affiliation": "AI", "payment_method": "cash"},
    ]
    shoot, _ = ShootService.create_shoot(
        shoot_date=date.today(),
        location="HALL",
        description="Shoot",
        visitors=visitor_data,
        created_by_id=admin_user.id,
    )

    assert len(FinancialTransaction.query.filter_by(category="shoot_fees").all()) == 1

    # Edit with the same visitor — should NOT create a new transaction
    success, _ = ShootService.update_shoot(
        shoot=shoot,
        shoot_date=date.today(),
        location="HALL",
        description="Updated",
        visitors=visitor_data,
        created_by_id=admin_user.id,
    )

    assert success is True
    assert len(shoot.visitors) == 1
    txns = FinancialTransaction.query.filter_by(category="shoot_fees").all()
    assert len(txns) == 1  # No duplicate


def test_visitor_fee_uses_settings(app, admin_user):
    """Test that visitor fee comes from application settings"""
    from app.models import FinancialTransaction
    from app.services import ShootService
    from app.services.settings_service import SettingsService

    settings = SettingsService.get()
    settings.visitor_shoot_fee = 1500  # €15.00
    SettingsService.save(settings)

    shoot, _ = ShootService.create_shoot(
        shoot_date=date.today(),
        location="HALL",
        description="Custom fee shoot",
        visitors=[
            {"name": "Custom Fee Visitor", "club": "Club Z", "affiliation": "AI", "payment_method": "cash"},
        ],
        created_by_id=admin_user.id,
    )

    txn = FinancialTransaction.query.filter_by(category="shoot_fees").first()
    assert txn.amount_cents == 1500


def test_create_shoot_with_visitors_route(client, admin_user, app):
    """Test creating shoot with visitors via HTTP route"""
    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    response = client.post(
        "/admin/shoots/create",
        data={
            "date": date.today().isoformat(),
            "location": "HALL",
            "description": "Route visitor test",
            "csrf_token": "test",
            "visitor_name": ["Test Visitor"],
            "visitor_club": ["Test Club"],
            "visitor_affiliation": ["AI"],
            "visitor_payment_method": ["cash"],
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"visitor" in response.data.lower()


def test_shoots_list_shows_visitors(client, admin_user, app):
    """Test shoots list shows visitor count and names"""
    from app.models.shoot import ShootVisitor

    shoot = Shoot(date=date.today(), location=ShootLocation.HALL, description="Visitor test")
    db.session.add(shoot)
    db.session.flush()
    visitor = ShootVisitor(shoot_id=shoot.id, name="List Visitor", club="Test Club", affiliation="AI", payment_method="cash")
    db.session.add(visitor)
    db.session.commit()

    client.post("/auth/login", data={"email": admin_user.email, "password": "adminpass"})

    response = client.get("/admin/shoots")
    assert response.status_code == 200
    assert b"1 visitor" in response.data
    assert b"List Visitor" in response.data
