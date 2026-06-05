"""Admin member route edge cases not covered elsewhere."""

from unittest.mock import patch

from app.services.result import ServiceResult


def test_activate_membership_not_found(admin_client):
    response = admin_client.post("/admin/members/99999/membership/activate")
    assert response.status_code == 404


def test_activate_membership_service_failure_shows_flash(admin_client, test_user):
    with patch(
        "app.routers.admin.members.MembershipService.activate_membership",
        return_value=ServiceResult.fail("Error reason"),
    ):
        response = admin_client.post(
            f"/admin/members/{test_user.id}/membership/activate",
            follow_redirects=True,
        )
    assert b"Error reason" in response.content


def test_edit_member_not_found(admin_client):
    response = admin_client.post("/admin/members/99999/edit")
    assert response.status_code == 404
