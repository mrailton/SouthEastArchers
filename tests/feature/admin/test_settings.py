"""Admin settings routes — access control and update flash."""


def test_settings_page_loads(admin_client):
    response = admin_client.get("/admin/settings")
    assert response.status_code == 200
    assert b"Application Settings" in response.content


def test_settings_requires_admin(member_client):
    response = member_client.get("/admin/settings")
    assert response.status_code in (302, 403)


def test_update_settings_success_flash(admin_client):
    response = admin_client.post(
        "/admin/settings",
        data={
            "membership_year_start_month": "4",
            "membership_year_start_day": "15",
            "annual_membership_cost": "120",
            "membership_shoots_included": "25",
            "additional_shoot_cost": "6",
            "visitor_shoot_fee": "10",
            "cash_payment_instructions": "Please pay at the next shoot night.",
        },
        follow_redirects=True,
    )
    assert b"Settings updated successfully" in response.content
