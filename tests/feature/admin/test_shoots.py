"""Admin shoot routes — permissions and basic create/edit wiring."""


def test_shoots_list(admin_client):
    response = admin_client.get("/admin/shoots")
    assert response.status_code == 200


def test_create_shoot_page(admin_client):
    response = admin_client.get("/admin/shoots/create")
    assert response.status_code == 200


def test_edit_shoot_not_found(admin_client):
    response = admin_client.get("/admin/shoots/99999/edit")
    assert response.status_code == 404


def test_shoots_requires_admin(member_client):
    response = member_client.get("/admin/shoots")
    assert response.status_code in (302, 403)


def test_create_shoot_with_attendee(admin_client, test_user):
    response = admin_client.post(
        "/admin/shoots/create",
        data={
            "date": "2026-04-01",
            "location": "HALL",
            "description": "Practice night",
            "attendees": str(test_user.id),
        },
        follow_redirects=True,
    )
    assert b"Shoot created" in response.content


def test_edit_shoot_success(admin_client, test_user):
    admin_client.post(
        "/admin/shoots/create",
        data={
            "date": "2026-04-02",
            "location": "MEADOW",
            "attendees": str(test_user.id),
        },
        follow_redirects=False,
    )
    from app.models import Shoot

    shoot = Shoot.query.order_by(Shoot.id.desc()).first()
    response = admin_client.get(f"/admin/shoots/{shoot.id}/edit")
    assert response.status_code == 200

    response = admin_client.post(
        f"/admin/shoots/{shoot.id}/edit",
        data={
            "date": "2026-04-03",
            "location": "WOODS",
            "description": "Updated",
            "attendees": str(test_user.id),
        },
        follow_redirects=True,
    )
    assert b"Shoot updated" in response.content


def test_create_shoot_with_visitor(admin_client):
    response = admin_client.post(
        "/admin/shoots/create",
        data={
            "date": "2026-05-01",
            "location": "HALL",
            "visitor_name": "Guest Archer",
            "visitor_club": "Other Club",
            "visitor_affiliation": "AI",
            "visitor_payment_method": "cash",
        },
        follow_redirects=True,
    )
    assert b"Shoot created" in response.content
    assert b"1 visitor" in response.content
