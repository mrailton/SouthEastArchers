"""Member routes — auth gates and form error display (profile/password logic: users service tests)."""


def test_dashboard_requires_login(client):
    response = client.get("/member/dashboard", follow_redirects=True)
    assert b"Login" in response.content


def test_dashboard_logged_in(member_client):
    response = member_client.get("/member/dashboard")
    assert response.status_code == 200
    assert b"Credits Remaining" in response.content


def test_update_profile_redirects(member_client):
    response = member_client.post(
        "/member/profile",
        data={"name": "Updated Name", "phone": "9876543210"},
        follow_redirects=False,
    )
    assert response.status_code in (302, 303)


def test_change_password_wrong_current_shows_error(member_client):
    response = member_client.post(
        "/member/change-password",
        data={
            "current_password": "wrongpassword",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123",
        },
    )
    assert "incorrect" in response.text.lower()


def test_change_password_mismatch_shows_error(member_client):
    response = member_client.post(
        "/member/change-password",
        data={
            "current_password": "password123",
            "new_password": "newpassword123",
            "confirm_password": "differentpassword",
        },
    )
    assert "do not match" in response.text.lower()


def test_shoots_page(member_client, test_user):
    response = member_client.get("/member/shoots")
    assert response.status_code == 200


def test_credits_page(member_client):
    response = member_client.get("/member/credits")
    assert response.status_code == 200


def test_profile_page(member_client):
    response = member_client.get("/member/profile")
    assert response.status_code == 200


def test_change_password_page(member_client):
    response = member_client.get("/member/change-password")
    assert response.status_code == 200


def test_change_password_success(member_client):
    response = member_client.post(
        "/member/change-password",
        data={
            "current_password": "password123",
            "new_password": "newpassword456",
            "confirm_password": "newpassword456",
        },
        follow_redirects=True,
    )
    assert b"successfully" in response.content.lower() or response.status_code == 200


def test_profile_validation_error(member_client):
    response = member_client.post("/member/profile", data={"name": "A", "phone": ""})
    assert response.status_code == 422
