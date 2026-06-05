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
